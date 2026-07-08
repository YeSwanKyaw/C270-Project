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

        title = tk.Label(self, text="PLAYER STATISTICS", font=("Arial", 20, "bold"))
        title.pack(pady=20)

        self.stats_label = tk.Label(self, font=("Arial", 14), justify="left")
        self.stats_label.pack(pady=20)

        button_row = tk.Frame(self)
        button_row.pack(pady=10)

        tk.Button(button_row, text="Refresh Stats", command=self.refresh).pack(side="left", padx=5)
        tk.Button(
            button_row,
            text="Back",
            command=lambda: controller.show_frame("MainMenu")
        ).pack(side="left", padx=5)

    def on_show(self):
        self.refresh()

    def refresh(self):
        player = self.controller.player_stats

        text = f"""
Player Name:
{player.name}


Games Played:
{player.games_played}


Wins:
{player.wins}


Losses:
{player.losses}


Win Rate:
{player.get_win_rate():.2f}%


Local Mode Wins:
{player.local_wins}


AI Mode Wins:
{player.ai_wins}


Total Spaces Captured:
{player.total_spaces}
        """

        self.stats_label.config(text=text)
