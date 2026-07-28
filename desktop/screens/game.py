import tkinter as tk

from desktop.network import client, host


def close_connections():
    """Close either network role if it is running."""
    host.stop_server()
    client.disconnect()


# This screen connects two players before the full game starts.
class MultiplayerScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#F39C12")
        self.controller = controller

        self.screen_active = False
        self.current_role = None

        title_label = tk.Label(
            self,
            text="Multiplayer",
            font=("Arial", 30, "bold"),
            bg="#F39C12",
            fg="white"
        )
        title_label.pack(pady=(25, 15))

        self.role_frame = tk.Frame(self, bg="#F39C12")
        self.role_frame.pack(pady=5)

        self.details_frame = tk.Frame(self, bg="#F39C12")
        self.details_frame.pack(pady=10)

        self.status_label = tk.Label(
            self,
            text="Choose Host Game or Join Game",
            font=("Arial", 14, "bold"),
            bg="#F39C12",
            fg="white"
        )
        self.status_label.pack(pady=8)

        self.messages_box = tk.Text(self, width=58, height=8, state="disabled")
        self.messages_box.pack(pady=8)

        message_frame = tk.Frame(self, bg="#F39C12")
        message_frame.pack(pady=5)

        self.message_entry = tk.Entry(message_frame, font=("Arial", 13), width=34)
        self.message_entry.pack(side="left", padx=5)
        self.message_entry.bind("<Return>", lambda event: self.send_test_message())

        self.send_button = tk.Button(
            message_frame,
            text="Send Test Message",
            command=self.send_test_message,
            font=("Arial", 12, "bold"),
            state="disabled"
        )
        self.send_button.pack(side="left", padx=5)

        host_button = tk.Button(
            self.role_frame,
            text="Host Game",
            command=self.host_game,
            font=("Arial", 16, "bold"),
            width=12
        )
        host_button.pack(side="left", padx=10)

        join_button = tk.Button(
            self.role_frame,
            text="Join Game",
            command=self.join_game,
            font=("Arial", 16, "bold"),
            width=12
        )
        join_button.pack(side="left", padx=10)

        back_button = tk.Button(
            self,
            text="Back",
            command=self.go_back,
            font=("Arial", 14, "bold"),
            width=10
        )
        back_button.pack(pady=10)

    def on_show(self):
        close_connections()
        self.screen_active = True
        self.current_role = None
        self.clear_details()
        self.update_status("Choose Host Game or Join Game")

        self.messages_box.configure(state="normal")
        self.messages_box.delete("1.0", "end")
        self.messages_box.configure(state="disabled")

    def add_message(self, text):
        self.messages_box.configure(state="normal")
        self.messages_box.insert("end", text + "\n")
        self.messages_box.see("end")
        self.messages_box.configure(state="disabled")

    def update_status(self, text, connected=False):
        self.status_label.configure(text=text, fg="green" if connected else "red")
        self.send_button.configure(state="normal" if connected else "disabled")

    def safely_update_status(self, text, connected=False):
        # Network threads schedule all Tkinter changes on the main thread.
        def update_screen():
            if not self.screen_active:
                return
            self.update_status(text, connected)
            if connected:
                self.screen_active = False
                self.controller.show_frame("MultiGame", role=self.current_role)

        self.controller.after(0, update_screen)

    def safely_show_message(self, data):
        def show_message():
            if self.screen_active and data.get("type") == "test_message":
                sender = data.get("sender", "Other player")
                self.add_message(sender + ": " + data.get("message", ""))
            else:
                self.controller.frames["MultiGame"].handle_network_message(data)

        self.controller.after(0, show_message)

    def clear_details(self):
        for widget in self.details_frame.winfo_children():
            widget.destroy()

    def host_game(self):
        close_connections()
        self.clear_details()
        self.current_role = "host"

        success, result = host.start_server(self.safely_update_status, self.safely_show_message)

        if not success:
            self.update_status("Could not host game: " + result)
            return

        ip_label = tk.Label(
            self.details_frame,
            text=f"{self.controller.player_stats.name} is Player 1\nHost IP: {result}",
            font=("Arial", 16, "bold"),
            bg="#F39C12",
            fg="white"
        )
        ip_label.pack()
        self.update_status("Waiting for Player 2...")
        self.controller.apply_theme(self)

    def connect_to_host(self, ip_entry):
        host_ip = ip_entry.get().strip()

        if not host_ip:
            self.update_status("Enter the host IP address")
            return

        self.current_role = "client"
        self.update_status("Connecting...")
        client.connect_to_host(host_ip, self.safely_update_status, self.safely_show_message)

    def join_game(self):
        close_connections()
        self.clear_details()
        self.current_role = "client"

        ip_entry = tk.Entry(self.details_frame, font=("Arial", 14), width=20)
        ip_entry.pack(side="left", padx=5)

        connect_button = tk.Button(
            self.details_frame,
            text="Connect",
            command=lambda: self.connect_to_host(ip_entry),
            font=("Arial", 13, "bold")
        )
        connect_button.pack(side="left", padx=5)
        self.update_status("Enter the host IP address")
        ip_entry.focus_set()
        self.controller.apply_theme(self)

    def send_test_message(self):
        message = self.message_entry.get().strip()

        if not message:
            return

        if self.current_role == "host":
            sent = host.send_message(message)
        else:
            sent = client.send_message(message)

        if sent:
            self.add_message("You: " + message)
            self.message_entry.delete(0, "end")
        else:
            self.update_status("Message could not be sent")

    def go_back(self):
        self.screen_active = False
        close_connections()
        self.controller.show_frame("MainMenu")
