import tkinter as tk

from login_screen import LoginScreen
from main_menu import MainMenu
from settings import SettingsScreen
from game import MultiplayerScreen
import game
from gamemodes import GamemodeSelect
from main_gui import GameBoard
from player_stats import PlayerStats, StatsScreen


class AppController(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Answer and Conquer")
        self.geometry("1000x700")
        self.resizable(False, False)
        self.configure(bg="#808080")

        # "default" means that each page uses its original color.
        self.background_color = "default"
        self.player_stats = PlayerStats("Player 1")
        self.active_match = None

        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        for ScreenClass in (
            LoginScreen,
            MainMenu,
            SettingsScreen,
            MultiplayerScreen,
            GamemodeSelect,
            GameBoard,
            StatsScreen,
        ):
            frame = ScreenClass(parent=container, controller=self)
            self.frames[ScreenClass.__name__] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.protocol("WM_DELETE_WINDOW", self.close_app)
        self.show_frame("LoginScreen")

    def show_frame(self, frame_name, **kwargs):
        frame = self.frames[frame_name]
        if hasattr(frame, "on_show"):
            frame.on_show(**kwargs)
        frame.tkraise()

    def set_background_color(self, color):
        # Save the chosen color so other screens can reuse it.
        self.background_color = color

    def close_app(self):
        # Close any sockets before exiting.
        game.close_connections()
        self.destroy()


if __name__ == "__main__":
    app = AppController()
    app.mainloop()
