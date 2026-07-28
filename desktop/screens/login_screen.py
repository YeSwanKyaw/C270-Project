import tkinter as tk


class LoginScreen(tk.Frame):
    """Placeholder login screen - no real authentication yet.
    Ye Swan: replace verify_login() with real auth logic."""

    def __init__(self, parent, controller):
        super().__init__(parent, bg="#808080")
        self.controller = controller

        title_label = tk.Label(
            self,
            text="ANSWER AND CONQUER",
            font=("Arial", 30, "bold"),
            bg="#808080",
            fg="white"
        )
        title_label.pack(pady=(80, 40))

        tk.Label(self, text="Username", font=("Arial", 14), bg="#808080", fg="white").pack()
        self.username_entry = tk.Entry(self, font=("Arial", 14))
        self.username_entry.pack(pady=(0, 20))
        self.username_entry.bind("<Return>", lambda event: self.verify_login())

        login_button = tk.Button(
            self,
            text="Log In",
            command=self.verify_login,
            font=("Arial", 16, "bold"),
            width=14,
            bg="#F39C12",
            fg="white"
        )
        login_button.pack(pady=10)

        self.error_label = tk.Label(self, text="", font=("Arial", 12, "bold"), fg="red", bg="#808080")
        self.error_label.pack(pady=5)

    def on_show(self):
        self.error_label.config(text="")
        self.username_entry.delete(0, "end")
        self.username_entry.focus_set()

    def verify_login(self):
        username = self.username_entry.get().strip()

        if not username:
            self.error_label.config(text="Enter a username to continue")
            return

        self.controller.player_stats.name = username
        self.controller.show_frame("MainMenu")
