import socket
import threading

# GLOBAL VARIABLES 
HOST = '127.0.0.1'  # Standard loopback IP address (localhost)
PORT = 5000  # Port to listen on (non-privileged ports are > 1023)
FORMAT = 'utf-8'  # Define the encoding format of messages from client-server
ADDR = (HOST, PORT)  # Creating a tuple of IP+PORT

def start_server():
    # Step 1: Bind and start listening
    server_socket.bind(ADDR)
    print(f"[LISTENING] Server is listening on {HOST}:{PORT}")
    server_socket.listen()
    
    active_connections = 0  # Counter for active clients/games
    clients = []  # List to store connected clients
    
    # Step 2: Accept clients dynamically
    while True:
        connection, address = server_socket.accept()
        print(f"[NEW CONNECTION] {address} connected.")
        
        # Add client to active list
        clients.append(connection)
        active_connections += 1
        print(f"[ACTIVE CONNECTIONS] {active_connections}")
        
        # Step 3: Handle client in a new thread
        thread = threading.Thread(target=handle_client, args=(connection, address,active_connections))
        thread.start()

def handle_client(connection, addr, active_connections):
    print(f"[HANDLING CLIENT] {addr}")
    connected = True
    game_state = None  # Initialize game_state as None until 'start' is received

    try:
        while connected:
            # Step 1: Receive a move or command from the client
            msg = connection.recv(1024).decode(FORMAT)

            if not msg:
                print(f"[DISCONNECT] Empty message received. Closing connection to {addr}")
                break
            
            print(f"[{addr}] {msg}")

            # Step 2: Process the client's command
            if msg.lower() == 'quit':
                print(f"[DISCONNECT] {addr} disconnected.")
                connected = False
                active_connections -=1
                break

            if msg.lower() == 'start':
                print(f"[START] Client {addr} is starting the game...")
                
                if active_connections > 2:
                    # Initialize the game state dynamically based on active connections
                    board_size = (active_connections + 1) ** 2
                    game_state = [["" for _ in range(board_size)] for _ in range(board_size)]
                    print(f"[GAME STATE INITIALIZED] Board size: {board_size}x{board_size}")

                else:
                    # Initialize the game state dynamically based on active connections
                    board_size = 3
                    game_state = [["" for _ in range(board_size)] for _ in range(board_size)]
                    print(f"[GAME STATE INITIALIZED] Board size: {board_size}x{board_size}")
             
                # Acknowledge the start to the client
                connection.send(f"Game started with a {board_size}x{board_size} board.".encode(FORMAT))
                continue  # Continue to the next iteration to wait for moves
            
            # Process moves only if the game has started
            if game_state:
                # Here we can add logic to process moves (e.g., update the game state)
                response = f"Server received your move: {msg}"  # Placeholder response
                connection.send(response.encode(FORMAT))
            else:
                connection.send("Game has not started yet. Send 'start' to begin.".encode(FORMAT))
        
    except ConnectionResetError:
        print(f"[ERROR] Connection with {addr} reset unexpectedly.")
    finally:
        # Step 3: Clean up the connection
        connection.close()
        print(f"[CONNECTION CLOSED] {addr}")


def broadcast_update(clients, game_state, next_turn, status, winner=None):
    """
    Sends the updated game state to all players in the game.

    Args:
        clients (list): List of connected client sockets.
        game_state (list of list): The current game board.
        next_turn (str): The marker ("X", "O", etc.) of the next player.
        status (str): The current status of the game ("ongoing", "win", "draw").
        winner (str or None): The winning player, if any.
    """
    # Prepare the game data dictionary
    game_data = {
        "board": game_state,
        "next_turn": next_turn,
        "status": status,
        "winner": winner,
    }

    # Convert the game data to a string for transmission
    update_message = str(game_data)

    # Send the game data to all connected clients
    for client in clients:
        try:
            client.send(update_message.encode(FORMAT))
            print(f"[BROADCAST] Sent game update to client: {client}")
        except Exception as e:
            print(f"[ERROR] Failed to send game update to client: {e}")

def update_game_data(game_state, move, current_player, players):
    """
    Updates the game state based on the player's move.

    Args:
        game_state (list of list): The current game board.
        move (tuple): The player's move as (row, col).
        current_player (str): The marker for the current player ("X", "O", etc.).
        players (list): List of player markers (e.g., ["X", "O", "Δ"]).

    Returns:
        dict: Updated game data including the board, next turn, status, and winner.
    """
    row, col = move
    game_state[row][col] = current_player  # Update the board with the current player's marker

    # Check the game status
    status, winner = check_winner(game_state, players)

    # Determine the next turn
    next_turn_index = (players.index(current_player) + 1) % len(players)
    next_turn = players[next_turn_index]

    # Prepare the game data
    game_data = {
        "board": game_state,
        "next_turn": next_turn,
        "status": status,
        "winner": winner,
    }

    return game_data

# Main
if __name__ == '__main__':
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Opening Server socket
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Allow address reuse
    print("[STARTING] server is starting...")
    start_server()