import os
import tkinter as tk
from tkinter import messagebox
from pathlib import Path
import uuid

import requests
from dotenv import load_dotenv

try:
    from PIL import Image, ImageTk
except ImportError:
    Image = None
    ImageTk = None

load_dotenv()
_BOT_API_BASE = os.getenv("BOT_API_BASE", "http://127.0.0.1:5050").rstrip("/")
GAMEMODE_API_URL = f"{_BOT_API_BASE}/api/start_match"


class GamemodeSelect(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#7CB342")
        self.controller = controller
        self.mode_images = {}

        title_label = tk.Label(
            self,
            text="VS BOT",
            font=("Arial", 30, "bold"),
            bg="#7CB342",
            fg="white"
        )
        title_label.pack(pady=40)

        mode_buttons = [
            ("CPU (rule-based)", "cpu", "#F39C12", "Vs Computer Logo.png"),
            ("Smart AI (Groq)", "ai", "#3498DB", "Vs AI logo.jpg"),
        ]

        button_row = tk.Frame(self, bg="#7CB342")
        button_row.pack(pady=30)

        for text, mode, color, image_name in mode_buttons:
            logo = self.load_mode_image(image_name)
            self.mode_images[mode] = logo

            button_options = {
                "text": text,
                "command": lambda m=mode: self.start_match(m),
                "font": ("Arial", 16, "bold"),
                "bg": color,
                "fg": "white",
                "pady": 18,
                "cursor": "hand2",
            }
            if logo is not None:
                button_options.update({
                    "image": logo,
                    "compound": "top",
                    "width": 230,
                    "height": 260,
                })
            else:
                button_options.update({"width": 20, "height": 14})

            tk.Button(button_row, **button_options).pack(side="left", padx=20)

        back_button = tk.Button(
            self,
            text="Back",
            command=lambda: controller.show_frame("MainMenu"),
            font=("Arial", 16, "bold"),
            width=12
        )
        back_button.pack(pady=30)

    def load_mode_image(self, image_name):
        if Image is None or ImageTk is None:
            return None

        asset_path = Path(__file__).resolve().parent / "Assets" / image_name
        image = Image.open(asset_path)
        resampling_filter = getattr(Image, "Resampling", Image).LANCZOS
        image.thumbnail((150, 150), resampling_filter)
        return ImageTk.PhotoImage(image)

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
