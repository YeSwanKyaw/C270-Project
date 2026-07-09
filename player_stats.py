import tkinter as tk


class PlayerStats:
    def __init__(self, name):
        self.name = name

        self.games_played = 0
        self.wins = 0
        self.losses = 0

        self.local_wins = 0
        self.ai_wins = 0

        self.total_spaces = 0

    # Function called after every game
    def update_game(self, result, mode, spaces):
        self.games_played += 1
        self.total_spaces += spaces

        if result == "win":
            self.wins += 1

            if mode == "local":
                self.local_wins += 1
            elif mode == "ai":
                self.ai_wins += 1
        else:
            self.losses += 1

    def get_win_rate(self):
        if self.games_played == 0:
            return 0

        return (self.wins / self.games_played) * 100


class StatsScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        tk.Label(
            self,
            text="PLAYER STATISTICS",
            font=("Arial", 18, "bold")
        ).pack(pady=15)

        self.table = tk.Frame(self)
        self.table.pack(pady=10)

        self.values = {}

        fields = [
            "Player Name",
            "Games Played",
            "Wins",
            "Losses",
            "Win Rate",
            "Local Mode Wins",
            "AI Mode Wins",
            "Total Spaces Captured"
        ]

        for row, field in enumerate(fields):
            tk.Label(
                self.table,
                text=field + ":",
                font=("Arial", 12, "bold"),
                width=22,
                anchor="w"
            ).grid(row=row, column=0, padx=10, pady=5, sticky="w")

            value = tk.Label(
                self.table,
                text="",
                font=("Arial", 12),
                width=18,
                anchor="w"
            )
            value.grid(row=row, column=1, padx=10, pady=5, sticky="w")

            self.values[field] = value

        button_row = tk.Frame(self)
        button_row.pack(pady=20)

        tk.Button(
            button_row,
            text="Back",
            width=15,
            command=lambda: controller.show_frame("MainMenu")
        ).pack(side="left", padx=10)

    def on_show(self):
        self.refresh()

    def refresh(self):
        player = self.controller.player_stats

        self.values["Player Name"].config(text=player.name)
        self.values["Games Played"].config(text=player.games_played)
        self.values["Wins"].config(text=player.wins)
        self.values["Losses"].config(text=player.losses)
        self.values["Win Rate"].config(text=f"{player.get_win_rate():.2f}%")
        self.values["Local Mode Wins"].config(text=player.local_wins)
        self.values["AI Mode Wins"].config(text=player.ai_wins)
        self.values["Total Spaces Captured"].config(text=player.total_spaces)