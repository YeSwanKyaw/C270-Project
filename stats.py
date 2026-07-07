import tkinter as tk


# This is the place to view and keep track of statistics.
def run(window, show_menu):
    for widget in window.winfo_children():
        widget.destroy()

    window.configure(bg="#3498DB")

    title_label = tk.Label(
        window,
        text="Statistics",
        font=("Arial", 30, "bold"),
        bg="#3498DB",
        fg="white"
    )
    title_label.pack(pady=40)

    message_label = tk.Label(
        window,
        text="Put the statistics content in stats.py",
        font=("Arial", 16),
        bg="#3498DB",
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
