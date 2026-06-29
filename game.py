import tkinter as tk


# This is the place where the game is made.
def run(window, show_menu):
    for widget in window.winfo_children():
        widget.destroy()

    window.configure(bg="#F39C12")

    title_label = tk.Label(
        window,
        text="Game",
        font=("Arial", 30, "bold"),
        bg="#F39C12",
        fg="white"
    )
    title_label.pack(pady=40)

    message_label = tk.Label(
        window,
        text="Put the game content in game.py",
        font=("Arial", 16),
        bg="#F39C12",
        fg="white"
    )
    message_label.pack(pady=20)

    back_button = tk.Button(
        window,
        text="Back",
        command=show_menu,
        font=("Arial", 16, "bold"),
        width=12
    )
    back_button.pack(pady=30)
