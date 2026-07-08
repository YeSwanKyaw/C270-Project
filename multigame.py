import json
import math
import random
import tkinter as tk
from pathlib import Path
from tkinter import messagebox

import client
import game_engine
import host
from main_gui import QuestionPopup


class MultiGame(tk.Frame):
    """A networked game board shared by Player 1 and Player 2."""

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.engine = game_engine.GameEngine()
        self.role = None
        self.player_number = None
        self.active = False
        # ==================== START OF MULTIPLAYER AVERAGED SETTINGS ====================
        self.match_ready = False
        self.match_timer = 15
        # ===================== END OF MULTIPLAYER AVERAGED SETTINGS =====================
        # ==================== START OF MULTIPLAYER RANDOM MODE ====================
        self.match_chance_mode = "normal"
        # ===================== END OF MULTIPLAYER RANDOM MODE =====================

        questions_path = Path(__file__).with_name("questions.json")
        with questions_path.open("r", encoding="utf-8") as file:
            self.master_question_bank = json.load(file)
        self.active_deck = list(self.master_question_bank)

        header_frame = tk.Frame(self)
        header_frame.pack(pady=(8, 4))

        self.status_label = tk.Label(header_frame, font=("Arial", 16, "bold"))
        self.status_label.pack()

        self.skip_label = tk.Label(
            header_frame,
            text="P1 Skips: 3  |  P2 Skips: 3",
            font=("Arial", 10),
        )
        self.skip_label.pack()

        # ==================== START OF MULTIPLAYER RANDOM MODE ====================
        self.mode_label = tk.Label(
            header_frame,
            text="Mode: Choosing...",
            font=("Arial", 11, "bold"),
        )
        self.mode_label._preserve_theme_foreground = True
        self.mode_label.pack(pady=(2, 0))
        # ===================== END OF MULTIPLAYER RANDOM MODE =====================

        # Packing this frame without a side or anchor keeps the game centered.
        board_frame = tk.Frame(self)
        board_frame.pack()
        self.buttons = {}
        for row in range(game_engine.BOARD_SIZE):
            for col in range(game_engine.BOARD_SIZE):
                button = tk.Button(
                    board_frame,
                    width=8,
                    height=4,
                    font=("Arial", 12, "bold"),
                    command=lambda r=row, c=col: self.handle_click(r, c),
                )
                button.grid(row=row, column=col, padx=2, pady=2)
                self.buttons[(row, col)] = button

        # Chat is intentionally placed below the shared game board.
        self.chat_box = tk.Text(self, width=65, height=5, state="disabled")
        self.chat_box.pack(pady=(8, 4))

        chat_row = tk.Frame(self)
        chat_row.pack()
        self.chat_entry = tk.Entry(chat_row, width=48, font=("Arial", 11))
        self.chat_entry.pack(side="left", padx=5)
        self.chat_entry.bind("<Return>", lambda event: self.send_chat())
        tk.Button(chat_row, text="Send", command=self.send_chat).pack(side="left")
        tk.Button(chat_row, text="Leave Game", command=self.leave_game).pack(side="left", padx=10)

    def on_show(self, role=None):
        self.role = role or self.role
        self.player_number = 1 if self.role == "host" else 2
        self.active = True
        # ==================== START OF MULTIPLAYER AVERAGED SETTINGS ====================
        self.match_ready = False
        self.match_timer = 15
        # ===================== END OF MULTIPLAYER AVERAGED SETTINGS =====================
        # ==================== START OF MULTIPLAYER RANDOM MODE ====================
        self.match_chance_mode = "normal"
        # ===================== END OF MULTIPLAYER RANDOM MODE =====================
        self.active_deck = list(self.master_question_bank)
        random.shuffle(self.active_deck)
        self.chat_box.configure(state="normal")
        self.chat_box.delete("1.0", "end")
        self.chat_box.configure(state="disabled")

        if self.role == "host":
            self.engine.reset_game()
        # ==================== START OF MULTIPLAYER AVERAGED SETTINGS ====================
        else:
            client.send_data({
                "type": "match_settings",
                "timer": self.controller.question_timer,
                "skips": self.controller.cpu_skips,
                # ==================== START OF MULTIPLAYER RANDOM MODE ====================
                "chance_mode": self.controller.cpu_chance_mode,
                # ===================== END OF MULTIPLAYER RANDOM MODE =====================
            })
        # The host waits for Player 2's values before enabling or publishing
        # the shared board.
        # ===================== END OF MULTIPLAYER AVERAGED SETTINGS =====================
        self.sync_board()

    def handle_click(self, row, col):
        if self.engine.active_player != self.player_number:
            return
        if self.engine.board[(row, col)] is not None:
            return
        if not self.active_deck:
            self.active_deck = list(self.master_question_bank)
            random.shuffle(self.active_deck)

        question = self.active_deck.pop()
        skips = self.engine.skips.get(self.player_number, 0)
        QuestionPopup(
            self.controller,
            question,
            self.player_number,
            skips,
            # ==================== START OF MULTIPLAYER SKIP FIX ====================
            lambda is_correct, used_skip, timeout: self.submit_turn(
                row, col, is_correct, used_skip, timeout
            ),
            # ===================== END OF MULTIPLAYER SKIP FIX =====================
            # ==================== START OF MULTIPLAYER AVERAGED SETTINGS ====================
            timer_seconds=self.match_timer,
            # ===================== END OF MULTIPLAYER AVERAGED SETTINGS =====================
        )

    def submit_turn(self, row, col, correct, used_skip, timeout):
        action = {
            "type": "game_action",
            "player": self.player_number,
            "row": row,
            "col": col,
            "correct": correct,
            "used_skip": used_skip,
            "timeout": timeout,
        }
        if self.role == "host":
            self.apply_action(action)
        else:
            client.send_data(action)

    def apply_action(self, action):
        """Host validates and applies a turn, then publishes one shared state."""
        player = action.get("player")
        row, col = action.get("row"), action.get("col")
        if player != self.engine.active_player or (row, col) not in self.engine.board:
            return
        if self.engine.board[(row, col)] is not None:
            return

        if action.get("correct"):
            self.engine.claim_space(row, col)
        else:
            # ==================== START OF MULTIPLAYER SKIP FIX ====================
            # The host is authoritative: only consume/protect with a skip when
            # that player actually has one remaining.
            used_skip = action.get("used_skip", False) and self.engine.skips.get(player, 0) > 0
            self.engine.fail_turn(player, used_skip)
            # ===================== END OF MULTIPLAYER SKIP FIX =====================

        winner = player if self.engine.check_win_condition(player) else None
        if winner is None and self.engine.is_board_full():
            winner = self.engine.get_territory_winner()
        if winner is None:
            self.engine.switch_turn()

        self.send_state(winner)
        self.sync_board()
        if winner is not None:
            self.show_result(winner)

    def send_state(self, winner=None):
        board = [
            self.engine.board[(row, col)]
            for row in range(game_engine.BOARD_SIZE)
            for col in range(game_engine.BOARD_SIZE)
        ]
        host.send_data({
            "type": "game_state",
            "board": board,
            "active_player": self.engine.active_player,
            "skips": self.engine.skips,
            "winner": winner,
            # ==================== START OF MULTIPLAYER AVERAGED SETTINGS ====================
            "timer": self.match_timer,
            # ===================== END OF MULTIPLAYER AVERAGED SETTINGS =====================
            # ==================== START OF MULTIPLAYER RANDOM MODE ====================
            "chance_mode": self.match_chance_mode,
            # ===================== END OF MULTIPLAYER RANDOM MODE =====================
        })

    def handle_network_message(self, data):
        if not self.active:
            return
        message_type = data.get("type")
        # ==================== START OF MULTIPLAYER AVERAGED SETTINGS ====================
        if message_type == "match_settings" and self.role == "host":
            self.match_timer = math.ceil(
                (self.controller.question_timer + int(data.get("timer", 15))) / 2
            )
            averaged_skips = math.ceil(
                (self.controller.cpu_skips + int(data.get("skips", 3))) / 2
            )
            self.engine.skips = {1: averaged_skips, 2: averaged_skips}
            # ==================== START OF MULTIPLAYER RANDOM MODE ====================
            player_modes = [
                self.controller.cpu_chance_mode,
                data.get("chance_mode", "normal"),
            ]
            self.match_chance_mode = random.choice(player_modes)
            chance_settings = {
                "safe": (0.0, 0.0),
                "normal": (
                    game_engine.OVERCLOCK_BONUS_CHANCE,
                    game_engine.TILE_LOSS_CHANCE,
                ),
                "chaos": (1.0, 1.0),
            }
            bonus_chance, loss_chance = chance_settings.get(
                self.match_chance_mode, chance_settings["normal"]
            )
            self.engine.overclock_bonus_chance = bonus_chance
            self.engine.tile_loss_chance = loss_chance
            # ===================== END OF MULTIPLAYER RANDOM MODE =====================
            self.match_ready = True
            self.send_state()
            self.sync_board()
            return
        # ===================== END OF MULTIPLAYER AVERAGED SETTINGS =====================

        if message_type == "game_action" and self.role == "host":
            self.apply_action(data)
        elif message_type == "game_state" and self.role == "client":
            for index, owner in enumerate(data.get("board", [])):
                row, col = divmod(index, game_engine.BOARD_SIZE)
                self.engine.board[(row, col)] = owner
            self.engine.active_player = data.get("active_player", 1)
            skips = data.get("skips", {"1": 3, "2": 3})
            self.engine.skips = {int(key): value for key, value in skips.items()}
            # ==================== START OF MULTIPLAYER AVERAGED SETTINGS ====================
            self.match_timer = int(data.get("timer", 15))
            self.match_ready = True
            # ===================== END OF MULTIPLAYER AVERAGED SETTINGS =====================
            # ==================== START OF MULTIPLAYER RANDOM MODE ====================
            self.match_chance_mode = data.get("chance_mode", "normal")
            # ===================== END OF MULTIPLAYER RANDOM MODE =====================
            self.sync_board()
            if data.get("winner") is not None:
                self.show_result(data["winner"])
        elif message_type == "test_message":
            self.add_chat(f'{data.get("sender", "Other player")}: {data.get("message", "")}')

    def sync_board(self):
        # ==================== START OF MULTIPLAYER AVERAGED SETTINGS ====================
        if not self.match_ready:
            status_text = "Waiting for both players' settings..."
        else:
            status_text = (
                f"{self.controller.player_stats.name} is Player {self.player_number}"
                f"  |  Player {self.engine.active_player}'s turn"
            )
        self.status_label.configure(text=status_text)
        # ===================== END OF MULTIPLAYER AVERAGED SETTINGS =====================
        self.skip_label.configure(
            text=(
                f"P1 Skips: {self.engine.skips.get(1, 0)}  |  "
                f"P2 Skips: {self.engine.skips.get(2, 0)}"
            )
        )
        # ==================== START OF MULTIPLAYER RANDOM MODE ====================
        mode_display = {
            "safe": ("Simple", "#2ECC71"),
            "normal": ("Normal", "#F39C12"),
            "chaos": ("Extreme", "#E74C3C"),
        }
        if self.match_ready:
            mode_name, mode_color = mode_display.get(
                self.match_chance_mode, mode_display["normal"]
            )
            self.mode_label.configure(text=f"Mode: {mode_name}", fg=mode_color)
        else:
            self.mode_label.configure(text="Mode: Choosing...", fg="#707070")
        # ===================== END OF MULTIPLAYER RANDOM MODE =====================
        for coordinate, owner in self.engine.board.items():
            button = self.buttons[coordinate]
            if owner == 1:
                # ==================== START OF TILE COLOR SETTINGS ====================
                tile_color = self.controller.player_tile_color
                text_color = "white" if tile_color == "#000000" else "black"
                button.configure(text="P1", bg=tile_color, fg=text_color, state="disabled")
                # ===================== END OF TILE COLOR SETTINGS =====================
            elif owner == 2:
                # ==================== START OF TILE COLOR SETTINGS ====================
                tile_color = self.controller.opponent_tile_color
                text_color = "white" if tile_color == "#000000" else "black"
                button.configure(text="P2", bg=tile_color, fg=text_color, state="disabled")
                # ===================== END OF TILE COLOR SETTINGS =====================
            else:
                # ==================== START OF MULTIPLAYER AVERAGED SETTINGS ====================
                enabled = self.match_ready and self.engine.active_player == self.player_number
                # ===================== END OF MULTIPLAYER AVERAGED SETTINGS =====================
                button.configure(text="", bg="SystemButtonFace", state="normal" if enabled else "disabled")

        self.controller.apply_theme(self)

    def send_chat(self):
        message = self.chat_entry.get().strip()
        if not message:
            return
        # ==================== START OF NAME SETTINGS ====================
        username = self.controller.player_stats.name
        sent = (
            host.send_message(message, username)
            if self.role == "host"
            else client.send_message(message, username)
        )
        if sent:
            self.add_chat(username + ": " + message)
            self.chat_entry.delete(0, "end")
        # ===================== END OF NAME SETTINGS =====================

    def add_chat(self, message):
        self.chat_box.configure(state="normal")
        self.chat_box.insert("end", message + "\n")
        self.chat_box.see("end")
        self.chat_box.configure(state="disabled")

    def show_result(self, winner):
        text = "The match is a tie!" if winner == 0 else f"Player {winner} wins!"
        messagebox.showinfo("Game Over", text, parent=self.controller)
        self.sync_board()

    def leave_game(self):
        self.active = False
        host.stop_server()
        client.disconnect()
        self.controller.show_frame("MainMenu")
