import tkinter as tk

import game
import gamemodes
import settings
import stats


# -----------------------------
# WINDOW SETUP
# -----------------------------

window = tk.Tk()
window.title("Answer and Conquer")
window.geometry("1000x700")
window.resizable(False, False)

BACKGROUND_COLOR = "#808080"

window.configure(bg=BACKGROUND_COLOR)


# -----------------------------
# PAGE FUNCTIONS
# -----------------------------

def clear_window():
    for widget in window.winfo_children():
        widget.destroy()


def play_game():
    game.run(window, show_menu)


def open_gamemode():
    gamemodes.run(window, show_menu)


def open_statistics():
    stats.run(window, show_menu)


def open_settings():
    settings.run(window, show_menu)


def show_menu():
    clear_window()
    window.configure(bg=BACKGROUND_COLOR)

    title_label = tk.Label(
        window,
        text="ANSWER AND CONQUER",
        font=("Arial", 34, "bold"),
        fg="white",
        bg=BACKGROUND_COLOR
    )
    title_label.pack(pady=(70, 50))

    button_details = [
        ("Play", play_game, "#F39C12", "#F5B041"),
        ("Gamemodes", open_gamemode, "#7CB342", "#9CCC65"),
        ("Statistics", open_statistics, "#3498DB", "#5DADE2"),
        ("Settings", open_settings, "#E74C3C", "#EC7063")
    ]

    for text, command, color, active_color in button_details:
        button = tk.Button(
            window,
            text=text,
            command=command,
            font=("Arial", 20, "bold"),
            width=18,
            height=2,
            bg=color,
            fg="white",
            activebackground=active_color,
            activeforeground="white",
            relief="raised",
            bd=6,
            cursor="hand2"
        )
        button.pack(pady=10)


# -----------------------------
# START APPLICATION
# -----------------------------

show_menu()
window.mainloop()
