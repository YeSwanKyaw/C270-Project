import tkinter as tk


# This is the place where the different gamemodes are defined.
def run(window, show_menu):
    for widget in window.winfo_children():
        widget.destroy()

    window.configure(bg="#7CB342")

    title_label = tk.Label(
        window,
        text="Gamemodes",
        font=("Arial", 30, "bold"),
        bg="#7CB342",
        fg="white"
    )
    title_label.pack(pady=40)

    message_label = tk.Label(
        window,
        text="Put the gamemode content in gamemodes.py",
        font=("Arial", 16),
        bg="#7CB342",
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
