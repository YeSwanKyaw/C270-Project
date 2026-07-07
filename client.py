import socket
import threading

from network_utils import receive_json, send_json


PORT = 5000
client_socket = None
client_running = False


def connect_to_host(host_ip, on_status, on_message):
    """Connect without blocking Tkinter's main thread."""
    global client_running

    disconnect()
    client_running = True

    connect_thread = threading.Thread(
        target=_connect,
        args=(host_ip, on_status, on_message),
        daemon=True
    )
    connect_thread.start()


def _connect(host_ip, on_status, on_message):
    global client_socket, client_running

    connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    connection.settimeout(5)

    try:
        connection.connect((host_ip, PORT))
        connection.settimeout(None)

        if not client_running:
            connection.close()
            return

        client_socket = connection
        on_status("Connection successful", True)
        _receive_messages(on_status, on_message)
    except OSError as error:
        connection.close()

        if client_running:
            client_running = False
            on_status("Connection failed: " + str(error), False)


def _receive_messages(on_status, on_message):
    global client_running

    connection_file = client_socket.makefile("r", encoding="utf-8")

    try:
        while client_running:
            data = receive_json(connection_file)

            if data is None or data.get("type") == "disconnect":
                break

            # The first message confirms the host accepted Player 2.
            if data.get("type") != "connected":
                on_message(data)
    except (OSError, ValueError):
        pass
    finally:
        connection_file.close()

        if client_running:
            client_running = False
            _close_socket()
            on_status("Host disconnected", False)


def send_message(message):
    """Send a test message from Player 2."""
    if client_socket is None:
        return False

    try:
        send_json(
            client_socket,
            {"type": "test_message", "sender": "Player 2", "message": message}
        )
        return True
    except OSError:
        return False


def _close_socket():
    global client_socket

    if client_socket is not None:
        try:
            client_socket.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        client_socket.close()
        client_socket = None


def disconnect():
    """Disconnect from the host."""
    global client_running

    was_running = client_running
    client_running = False

    if was_running and client_socket is not None:
        try:
            send_json(client_socket, {"type": "disconnect"})
        except OSError:
            pass

    _close_socket()
