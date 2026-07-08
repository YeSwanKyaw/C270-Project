import tkinter as tk


class MainMenu(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self.title_label = tk.Label(self, font=("Arial", 34, "bold"))
        self.title_label.pack(pady=(70, 50))

        self.error_label = tk.Label(self, font=("Arial", 15, "bold"), fg="red")

        button_details = [
            ("Play", lambda: controller.show_frame("MultiplayerScreen"), "#F39C12", "#F5B041"),
            ("VS BOT", lambda: controller.show_frame("GamemodeSelect"), "#7CB342", "#9CCC65"),
            ("Statistics", lambda: controller.show_frame("StatsScreen"), "#3498DB", "#5DADE2"),
            ("Settings", lambda: controller.show_frame("SettingsScreen"), "#E74C3C", "#EC7063"),
        ]

        for text, command, color, active_color in button_details:
            button = tk.Button(
                self,
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

    def on_show(self, error_message=""):
        # The main menu's original background is grey.
        menu_color = "#808080" if self.controller.background_color == "default" else self.controller.background_color
        title_color = "black" if menu_color == "#B8B8B8" else "white"

        self.configure(bg=menu_color)
        self.title_label.configure(text="ANSWER AND CONQUER", bg=menu_color, fg=title_color)

        if error_message:
            self.error_label.configure(text=error_message, bg=menu_color)
            self.error_label.pack(pady=(0, 10), after=self.title_label)
        else:
            self.error_label.pack_forget()
