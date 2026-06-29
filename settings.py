import tkinter as tk


def run(window, show_menu):
    for widget in window.winfo_children():
        widget.destroy()

    window.configure(bg="#E74C3C")

    title_label = tk.Label(
        window,
        text="Settings",
        font=("Arial", 30, "bold"),
        bg="#E74C3C",
        fg="white"
    )
    title_label.pack(pady=40)

    message_label = tk.Label(
        window,
        text="Put the settings content in settings.py",
        font=("Arial", 16),
        bg="#E74C3C",
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
