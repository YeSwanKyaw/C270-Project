import tkinter as tk

import client
import host


def close_connections():
    """Close either network role if it is running."""
    host.stop_server()
    client.disconnect()


# This screen connects two players before the full game starts.
def run(window, show_menu):
    close_connections()

    for widget in window.winfo_children():
        widget.destroy()

    background = "#F39C12"
    window.configure(bg=background)
    screen_active = {"value": True}
    current_role = {"value": None}

    title_label = tk.Label(
        window,
        text="Multiplayer",
        font=("Arial", 30, "bold"),
        bg=background,
        fg="white"
    )
    title_label.pack(pady=(25, 15))

    role_frame = tk.Frame(window, bg=background)
    role_frame.pack(pady=5)

    details_frame = tk.Frame(window, bg=background)
    details_frame.pack(pady=10)

    status_label = tk.Label(
        window,
        text="Choose Host Game or Join Game",
        font=("Arial", 14, "bold"),
        bg=background,
        fg="white"
    )
    status_label.pack(pady=8)

    messages_box = tk.Text(window, width=58, height=8, state="disabled")
    messages_box.pack(pady=8)

    message_frame = tk.Frame(window, bg=background)
    message_frame.pack(pady=5)

    message_entry = tk.Entry(message_frame, font=("Arial", 13), width=34)
    message_entry.pack(side="left", padx=5)

    send_button = tk.Button(
        message_frame,
        text="Send Test Message",
        font=("Arial", 12, "bold"),
        state="disabled"
    )
    send_button.pack(side="left", padx=5)

    def add_message(text):
        messages_box.configure(state="normal")
        messages_box.insert("end", text + "\n")
        messages_box.see("end")
        messages_box.configure(state="disabled")

    def update_status(text, connected=False):
        status_label.configure(text=text, fg="green" if connected else "red")
        send_button.configure(state="normal" if connected else "disabled")

    def safely_update_status(text, connected=False):
        # Network threads schedule all Tkinter changes on the main thread.
        window.after(
            0,
            lambda: update_status(text, connected) if screen_active["value"] else None
        )

    def safely_show_message(data):
        def show_message():
            if not screen_active["value"]:
                return

            if data.get("type") == "test_message":
                sender = data.get("sender", "Other player")
                add_message(sender + ": " + data.get("message", ""))

        window.after(0, show_message)

    def clear_details():
        for widget in details_frame.winfo_children():
            widget.destroy()

    def host_game():
        close_connections()
        clear_details()
        current_role["value"] = "host"

        success, result = host.start_server(safely_update_status, safely_show_message)

        if not success:
            update_status("Could not host game: " + result)
            return

        ip_label = tk.Label(
            details_frame,
            text="You are Player 1\nHost IP: " + result,
            font=("Arial", 16, "bold"),
            bg=background,
            fg="white"
        )
        ip_label.pack()
        update_status("Waiting for Player 2...")

    def connect_to_host(ip_entry):
        host_ip = ip_entry.get().strip()

        if not host_ip:
            update_status("Enter the host IP address")
            return

        current_role["value"] = "client"
        update_status("Connecting...")
        client.connect_to_host(host_ip, safely_update_status, safely_show_message)

    def join_game():
        close_connections()
        clear_details()
        current_role["value"] = "client"

        ip_entry = tk.Entry(details_frame, font=("Arial", 14), width=20)
        ip_entry.pack(side="left", padx=5)

        connect_button = tk.Button(
            details_frame,
            text="Connect",
            command=lambda: connect_to_host(ip_entry),
            font=("Arial", 13, "bold")
        )
        connect_button.pack(side="left", padx=5)
        update_status("Enter the host IP address")
        ip_entry.focus_set()

    def send_test_message():
        message = message_entry.get().strip()

        if not message:
            return

        if current_role["value"] == "host":
            sent = host.send_message(message)
        else:
            sent = client.send_message(message)

        if sent:
            add_message("You: " + message)
            message_entry.delete(0, "end")
        else:
            update_status("Message could not be sent")

    def go_back():
        screen_active["value"] = False
        close_connections()
        show_menu()

    host_button = tk.Button(
        role_frame,
        text="Host Game",
        command=host_game,
        font=("Arial", 16, "bold"),
        width=12
    )
    host_button.pack(side="left", padx=10)

    join_button = tk.Button(
        role_frame,
        text="Join Game",
        command=join_game,
        font=("Arial", 16, "bold"),
        width=12
    )
    join_button.pack(side="left", padx=10)

    send_button.configure(command=send_test_message)
    message_entry.bind("<Return>", lambda event: send_test_message())

    back_button = tk.Button(
        window,
        text="Back",
        command=go_back,
        font=("Arial", 14, "bold"),
        width=10
    )
    back_button.pack(pady=10)
