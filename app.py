from flask import Flask, request, jsonify
import random

app = Flask(__name__)

# Temporary database mock for tracking active game states
GAMES_DB = {}

@app.route('/api/start_match', methods=['POST'])
def start_match():
    """Initializes a 5x5 match based on the selected game mode."""
    data = request.json
    game_id = len(GAMES_DB) + 1
    mode = data.get('mode') # 'local' or 'ai'
    
    # Generate an empty 5x5 board grid array (25 elements)
    initial_board = [""] * 25 
    
    GAMES_DB[game_id] = {
        "game_id": game_id,
        "mode": mode,
        "player_1": "Player 1",
        "player_2": "AI_Bot" if mode == 'ai' else "Player 2",
        "board_state": initial_board,
        "current_turn": "P1",
        "status": "Active"
    }
    
    return jsonify({"game_id": game_id, "message": f"Started {mode} match successfully!"}), 201

@app.route('/api/submit_move', methods=['POST'])
def submit_move():
    """Processes human grid selections and branches behavior based on the game mode."""
    data = request.json
    game_id = data.get('game_id')
    player = data.get('player') # 'P1' or 'P2'
    cell_index = data.get('cell_index') # Integer from 0 to 24
    
    game = GAMES_DB.get(game_id)
    if not game or game["status"] != "Active":
        return jsonify({"error": "Match not active"}), 400
        
    if game["current_turn"] != player:
        return jsonify({"error": "It is not your turn!"}), 403

    # 1. Validate if the targeted space is empty
    if game["board_state"][cell_index] != "":
        return jsonify({"error": "Space already conquered!"}), 400
        
    # 2. Claim the cell with the active player's marker
    marker = "X" if player == "P1" else "O"
    game["board_state"][cell_index] = marker

    # -------------------------------------------------------------
    # Core Feature Logic: Game Mode Switching Handler
    # -------------------------------------------------------------
    if game["mode"] == "ai" and game["current_turn"] == "P1":
        # AI Mode branch: Find available spaces and immediately execute bot move
        empty_cells = [i for i, cell in enumerate(game["board_state"]) if cell == ""]
        if empty_cells:
            ai_choice = random.choice(empty_cells) # AI picks a free cell
            game["board_state"][ai_choice] = "O"   # Conquered by AI
            
        # Control loops right back to P1 since the AI played its automated turn
        game["current_turn"] = "P1"
    else:
        # Local Mode branch: Simply pass the turn control to the other human player
        game["current_turn"] = "P2" if game["current_turn"] == "P1" else "P1"

    return jsonify({
        "message": "Move processed successfully!",
        "board_state": game["board_state"],
        "next_turn": game["current_turn"]
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050, debug=True)