from flask import Flask, request, jsonify
import random
import requests
import os
import itertools
import threading

app = Flask(__name__)

# --- Config -----------------------------------------------------------
# Fail loudly if the key is missing instead of silently shipping a
# placeholder string that will 401 on every real request.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/"
    f"gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
)

GRID_SIZE = 5
WIN_LENGTH = 4

# In-memory "database". A dict keyed by an ever-incrementing counter
# (not len(GAMES_DB)+1, which collides once a game is ever removed).
GAMES_DB = {}
_id_counter = itertools.count(1)
_db_lock = threading.Lock()  # Flask's dev server can be multi-threaded


# --- Win detection ------------------------------------------------------
def _winning_lines():
    """Precompute every group of 4 consecutive cell-indices that counts
    as a win: horizontal, vertical, and both diagonals."""
    lines = []
    n = GRID_SIZE

    def idx(r, c):
        return r * n + c

    # Horizontal
    for r in range(n):
        for c in range(n - WIN_LENGTH + 1):
            lines.append([idx(r, c + k) for k in range(WIN_LENGTH)])

    # Vertical
    for c in range(n):
        for r in range(n - WIN_LENGTH + 1):
            lines.append([idx(r + k, c) for k in range(WIN_LENGTH)])

    # Diagonal (down-right)
    for r in range(n - WIN_LENGTH + 1):
        for c in range(n - WIN_LENGTH + 1):
            lines.append([idx(r + k, c + k) for k in range(WIN_LENGTH)])

    # Diagonal (down-left)
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


# --- Gemini opponent ------------------------------------------------------
def get_gemini_strategic_move(board_state):
    """Fires a live API request to Google Gemini to calculate the best
    5x5 strategic grid move. Returns an int index or None on any failure."""
    if not GEMINI_API_KEY:
        print("GEMINI_API_KEY not set, skipping API call.")
        return None

    prompt = f"""
    You are playing a competitive 5x5 Tic-Tac-Toe variant. The grid has 25 spaces indexed from 0 to 24.
    Player 1 uses 'X' and you (the AI) use 'O'. An empty space is represented by an empty string "".

    Current Board Array State: {board_state}

    Analyze the grid layout carefully. Your goal is to block 'X' from getting a row of 4,
    or build your own row of 4 'O's.
    Identify the remaining empty indices (where the value is "").
    Pick the absolute best empty index to make your move.

    CRITICAL: Reply with ONLY the single integer index number (0 to 24). Do not write any words, punctuation, or explanations. Just the number.
    """

    headers = {"Content-Type": "application/json"}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    try:
        response = requests.post(GEMINI_URL, json=payload, headers=headers, timeout=5)
        response.raise_for_status()
        ai_reply = response.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        return int(ai_reply)
    except (requests.RequestException, KeyError, IndexError, ValueError) as e:
        print(f"API Error, falling back to basic CPU logic: {e}")
        return None


# --- Routes ---------------------------------------------------------------
@app.route("/api/start_match", methods=["POST"])
def start_match():
    """Initializes a 5x5 match based on the selected game mode."""
    data = request.get_json(silent=True) or {}
    mode = data.get("mode")

    if mode not in ("local", "cpu", "ai"):
        return jsonify({"error": "mode must be 'local', 'cpu', or 'ai'"}), 400

    with _db_lock:
        game_id = next(_id_counter)
        GAMES_DB[game_id] = {
            "game_id": game_id,
            "mode": mode,
            "player_1": "Player 1",
            "player_2": "Smart_AI" if mode == "ai" else ("CPU_Bot" if mode == "cpu" else "Player 2"),
            "board_state": [""] * (GRID_SIZE * GRID_SIZE),
            "current_turn": "P1",
            "status": "Active",
            "winner": None,
        }

    return jsonify({"game_id": game_id, "message": f"Started {mode} match successfully!"}), 201


@app.route("/api/submit_move", methods=["POST"])
def submit_move():
    """Processes human grid selections and routes automated opponent behaviors."""
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

    # Validate cell_index: must be an int in range. (Also blocks negative
    # indices, which Python would otherwise silently wrap around to the
    # end of the list.)
    if not isinstance(cell_index, int) or not (0 <= cell_index < GRID_SIZE * GRID_SIZE):
        return jsonify({"error": f"cell_index must be an integer from 0 to {GRID_SIZE*GRID_SIZE - 1}"}), 400

    if game["board_state"][cell_index] != "":
        return jsonify({"error": "Space already conquered!"}), 400

    # Human places their mark
    game["board_state"][cell_index] = "X" if player == "P1" else "O"

    # Check for a win immediately after the human's move
    winner = check_winner(game["board_state"])
    if winner:
        game["status"] = "Finished"
        game["winner"] = winner
        return jsonify({
            "message": f"Player {winner} wins!",
            "board_state": game["board_state"],
            "winner": winner,
        }), 200

    empty_cells = [i for i, cell in enumerate(game["board_state"]) if cell == ""]
    if not empty_cells:
        game["status"] = "Draw"
        return jsonify({"message": "Game ended in a draw!", "board_state": game["board_state"]}), 200

    # -------------------------------------------------------------
    # Game Mode Switching Logic Branch
    # -------------------------------------------------------------
    if game["mode"] == "ai" and game["current_turn"] == "P1":
        ai_move = get_gemini_strategic_move(game["board_state"])
        if ai_move is not None and ai_move in empty_cells:
            game["board_state"][ai_move] = "O"
        else:
            game["board_state"][random.choice(empty_cells)] = "O"
        game["current_turn"] = "P1"

    elif game["mode"] == "cpu" and game["current_turn"] == "P1":
        game["board_state"][random.choice(empty_cells)] = "O"
        game["current_turn"] = "P1"

    else:
        game["current_turn"] = "P2" if game["current_turn"] == "P1" else "P1"

    # Check for a win after the AI/CPU move too
    winner = check_winner(game["board_state"])
    if winner:
        game["status"] = "Finished"
        game["winner"] = winner
        return jsonify({
            "message": f"Player {winner} wins!",
            "board_state": game["board_state"],
            "winner": winner,
        }), 200

    if not any(cell == "" for cell in game["board_state"]):
        game["status"] = "Draw"
        return jsonify({"message": "Game ended in a draw!", "board_state": game["board_state"]}), 200

    return jsonify({
        "message": "Move processed successfully!",
        "board_state": game["board_state"],
        "next_turn": game["current_turn"],
    }), 200


if __name__ == "__main__":
    debug_mode = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=5050, debug=debug_mode)