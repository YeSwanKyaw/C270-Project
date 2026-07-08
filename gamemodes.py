import tkinter as tk
from tkinter import messagebox
import uuid

import requests

GAMEMODE_API_URL = "http://127.0.0.1:5050/api/start_match"


class GamemodeSelect(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#7CB342")
        self.controller = controller

        title_label = tk.Label(
            self,
            text="VS BOT",
            font=("Arial", 30, "bold"),
            bg="#7CB342",
            fg="white"
        )
        title_label.pack(pady=40)

        mode_buttons = [
            ("CPU (rule-based)", "cpu", "#F39C12"),
            ("Smart AI (Gemini)", "ai", "#3498DB"),
        ]

        button_row = tk.Frame(self, bg="#7CB342")
        button_row.pack(pady=30)

        for text, mode, color in mode_buttons:
            tk.Button(
                button_row,
                text=text,
                command=lambda m=mode: self.start_match(m),
                font=("Arial", 16, "bold"),
                width=20,
                height=14,
                bg=color,
                fg="white",
                anchor="n",
                pady=22
            ).pack(side="left", padx=20)

        back_button = tk.Button(
            self,
            text="Back",
            command=lambda: controller.show_frame("MainMenu"),
            font=("Arial", 16, "bold"),
            width=12
        )
        back_button.pack(pady=30)

    def start_match(self, mode):
        # gamemode.py's Flask API models a plain X/O 4-in-a-row board, while
        # GameBoard's engine models trivia-claim tiles with skips/overclock.
        # Feeding opponent moves from that API into GameBoard's turn logic is
        # separate follow-up work - this call only confirms the bot server is
        # reachable and reserves a match id.
        try:
            response = requests.post(GAMEMODE_API_URL, json={"mode": mode}, timeout=5)
            response.raise_for_status()
        except requests.RequestException as error:
            # ==================== START OF DUMMY AREA ====================
            # CPU mode can run locally when the separate Flask bot server is
            # unavailable.  This keeps the GUI usable during development.
            if mode == "cpu":
                self.controller.active_match = {
                    "match_id": "dummy-" + uuid.uuid4().hex,
                    "mode": "cpu",
                    "dummy": True,
                }
                self.controller.show_frame("GameBoard")
                return
            # ===================== END OF DUMMY AREA =====================

            messagebox.showerror(
                "Bot server unavailable",
                f"Could not reach the gamemode server (is gamemode.py running?): {error}",
                parent=self.controller
            )
            return

        # /api/start_match's response doesn't echo back "mode", so record
        # it here - main_gui.py needs it to ask for cpu vs. ai bot moves.
        match_info = response.json()
        match_info["mode"] = mode
        self.controller.active_match = match_info
        self.controller.show_frame("GameBoard")
