import tkinter as tk

from desktop.screens.login_screen import LoginScreen
from desktop.screens.main_menu import MainMenu
from desktop.screens.settings import SettingsScreen
from desktop.screens.game import MultiplayerScreen
from desktop.screens import game
from desktop.screens.gamemodes import GamemodeSelect
from desktop.screens.main_gui import GameBoard
from desktop.screens.multigame import MultiGame
from desktop.screens.player_stats import PlayerStats, StatsScreen
from desktop.screens.rules_lobby import RulesLobbyFrame


class AppController(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Answer and Conquer")
        self.geometry("1000x700")
        self.resizable(False, False)
        self.configure(bg="#808080")

        # "default" means that each page uses its original color.
        self.background_color = "default"
        # ==================== START OF TILE COLOR SETTINGS ====================
        self.player_tile_color = "#FF0000"
        self.opponent_tile_color = "#ADD8E6"
        # ===================== END OF TILE COLOR SETTINGS =====================
        # ==================== START OF TIMER SETTINGS ====================
        self.question_timer = 15
        # ===================== END OF TIMER SETTINGS =====================
        # ==================== START OF SKIP SETTINGS ====================
        self.cpu_skips = 3
        # ===================== END OF SKIP SETTINGS =====================
        # ==================== START OF GAME SETTINGS ====================
        self.cpu_chance_mode = "normal"
        # ===================== END OF GAME SETTINGS =====================
        self._original_widget_colors = {}
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
            RulesLobbyFrame,
            GameBoard,
            MultiGame,
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
        self.apply_theme(frame)
        frame.tkraise()

    def set_background_color(self, color):
        # Save the chosen color so other screens can reuse it.
        self.background_color = color
        for frame in self.frames.values():
            self.apply_theme(frame)

    # ==================== START OF TILE COLOR SETTINGS ====================
    def set_player_tile_color(self, color):
        if color == self.opponent_tile_color:
            return False
        self.player_tile_color = color
        self.refresh_game_boards()
        return True

    def set_opponent_tile_color(self, color):
        if color == self.player_tile_color:
            return False
        self.opponent_tile_color = color
        self.refresh_game_boards()
        return True

    def refresh_game_boards(self):
        for frame_name in ("GameBoard", "MultiGame"):
            frame = self.frames.get(frame_name)
            if frame is not None and hasattr(frame, "sync_board_and_ui"):
                frame.sync_board_and_ui()
            elif frame is not None and hasattr(frame, "sync_board"):
                frame.sync_board()
    # ===================== END OF TILE COLOR SETTINGS =====================

    # ==================== START OF TIMER SETTINGS ====================
    def set_question_timer(self, seconds):
        self.question_timer = int(float(seconds))
    # ===================== END OF TIMER SETTINGS =====================

    # ==================== START OF SKIP SETTINGS ====================
    def set_cpu_skips(self, skips):
        self.cpu_skips = int(float(skips))
    # ===================== END OF SKIP SETTINGS =====================

    # ==================== START OF GAME SETTINGS ====================
    def set_cpu_chance_mode(self, mode):
        if mode in ("safe", "normal", "chaos"):
            self.cpu_chance_mode = mode
    # ===================== END OF GAME SETTINGS =====================

    # ==================== START OF COLOR THEME CHANGES ====================
    def get_theme_palette(self):
        if self.background_color == "#505050":
            return ["#303030", "#606060", "#909090", "#C0C0C0", "#E0E0E0"]
        return None

    def apply_theme(self, root_widget):
        """Apply the selected grey palette without changing game logic."""
        palette = self.get_theme_palette()
        color_slots = {
            "#808080": 0,
            "#f39c12": 1, "#f5b041": 1,
            "#7cb342": 2, "#9ccc65": 2,
            "#3498db": 3, "#5dade2": 3,
            "#e74c3c": 4, "#ec7063": 4,
        }
        ownership_colors = {"#add8e6", "#f08080"}

        def recolor(widget):
            saved = self._original_widget_colors.setdefault(widget, {})
            updates = {}

            for option in ("background", "activebackground"):
                try:
                    saved.setdefault(option, widget.cget(option))
                except tk.TclError:
                    continue

                original = str(saved[option])
                original_lower = original.lower()
                if isinstance(widget, tk.Button) and widget.cget("text") in ("P1", "P2"):
                    continue
                if original_lower in ownership_colors:
                    continue

                if palette is None:
                    updates[option] = original
                elif original_lower in color_slots:
                    updates[option] = palette[color_slots[original_lower]]
                elif original in ("SystemButtonFace", "#d9d9d9"):
                    updates[option] = palette[1] if isinstance(widget, tk.Button) else palette[0]

            for option in ("foreground", "activeforeground"):
                try:
                    saved.setdefault(option, widget.cget(option))
                except tk.TclError:
                    continue
                # ==================== START OF MULTIPLAYER RANDOM MODE ====================
                if getattr(widget, "_preserve_theme_foreground", False):
                    continue
                # ===================== END OF MULTIPLAYER RANDOM MODE =====================
                if isinstance(widget, tk.Button) and widget.cget("text") in ("P1", "P2"):
                    continue
                original = str(saved[option])
                if palette is None:
                    updates[option] = original
                elif original.lower() in ("white", "#ffffff", "black", "#000000", "systembuttontext"):
                    light_greys = {"#c0c0c0", "#e0e0e0"}
                    target_background = str(updates.get("background", "")).lower()
                    if target_background:
                        updates[option] = "black" if target_background in light_greys else "white"
                    else:
                        updates[option] = original

            if updates:
                widget.configure(**updates)
            for child in widget.winfo_children():
                recolor(child)

        recolor(root_widget)
    # ===================== END OF COLOR THEME CHANGES =====================

    def close_app(self):
        # Close any sockets before exiting.
        game.close_connections()
        self.destroy()


if __name__ == "__main__":
    app = AppController()
    app.mainloop()
