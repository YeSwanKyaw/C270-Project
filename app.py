from flask import Flask, request, jsonify, render_template
import sqlite3
import json

app = Flask(__name__)
DB_FILE = "tictactoe.db"

def init_db():
    """Initializes the database structure on startup if it doesn't exist."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # Create Users Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            xp INTEGER DEFAULT 0
        )
    ''')
    # Create Games Table to store board state asynchronously
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS games (
            game_id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_x TEXT NOT NULL,
            player_o TEXT NOT NULL,
            board_state TEXT NOT NULL, -- Stored as a JSON string array
            current_turn TEXT NOT NULL, -- 'X' or 'O'
            game_status TEXT DEFAULT 'Active' -- 'Active', 'X_Won', 'O_Won', 'Draw'
        )
    ''')
    conn.commit()
    conn.close()

# ----------------- 👤 USER & GUEST ROUTES -----------------

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password') # In a real app, hash this!
    
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        return jsonify({"message": "Registration successful!"}), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "Username already exists"}), 400
    finally:
        conn.close()

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT password, xp FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    
    if user and user[0] == password:
        return jsonify({"message": "Login successful", "username": username, "xp": user[1]}), 200
    return jsonify({"error": "Invalid credentials"}), 401

# ----------------- 🎮 GAME ENGINE ROUTES -----------------

@app.route('/api/create_game', methods=['POST'])
def create_game():
    """Creates a new game match entry."""
    data = request.json
    player_x = data.get('player_x', 'Guest_X')
    player_o = data.get('player_o', 'Guest_O')
    initial_board = json.dumps(["", "", "", "", "", "", "", "", ""]) # Empty 3x3 grid
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO games (player_x, player_o, board_state, current_turn)
        VALUES (?, ?, ?, 'X')
    ''', (player_x, player_o, initial_board))
    game_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return jsonify({"game_id": game_id, "message": "Game matching created successfully!"}), 201

@app.route('/api/get_game/<int:game_id>', methods=['GET'])
def get_game(game_id):
    """Fetches the current state of the board asynchronously for players."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT player_x, player_o, board_state, current_turn, game_status FROM games WHERE game_id = ?", (game_id,))
    game = cursor.fetchone()
    conn.close()
    
    if not game:
        return jsonify({"error": "Game match not found"}), 404
        
    return jsonify({
        "game_id": game_id,
        "player_x": game[0],
        "player_o": game[1],
        "board_state": json.loads(game[2]),
        "current_turn": game[3],
        "game_status": game[4]
    }), 200

@app.route('/api/make_move', methods=['POST'])
def make_move():
    """Validates player turn, updates grid state, and switches active turn."""
    data = request.json
    game_id = data.get('game_id')
    player = data.get('player') # The username of person clicking
    cell_index = data.get('cell_index') # Number 0 to 8
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT player_x, player_o, board_state, current_turn, game_status FROM games WHERE game_id = ?", (game_id,))
    game = cursor.fetchone()
    
    if not game or game[4] != 'Active':
        return jsonify({"error": "Game is not active or doesn't exist"}), 400
        
    player_x, player_o, board_state, current_turn, _ = game
    board = json.loads(board_state)
    
    # 1. Check if it's the correct person's turn
    expected_user = player_x if current_turn == 'X' else player_o
    if player != expected_user:
        return jsonify({"error": "It is not your turn!"}), 403
        
    # 2. Check if square is empty
    if board[cell_index] != "":
        return jsonify({"error": "Cell already taken!"}), 400
        
    # 3. Apply move and change turn toggle
    board[cell_index] = current_turn
    next_turn = 'O' if current_turn == 'X' else 'X'
    
    cursor.execute("UPDATE games SET board_state = ?, current_turn = ? WHERE game_id = ?", 
                   (json.dumps(board), next_turn, game_id))
    conn.commit()
    conn.close()
    
    return jsonify({"message": "Move recorded successfully!", "new_board": board}), 200

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5050, debug=True)