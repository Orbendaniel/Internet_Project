import socket
HOST = '127.0.0.1'
PORT = 5000
FORMAT = 'utf-8'


def connect_to_server(host, port):
    """
    Establishes a connection to the server.

    Args:
        host (str): The server's IP address.
        port (int): The server's port number.

    Returns:
        socket.socket: The connected client socket.
    """
    try:
        # Step 1: Create a socket
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print(f"[CONNECTING] Attempting to connect to {host}:{port}...")

        # Step 2: Connect to the server
        client_socket.connect((host, port))
        print(f"[CONNECTED] Successfully connected to {host}:{port}.")
        return client_socket

    except ConnectionRefusedError:
        print("[ERROR] Connection refused by the server. Ensure the server is running.")
    except Exception as e:
        print(f"[ERROR] An unexpected error occurred: {e}")

    return None

def send_move(client_socket, move):
    """
    Sends the player's move to the server.

    Args:
        client_socket (socket.socket): The socket object connected to the server.
        move (str): The player's move (e.g., "1,2" or "quit").
    """
    try:
        # Step 1: Encode and send the move
        client_socket.send(move.encode(FORMAT))
        print(f"[SENT] Move sent to server: {move}")
    except BrokenPipeError:
        print("[ERROR] Unable to send move. Connection to the server is broken.")
    except Exception as e:
        print(f"[ERROR] An unexpected error occurred while sending move: {e}")

if __name__ == "__main__":
    connect_to_server(HOST,PORT)
