import tkinter as tk
from tkinter import messagebox
import random
import json
import threading
import requests
import game_engine

GET_BOT_MOVE_URL = "http://127.0.0.1:5050/api/get_bot_move"

class QuestionPopup:
    """Handles the Tkinter popup, the ticking timer, and the skip button."""
    def __init__(self, parent, question_data, player, skips_left, callback):
        self.top = tk.Toplevel(parent)
        self.top.title(f"Player {player} - Answer to Conquer!")
        self.top.geometry("350x250")
        self.top.transient(parent)
        self.top.grab_set()
        
        self.callback = callback
        self.correct_answer = question_data["answer"].lower()
        self.time_left = 15  # 15 seconds per turn
        self.timer_active = True
        
        # Timer Display
        self.timer_label = tk.Label(self.top, text=f"Time: {self.time_left}s", font=("Arial", 14, "bold"), fg="red")
        self.timer_label.pack(pady=5)
        
        tk.Label(self.top, text=question_data["question"], wraplength=280, font=("Arial", 12)).pack(pady=10)
        
        self.answer_entry = tk.Entry(self.top, font=("Arial", 12))
        self.answer_entry.pack(pady=5)
        self.answer_entry.focus()
        
        self.top.bind('<Return>', lambda event: self.submit(used_skip=False))
        tk.Button(self.top, text="Submit Answer", command=lambda: self.submit(used_skip=False)).pack(pady=5)
        
        # Skip Button Logic
        if skips_left > 0:
            tk.Button(self.top, text=f"Use Skip ({skips_left} left)", bg="gold", 
                      command=lambda: self.submit(used_skip=True)).pack(pady=5)
        else:
            tk.Label(self.top, text="No skips remaining", fg="gray").pack(pady=5)
            
        self.update_timer()

    def update_timer(self):
        if not self.timer_active:
            return
            
        if self.time_left > 0:
            self.time_left -= 1
            self.timer_label.config(text=f"Time: {self.time_left}s")
            self.top.after(1000, self.update_timer)
        else:
            # Time out triggers a failed answer automatically
            self.timer_label.config(text="TIME'S UP!")
            self.submit(timeout=True)

    def submit(self, used_skip=False, timeout=False):
        self.timer_active = False # Stop the clock
        
        if used_skip:
            self.top.destroy()
            self.callback(is_correct=False, used_skip=True, timeout=False)
            return
            
        if timeout:
            self.top.destroy()
            self.callback(is_correct=False, used_skip=False, timeout=True)
            return

        user_answer = self.answer_entry.get().strip().lower()
        is_correct = (user_answer == self.correct_answer)
        
        if not is_correct:
            messagebox.showerror("Incorrect!", f"The correct answer was: {self.correct_answer.title()}", parent=self.top)
            
        self.top.destroy()
        self.callback(is_correct, used_skip=False, timeout=False)


class GameBoard(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self.engine = game_engine.GameEngine()

        self.load_questions()

        # Header Frame for Status and Skips
        header_frame = tk.Frame(self)
        header_frame.grid(row=0, column=0, columnspan=5, pady=10)

        self.status_label = tk.Label(header_frame, text="Player 1's Turn", font=("Arial", 16, "bold"))
        self.status_label.pack()

        self.skip_label = tk.Label(header_frame, text="P1 Skips: 3  |  P2 Skips: 3", font=("Arial", 10))
        self.skip_label.pack()

        self.buttons = {}

        # Generate Grid
        for r in range(game_engine.BOARD_SIZE):
            for c in range(game_engine.BOARD_SIZE):
                btn = tk.Button(self, text="", width=8, height=4, font=("Arial", 12, "bold"),
                                command=lambda row=r, col=c: self.handle_click(row, col))
                btn.grid(row=r+1, column=c, padx=2, pady=2)
                self.buttons[(r, c)] = btn

    def on_show(self):
        """Resets the board for a fresh match each time this frame is shown."""
        self.engine.reset_game()
        self.active_deck = list(self.master_question_bank)
        random.shuffle(self.active_deck)
        self.sync_board_and_ui()

    def load_questions(self):
        with open("questions.json", "r") as f:
            self.master_question_bank = json.load(f)

        self.active_deck = list(self.master_question_bank)
        random.shuffle(self.active_deck)

    def handle_click(self, row, col):
        current_player = self.engine.active_player

        # Retrieve remaining skips from the backend engine dictionary
        # (Assumes Claude names the variable self.skips)
        skips_left = self.engine.skips.get(current_player, 0)

        if not self.active_deck:
            self.active_deck = list(self.master_question_bank)
            random.shuffle(self.active_deck)

        question_data = self.active_deck.pop()
        QuestionPopup(self.controller, question_data, current_player, skips_left,
                      lambda is_correct, used_skip, timeout: self.resolve_turn(is_correct, used_skip, timeout, row, col))

    def resolve_turn(self, is_correct, used_skip, timeout, row, col):
        current_player = self.engine.active_player
        
        if used_skip:
            messagebox.showinfo("Skip Used", "You used a skip to protect your tiles. Turn ends.")
            self.engine.fail_turn(player=current_player, used_skip=True)
            
        elif timeout or not is_correct:
            if timeout:
                messagebox.showwarning("Time Out", "You ran out of time!")
            
            # Backend handles the 40% chance to lose a tile
            self.engine.fail_turn(player=current_player, used_skip=False)
            
        else:
            # Player got it right. The backend claim_space handles the 20% overclock bonus.
            self.engine.claim_space(row, col)
            
        # Check Win States before passing turn
        if self.engine.check_win_condition(current_player):
            self.sync_board_and_ui()
            messagebox.showinfo("Victory!", f"Player {current_player} wins with 4-in-a-row!", parent=self.controller)
            self.disable_all_buttons()
            self.record_match_result(winner=current_player)
            self.controller.show_frame("StatsScreen")
            return

        if self.engine.is_board_full():
            self.sync_board_and_ui()
            winner = self.engine.get_territory_winner()
            if winner == 0:
                messagebox.showinfo("Game Over", "It's a complete tie!", parent=self.controller)
            else:
                messagebox.showinfo("Game Over", f"Board full! Player {winner} wins by territory control!", parent=self.controller)
            self.disable_all_buttons()
            self.record_match_result(winner=winner)
            self.controller.show_frame("StatsScreen")
            return

        self.engine.switch_turn()
        self.sync_board_and_ui()
        self.trigger_bot_turn()

    def trigger_bot_turn(self):
        """Runs whenever it becomes Player 2's turn in a VS Bot match.
        self.engine.board is the single source of truth - we snapshot it
        into gamemode.py's flat "X"/"O" format and ask its stateless
        /api/get_bot_move endpoint where to play, off the Tk main thread
        so Gemini's response time doesn't freeze the UI."""
        if not self.controller.active_match or self.engine.active_player != 2:
            return

        mode = self.controller.active_match.get("mode", "ai")
        board_snapshot = self.board_to_flat_list()
        self.disable_all_buttons()

        def call_server():
            try:
                response = requests.post(
                    GET_BOT_MOVE_URL,
                    json={"board_state": board_snapshot, "mode": mode},
                    timeout=20,
                )
                response.raise_for_status()
                data = response.json()
            except requests.RequestException as error:
                err_msg = str(error)
                self.controller.after(0, lambda msg=err_msg: self.handle_bot_error(msg))
                return

            self.controller.after(0, lambda: self.apply_bot_move(data))

        threading.Thread(target=call_server, daemon=True).start()

    def board_to_flat_list(self):
        """Converts engine.board's (row, col) -> owner dict into the flat,
        row-major "X"/"O"/"" list gamemode.py's move logic expects."""
        flat = []
        for r in range(game_engine.BOARD_SIZE):
            for c in range(game_engine.BOARD_SIZE):
                owner = self.engine.board[(r, c)]
                flat.append("X" if owner == 1 else "O" if owner == 2 else "")
        return flat

    def handle_bot_error(self, error):
        messagebox.showerror(
            "Bot server unavailable",
            f"Could not reach the gamemode server for the bot's move: {error}",
            parent=self.controller
        )
        self.sync_board_and_ui()  # re-enables the board so the match isn't stuck

    def apply_bot_move(self, data):
        move = data.get("move")

        if move is None or not (0 <= move < game_engine.BOARD_SIZE * game_engine.BOARD_SIZE):
            self.handle_bot_error(data.get("error", "invalid move returned"))
            return

        bot_row, bot_col = divmod(move, game_engine.BOARD_SIZE)

        if self.engine.board[(bot_row, bot_col)] is not None:
            # Shouldn't happen since the snapshot is authoritative, but fall
            # back to any empty tile rather than dropping the bot's turn.
            empty = [coord for coord, owner in self.engine.board.items() if owner is None]
            if not empty:
                self.sync_board_and_ui()
                return
            bot_row, bot_col = random.choice(empty)

        self.engine.claim_space(bot_row, bot_col)

        if self.engine.check_win_condition(2):
            self.sync_board_and_ui()
            messagebox.showinfo("Victory!", "Player 2 (Bot) wins with 4-in-a-row!", parent=self.controller)
            self.disable_all_buttons()
            self.record_match_result(winner=2)
            self.controller.show_frame("StatsScreen")
            return

        if self.engine.is_board_full():
            self.sync_board_and_ui()
            winner = self.engine.get_territory_winner()
            if winner == 0:
                messagebox.showinfo("Game Over", "It's a complete tie!", parent=self.controller)
            else:
                messagebox.showinfo("Game Over", f"Board full! Player {winner} wins by territory control!", parent=self.controller)
            self.disable_all_buttons()
            self.record_match_result(winner=winner)
            self.controller.show_frame("StatsScreen")
            return

        self.engine.switch_turn()
        self.sync_board_and_ui()

    def record_match_result(self, winner):
        # PlayerStats tracks a single identity; hotseat Player 1 is treated
        # as "the user" until per-player accounts exist.
        spaces = sum(1 for owner in self.engine.board.values() if owner == 1)
        result = "win" if winner == 1 else "loss"
        mode = self.controller.active_match["mode"] if self.controller.active_match else "local"
        self.controller.player_stats.update_game(result=result, mode=mode, spaces=spaces)

    def sync_board_and_ui(self):
        """Redraws the entire board and HUD to match the backend dictionaries."""
        # 1. Update the top labels
        self.status_label.config(text=f"Player {self.engine.active_player}'s Turn")
        
        p1_skips = self.engine.skips.get(1, 0)
        p2_skips = self.engine.skips.get(2, 0)
        self.skip_label.config(text=f"P1 Skips: {p1_skips}  |  P2 Skips: {p2_skips}")

        # 2. Sync every button on the grid
        for (r, c), owner in self.engine.board.items():
            btn = self.buttons[(r, c)]
            
            if owner == 1:
                btn.config(text="P1", bg="#add8e6", state="disabled")
            elif owner == 2:
                btn.config(text="P2", bg="#f08080", state="disabled")
            else:
                btn.config(text="", bg="SystemButtonFace", state="normal")

    def disable_all_buttons(self):
        for btn in self.buttons.values():
            btn.config(state="disabled")