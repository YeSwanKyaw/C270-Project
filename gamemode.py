from flask import Flask, request, jsonify
import itertools
import os
import random
import re
import threading

import requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# --- Config -----------------------------------------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

GRID_SIZE = 5
WIN_LENGTH = 4

GAMES_DB = {}
_id_counter = itertools.count(1)
_db_lock = threading.Lock()


# --- Win detection ------------------------------------------------------
def _winning_lines():
    """Precompute every group of 4 consecutive cell-indices that counts
    as a win: horizontal, vertical, and both diagonals."""
    lines = []
    n = GRID_SIZE

    def idx(r, c):
        return r * n + c

    for r in range(n):
        for c in range(n - WIN_LENGTH + 1):
            lines.append([idx(r, c + k) for k in range(WIN_LENGTH)])

    for c in range(n):
        for r in range(n - WIN_LENGTH + 1):
            lines.append([idx(r + k, c) for k in range(WIN_LENGTH)])

    for r in range(n - WIN_LENGTH + 1):
        for c in range(n - WIN_LENGTH + 1):
            lines.append([idx(r + k, c + k) for k in range(WIN_LENGTH)])

    for r in range(n - WIN_LENGTH + 1):
        for c in range(WIN_LENGTH - 1, n):
            lines.append([idx(r + k, c - k) for k in range(WIN_LENGTH)])

    return lines


WINNING_LINES = _winning_lines()


def check_winner(board_state):
    """Return 'X', 'O', or None."""
    for line in WINNING_LINES:
        values = [board_state[i] for i in line]
        if values[0] != "" and all(v == values[0] for v in values):
            return values[0]
    return None


def empty_cells(board_state):
    return [i for i, cell in enumerate(board_state) if cell == ""]


# --- CPU opponent (rule-based if/else) ----------------------------------
def _line_move(board_state, empty, mark, target_count, open_count=0):
    """Return a winning/blocking cell if `mark` has `target_count` on a line
  with `open_count` empty cells (used for win-now and block-now rules)."""
    for line in WINNING_LINES:
        values = [board_state[i] for i in line]
        if values.count(mark) == target_count and values.count("") == open_count + 1:
            for i in line:
                if board_state[i] == "" and i in empty:
                    return i
    return None


def _best_extension(board_state, empty, mark):
    """Prefer moves that extend the longest existing run of `mark`."""
    opponent = "X" if mark == "O" else "O"
    best_index = None
    best_score = -1

    for cell in empty:
        score = 0
        for line in WINNING_LINES:
            if cell not in line:
                continue
            values = [board_state[i] for i in line]
            if opponent in values:
                continue
            if all(v in (mark, "") for v in values):
                score = max(score, values.count(mark))
        if score > best_score:
            best_score = score
            best_index = cell

    return best_index


def get_cpu_move(board_state):
    """Classic rule-based opponent: explicit if/else priorities, no ML."""
    empty = empty_cells(board_state)
    if not empty:
        return None

    # 1. Win immediately
    move = _line_move(board_state, empty, "O", WIN_LENGTH - 1)
    if move is not None:
        return move

    # 2. Block opponent win
    move = _line_move(board_state, empty, "X", WIN_LENGTH - 1)
    if move is not None:
        return move

    # 3. Build a 3-in-a-row threat
    move = _line_move(board_state, empty, "O", WIN_LENGTH - 2)
    if move is not None:
        return move

    # 4. Block opponent 3-in-a-row
    move = _line_move(board_state, empty, "X", WIN_LENGTH - 2)
    if move is not None:
        return move

    # 5. Extend the strongest existing line
    move = _best_extension(board_state, empty, "O")
    if move is not None:
        return move

    # 6. Take center, then corners, then anything left
    center = (GRID_SIZE * GRID_SIZE) // 2
    if center in empty:
        return center

    corners = [0, GRID_SIZE - 1, GRID_SIZE * (GRID_SIZE - 1), GRID_SIZE * GRID_SIZE - 1]
    for corner in corners:
        if corner in empty:
            return corner

    return random.choice(empty)


# --- AI opponent (trained model via API) --------------------------------
def _gemini_url():
    return (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    )


def _parse_move_index(text, valid_cells):
    """Gemini may add extra words; extract the first valid board index."""
    for match in re.finditer(r"\b(\d+)\b", text):
        index = int(match.group(1))
        if index in valid_cells:
            return index
    return None


def get_ai_move(board_state):
    """Calls a hosted LLM (Gemini). Returns (index, source_label)."""
    valid = empty_cells(board_state)
    if not valid:
        return None, "none"

    if not GEMINI_API_KEY:
        return None, "api_key_missing"

    prompt = (
        "You are playing 5x5 tic-tac-toe where 4 in a row wins.\n"
        "Board is a length-25 list indexed 0-24 (row-major). "
        "X is the human, O is you. Empty cells are \"\".\n"
        f"Board: {board_state}\n"
        f"Legal moves: {valid}\n"
        "Reply with ONE legal index only (0-24). No explanation."
    )

    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    try:
        response = requests.post(
            _gemini_url(),
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=8,
        )
        response.raise_for_status()
        text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
        move = _parse_move_index(text, set(valid))
        if move is None:
            return None, "api_invalid_response"
        return move, "gemini_api"
    except (requests.RequestException, KeyError, IndexError, ValueError) as exc:
        print(f"Gemini API error: {exc}")
        return None, "api_error"


def choose_opponent_move(mode, board_state):
    """Single entry point used by the game loop."""
    if mode == "cpu":
        return get_cpu_move(board_state), "cpu_rules"
    if mode == "ai":
        return get_ai_move(board_state)
    return None, "human"


# --- Routes ---------------------------------------------------------------
@app.route("/api/start_match", methods=["POST"])
def start_match():
    data = request.get_json(silent=True) or {}
    mode = data.get("mode")

    if mode not in ("local", "cpu", "ai"):
        return jsonify({"error": "mode must be 'local', 'cpu', or 'ai'"}), 400

    if mode == "ai" and not GEMINI_API_KEY:
        return jsonify({
            "error": "AI mode requires GEMINI_API_KEY to be set in the environment."
        }), 503

    with _db_lock:
        game_id = next(_id_counter)
        GAMES_DB[game_id] = {
            "game_id": game_id,
            "mode": mode,
            "player_1": "Player 1",
            "player_2": (
                "Gemini_AI" if mode == "ai"
                else "CPU_Bot" if mode == "cpu"
                else "Player 2"
            ),
            "board_state": [""] * (GRID_SIZE * GRID_SIZE),
            "current_turn": "P1",
            "status": "Active",
            "winner": None,
        }

    return jsonify({
        "game_id": game_id,
        "message": f"Started {mode} match successfully!",
        "opponent": GAMES_DB[game_id]["player_2"],
    }), 201


@app.route("/api/submit_move", methods=["POST"])
def submit_move():
    data = request.get_json(silent=True) or {}
    game_id = data.get("game_id")
    player = data.get("player")
    cell_index = data.get("cell_index")

    game = GAMES_DB.get(game_id)
    if not game:
        return jsonify({"error": "Game not found"}), 404
    if game["status"] != "Active":
        return jsonify({"error": "Match not active", "status": game["status"]}), 400

    if player not in ("P1", "P2"):
        return jsonify({"error": "player must be 'P1' or 'P2'"}), 400
    if game["current_turn"] != player:
        return jsonify({"error": "It is not your turn!"}), 403

    if not isinstance(cell_index, int) or not (0 <= cell_index < GRID_SIZE * GRID_SIZE):
        return jsonify({
            "error": f"cell_index must be an integer from 0 to {GRID_SIZE * GRID_SIZE - 1}"
        }), 400

    if game["board_state"][cell_index] != "":
        return jsonify({"error": "Space already conquered!"}), 400

    game["board_state"][cell_index] = "X" if player == "P1" else "O"

    winner = check_winner(game["board_state"])
    if winner:
        game["status"] = "Finished"
        game["winner"] = winner
        return jsonify({
            "message": f"Player {winner} wins!",
            "board_state": game["board_state"],
            "winner": winner,
        }), 200

    if not empty_cells(game["board_state"]):
        game["status"] = "Draw"
        return jsonify({"message": "Game ended in a draw!", "board_state": game["board_state"]}), 200

    opponent_payload = {}
    if game["mode"] in ("cpu", "ai") and game["current_turn"] == "P1":
        move, source = choose_opponent_move(game["mode"], game["board_state"])
        valid = empty_cells(game["board_state"])

        if move is None or move not in valid:
            if game["mode"] == "ai":
                return jsonify({
                    "error": "AI opponent could not produce a valid move.",
                    "ai_source": source,
                    "board_state": game["board_state"],
                }), 502
            move = get_cpu_move(game["board_state"])

        game["board_state"][move] = "O"
        game["current_turn"] = "P1"
        opponent_payload = {"opponent_move": move, "opponent_source": source}
    else:
        game["current_turn"] = "P2" if game["current_turn"] == "P1" else "P1"

    winner = check_winner(game["board_state"])
    if winner:
        game["status"] = "Finished"
        game["winner"] = winner
        return jsonify({
            "message": f"Player {winner} wins!",
            "board_state": game["board_state"],
            "winner": winner,
            **opponent_payload,
        }), 200

    if not empty_cells(game["board_state"]):
        game["status"] = "Draw"
        return jsonify({
            "message": "Game ended in a draw!",
            "board_state": game["board_state"],
            **opponent_payload,
        }), 200

    return jsonify({
        "message": "Move processed successfully!",
        "board_state": game["board_state"],
        "next_turn": game["current_turn"],
        **opponent_payload,
    }), 200


if __name__ == "__main__":
    debug_mode = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=5050, debug=debug_mode)
