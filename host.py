import socket
import threading

from network_utils import receive_json, send_json


PORT = 5000
server_socket = None
client_socket = None
server_running = False


def get_local_ip():
    """Find the Wi-Fi/LAN address that Player 2 should enter."""
    test_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        # No data is sent; this only discovers the preferred local address.
        test_socket.connect(("8.8.8.8", 80))
        return test_socket.getsockname()[0]
    except OSError:
        try:
            return socket.gethostbyname(socket.gethostname())
        except OSError:
            return "127.0.0.1"
    finally:
        test_socket.close()


def start_server(on_status, on_message):
    """Start a 1v1 server and accept one player in a background thread."""
    global server_socket, server_running

    stop_server()

    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(("", PORT))
        server_socket.listen(1)
        server_running = True
    except OSError as error:
        stop_server()
        return False, str(error)

    accept_thread = threading.Thread(
        target=_accept_client,
        args=(on_status, on_message),
        daemon=True
    )
    accept_thread.start()
    return True, get_local_ip()


def _accept_client(on_status, on_message):
    global server_socket, client_socket, server_running

    listening_socket = server_socket

    try:
        connection, address = listening_socket.accept()

        if not server_running:
            connection.close()
            return

        client_socket = connection

        # Closing the listening socket prevents a second player from joining.
        listening_socket.close()
        server_socket = None

        send_json(client_socket, {"type": "connected", "player": "Player 2"})
        on_status("Connection successful", True)
        _receive_messages(on_status, on_message)
    except OSError as error:
        if server_running:
            server_running = False
            _close_socket("server_socket")
            _close_socket("client_socket")
            on_status("Host error: " + str(error), False)


def _receive_messages(on_status, on_message):
    global server_running

    connection_file = client_socket.makefile("r", encoding="utf-8")

    try:
        while server_running:
            data = receive_json(connection_file)

            if data is None or data.get("type") == "disconnect":
                break

            on_message(data)
    except (OSError, ValueError):
        pass
    finally:
        connection_file.close()

        if server_running:
            server_running = False
            _close_socket("client_socket")
            on_status("Player 2 disconnected", False)


def send_message(message):
    """Send a test message from Player 1."""
    if client_socket is None:
        return False

    try:
        send_json(
            client_socket,
            {"type": "test_message", "sender": "Player 1", "message": message}
        )
        return True
    except OSError:
        return False


def _close_socket(socket_name):
    global server_socket, client_socket

    connection = server_socket if socket_name == "server_socket" else client_socket

    if connection is not None:
        try:
            connection.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        connection.close()

    if socket_name == "server_socket":
        server_socket = None
    else:
        client_socket = None


def stop_server():
    """Stop hosting and close the connected player socket."""
    global server_running

    was_running = server_running
    server_running = False

    if was_running and client_socket is not None:
        try:
            send_json(client_socket, {"type": "disconnect"})
        except OSError:
            pass

    _close_socket("server_socket")
    _close_socket("client_socket")
