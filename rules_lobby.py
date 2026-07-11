import tkinter as tk


class RulesLobbyFrame(tk.Frame):
    """Pre-match rules screen shown before VS Bot or Multiplayer starts.

    `next_frame` (set via on_show) tracks which screen "START MATCH"
    should continue to - "GamemodeSelect" for VS Bot, "MultiplayerScreen"
    for Multiplayer - so this one frame can serve both entry points.
    """

    RULES_TEXT = (
        "THE CORE RULES\n"
        "• The Board: 5x5 grid.\n"
        "• The Goal: Claim spaces by correctly answering trivia. "
        "Form a continuous row of four spaces to win.\n"
        "• The Tiebreaker: If the board fills up, the player with the "
        "most spaces wins.\n"
        "\n"
        "POWERS & PENALTIES\n"
        "• Overclock Power: 20% chance on a correct answer to get an "
        "extra adjacent tile for free.\n"
        "• Skips: 3 skips per match to avoid answering, by default.\n"
        "• Turn Failure Penalty: Answer wrong or run out of time? "
        "You have a 40% chance to lose a random tile you already own.\n"
        "\n"
        "These are the rules for Standard Mode"
    )

    def __init__(self, parent, controller):
        super().__init__(parent, bg="#2C3E50")
        self.controller = controller
        self.next_frame = "GamemodeSelect"

        tk.Label(
            self,
            text="PRE-MATCH RULES",
            font=("Arial", 28, "bold"),
            bg="#2C3E50",
            fg="white",
        ).pack(pady=(30, 10))

        self.subtitle_label = tk.Label(
            self,
            text="",
            font=("Arial", 14, "italic"),
            bg="#2C3E50",
            fg="#F5B041",
        )
        self.subtitle_label.pack(pady=(0, 20))

        rules_box = tk.Frame(self, bg="white", bd=2, relief="groove")
        rules_box.pack(padx=40, pady=10, fill="both", expand=True)

        tk.Label(
            rules_box,
            text=self.RULES_TEXT,
            font=("Arial", 13),
            bg="white",
            fg="black",
            justify="left",
            anchor="w",
            wraplength=760,
        ).pack(padx=25, pady=25, anchor="w")

        tk.Button(
            self,
            text="START MATCH",
            command=self.start_match,
            font=("Arial", 22, "bold"),
            bg="#27AE60",
            fg="white",
            activebackground="#2ECC71",
            activeforeground="white",
            width=20,
            height=2,
            relief="raised",
            bd=6,
            cursor="hand2",
        ).pack(pady=25)

        tk.Button(
            self,
            text="Back",
            command=lambda: controller.show_frame("MainMenu"),
            font=("Arial", 12, "bold"),
            width=10,
        ).pack(pady=(0, 20))

    def on_show(self, next_frame="GamemodeSelect"):
        self.next_frame = next_frame
        subtitle_by_target = {
            "GamemodeSelect": "Mode: VS Bot",
            "MultiplayerScreen": "Mode: Multiplayer",
        }
        self.subtitle_label.configure(text=subtitle_by_target.get(next_frame, ""))

    def start_match(self):
        self.controller.show_frame(self.next_frame)
