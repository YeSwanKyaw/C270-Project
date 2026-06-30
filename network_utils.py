import json


def send_json(connection, data):
    """Send one JSON message followed by a newline."""
    message = json.dumps(data) + "\n"
    connection.sendall(message.encode("utf-8"))


def receive_json(connection_file):
    """Read one complete newline-separated JSON message."""
    line = connection_file.readline()

    if not line:
        return None

    return json.loads(line)
