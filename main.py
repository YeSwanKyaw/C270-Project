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

# "default" means that each page uses its original color.
BACKGROUND_COLOR = "default"

window.configure(bg="#808080")


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
    settings.run(window, show_menu, BACKGROUND_COLOR, set_background_color)


def set_background_color(color):
    # Save the chosen color so other screens can reuse it.
    global BACKGROUND_COLOR
    BACKGROUND_COLOR = color


def show_menu(error_message=""):
    clear_window()

    # The main menu's original background is grey.
    menu_color = "#808080" if BACKGROUND_COLOR == "default" else BACKGROUND_COLOR
    window.configure(bg=menu_color)

    # Keep the title readable on light background colors.
    title_color = "black" if menu_color == "#B8B8B8" else "white"

    title_label = tk.Label(
        window,
        text="ANSWER AND CONQUER",
        font=("Arial", 34, "bold"),
        fg=title_color,
        bg=menu_color
    )
    title_label.pack(pady=(70, 50))

    if error_message:
        error_label = tk.Label(
            window,
            text=error_message,
            font=("Arial", 15, "bold"),
            fg="red",
            bg=menu_color
        )
        error_label.pack(pady=(0, 10))

    button_details = [
        ("Play", play_game, "#F39C12", "#F5B041"),
        ("VS BOT", open_gamemode, "#7CB342", "#9CCC65"),
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

def close_app():
    # Close any sockets before exiting.
    game.close_connections()
    window.destroy()


window.protocol("WM_DELETE_WINDOW", close_app)

show_menu()
window.mainloop()
