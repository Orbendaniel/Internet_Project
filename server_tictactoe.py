import socket
import threading
import time

# GLOBAL VARIABLES 
HOST = '127.0.0.1'  # Standard loopback IP address (localhost)
PORT = 5000  # Port to listen on (non-privileged ports are > 1023)
FORMAT = 'utf-8'  # Define the encoding format of messages from client-server
ADDR = (HOST, PORT)  # Creating a tuple of IP+PORT
PLAYER_MARKERS = ["X", "O", "Δ", "☆", "♠", "♣", "♥", "♦", "♪", "♫","⚡", "☀", "⚔", "⚖", "⚙", "⚛", "⚜", "⚠", "⚒"] # Define player markers 
CLIENT_MARKERS = {}  # Maps client connections to their assigned markers
game_state = None  # Global game state
game_state_lock = threading.Lock()  # Global lock for synchronizing game_state access
lobbies = {}  # Dictionary to manage multiple game lobbies
lobby_counter = 1  # Counter for naming new lobbies

def start_server():
    # Step 1: Bind and start listening
    server_socket.bind(ADDR)
    print(f"[LISTENING] Server is listening on {HOST}:{PORT}")
    server_socket.listen()

    active_connections = 0  # Counter for active connections
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
        thread = threading.Thread(target=handle_client, args=(connection, address,active_connections,clients))
        thread.start()

def handle_client(connection, addr, active_connections,clients):
    global game_state  # Access the global game state
    global lobbies, lobby_counter # Access the global lobby dictionary and lobby lobby counter  
    print(f"[HANDLING CLIENT] {addr}")
    connected = True

    # Assign a marker to the new client
    if connection not in CLIENT_MARKERS:
        available_markers = [marker for marker in PLAYER_MARKERS if marker not in CLIENT_MARKERS.values()]
        if available_markers:
            marker = available_markers[0]
            CLIENT_MARKERS[connection] = marker  # Assign marker

        else:
            print(f"[ERROR] No markers available for client {addr}")
            connection.send("[SERVER] No markers available, disconnecting.".encode(FORMAT))
            connection.close()
            return  # Close connection if no markers are available
    else:
            marker = CLIENT_MARKERS[connection]  # Retrieve existing marker

    # Send the assigned marker
    connection.send(marker.encode(FORMAT))  # Send the assigned marker
    print(f"[ASSIGN] Assigned marker '{CLIENT_MARKERS[connection]}' to client {addr}")

    # Pre-Lobby Logic: Ask the client to choose or create a lobby
    try:
        while True:  # Pre-lobby loop
            # Receive the client's choice
            choice = connection.recv(1024).decode(FORMAT).strip()
            if choice == "1":
                # Create a new lobby
                lobby_name = f"Lobby{lobby_counter}"
                lobbies[lobby_name] = {
                    "clients": [connection],
                    "game_state": None,
                    "players": []
                }
                lobby_counter += 1
                connection.send(f"[INFO] Created and joined {lobby_name}\n".encode(FORMAT))
                print(f"[LOBBY CREATED] {addr} created {lobby_name}.")
                break  # Exit pre-lobby loop

            elif choice == "2":
                # Show available lobbies
                if not lobbies:
                    connection.send("[INFO] No available lobbies. Please create one first.\n".encode(FORMAT))
                else:
                    lobby_list = "Available lobbies:\n" + "\n".join(
                        [f"{name} ({len(lobby['clients'])} players)" + "\n" for name, lobby in lobbies.items()]
                    )
                    connection.send((lobby_list).encode(FORMAT))

                    # Receive and process the client's lobby choice
                    lobby_name = connection.recv(1024).decode(FORMAT).strip()
                    if lobby_name in lobbies:
                        lobbies[lobby_name]["clients"].append(connection)
                        connection.send(f"[INFO] Joined {lobby_name}\n".encode(FORMAT))
                        print(f"[LOBBY JOINED] {addr} joined {lobby_name}.")
                        break  # Exit pre-lobby loop
                    else:
                        connection.send("[ERROR] Lobby not found. Try again.\n".encode(FORMAT))

            else:
                connection.send("[ERROR] Invalid choice. Please enter 1 or 2.\n".encode(FORMAT))

    except Exception as e:
        print(f"[ERROR] An error occurred while handling client pre-lobby: {e}")
        connection.close()
        return  # Exit the function if an error occurs
    
    # Main Game Loop 
    try:
        while connected:
            # Step 1: Receive a move or command from the client
            msg = connection.recv(1024).decode(FORMAT)
            print(f"[DEBUG] Received message from client: {msg}")
            if not msg:
                print(f"[DISCONNECT] Empty message received. Closing connection to {addr}")
                break
            
            # Handle other messages (e.g., chat messages)
            if not ',' and 'quit' in msg: 
                print(f"[CHAT] {addr} says: {msg}")

            # Step 2: Process the client's command
            if msg.lower() == 'quit':
                print(f"[DISCONNECT] {addr} disconnected.")
                connection.send("quit".encode(FORMAT)) #sends a quit signal to the client
                connected = False
                active_connections -=1
                CLIENT_MARKERS.pop(connection, None)  # Remove the client's marker

                # Remove client from lobby
                lobby_name = None
                for lobby, details in lobbies.items():
                    if connection in details["clients"]:
                        lobby_name = lobby

                if lobby_name:
                    lobbies[lobby_name]["clients"].remove(connection)
                    if not lobbies[lobby_name]["clients"]:  # If the lobby is empty, remove it
                        del lobbies[lobby_name]
                        print(f"[LOBBY DELETED] {lobby_name} deleted as it became empty.")

                break

            if msg.lower() == 'start':
                print(f"[START] Client {addr} is starting the game...")
                    # Get the lobby name for this client
                lobby_name = None
                for lobby, details in lobbies.items():
                    if connection in details["clients"]:
                        lobby_name = lobby

                # Get the lobby details
                lobby_details = lobbies[lobby_name]
                clients_in_lobby = lobby_details["clients"]    

                # Prepare the initial game state for the lobby
                num_players = len(clients_in_lobby)
                board_size = 3 if num_players <= 2 else (num_players + 1) ** 2
                lobby_details["game_state"] = [["" for _ in range(board_size)] for _ in range(board_size)]

                # Notify all clients in the lobby that the game has started
                for client in clients_in_lobby:
                    try:
                        client.send("game started".encode(FORMAT))
                        print(f"[BROADCAST] Sent 'game started' message to client: {client}")
                    except Exception as e:
                        print(f"[ERROR] Failed to send 'game started' message to client: {e}")
                
                # Prepare the players list
                players = [CLIENT_MARKERS[client] for client in clients_in_lobby]

                # Call update_game_data to set the initial state
                game_data = update_game_data(game_state=lobby_details["game_state"], move=None, current_player=players[0], players=players)
                
                # Broadcast the initial game state to the lobby
                broadcast_update(lobby_name=lobby_name, game_state=game_data["board"], next_turn= game_data["next_turn"],status= "ongoing", winner=None)
                continue  # Continue to the next iteration to wait for moves
            
            # Handle move commands (e.g., "1,2")
            elif ',' in msg:
                try:
                    # Step 1: Determine the lobby
                    lobby_name = None
                    for lobby, details in lobbies.items():
                        if connection in details["clients"]:
                            lobby_name = lobby

                    lobby_details = lobbies[lobby_name]
                    game_state = lobby_details["game_state"]
                    players = [CLIENT_MARKERS[client] for client in lobby_details["clients"]]

                    # Step 2: Parse and validate the move
                    move = tuple(map(int, msg.split(',')))  # Parse move as (row, col)
                    current_player = CLIENT_MARKERS[connection]
                    print(f"[DEBUG] Parsed move: {move}")

                    with game_state_lock:
                        # Validate the move
                        is_valid, validation_msg = validate_move(game_state, move)

                    # Step 3: Handle move validity
                        if not is_valid:
                            print(f"Player {current_player} [ERROR] Invalid move: {validation_msg}. Skipping turn!")
                            move = None  # Clear move as the turn is skipped
                            print("[DEBUG] validate_move COMPLETE")
                            game_data = update_game_data(game_state, move, current_player, players)
                            print("[DEBUG] update_game_data COMPLETE")
                            game_state = game_data["board"]  # Update the board state
                            print(game_state)
                        else:
                            print("[DEBUG] validate_move COMPLETE")
                            # Update the game state with a valid move
                            game_data = update_game_data(game_state, move, current_player, players)
                            print("[DEBUG] update_game_data COMPLETE")
                            game_state = game_data["board"]  # Update the board state
                            print(game_state)

                        # Step 4: Update the game state
                        game_data = update_game_data(game_state, move, current_player, players)
                        lobby_details["game_state"] = game_data["board"]  # Update the lobby's game state

                    # Broadcast the updated game state
                    broadcast_update(lobby_name=lobby_name, game_state= game_data["board"],next_turn= game_data["next_turn"], status= game_data["status"], winner= game_data["winner"])
                    move = None #clear move for next turn

                except ValueError:
                    connection.send("[ERROR] Invalid move format. Use 'row,col'.".encode(FORMAT))
                    continue

                except Exception as e:
                    print(f"[ERROR] Unexpected error while processing move: {e}")
                    continue  # Ensure the game loop continues



    except ConnectionResetError:
        print(f"[ERROR] Connection with {addr} reset unexpectedly.")
    finally:
        # Step 3: Clean up the connection
        connection.close()
        print(f"[CONNECTION CLOSED] {addr}")

def broadcast_update(lobby_name, game_state, next_turn, status, winner=None):
    """
    Sends the updated game state to all players in the game.

    Args:
        lobby_name (str): The name of the lobby to broadcast updates to.
        game_state (list of list): The current game board.
        next_turn (str): The marker ("X", "O", etc.) of the next player.
        status (str): The current status of the game ("ongoing", "win", "draw").
        winner (str or None): The winning player, if any.
    """
    # Ensure the lobby exists
    if lobby_name not in lobbies:
        print(f"[ERROR] Lobby '{lobby_name}' does not exist.")
        return

    # Get the clients in the lobby
    clients = lobbies[lobby_name]["clients"]
    formatted_board = [[" " if cell == "" else cell for cell in row] for row in game_state]

    # Prepare the game data dictionary
    game_data = {
        "board": formatted_board,
        "next_turn": next_turn,
        "status": status,
        "winner": winner,
    }

    # Convert the game data to a string for transmission
    update_message = repr(game_data)
    print(f"[DEBUG] Sending game data to {lobby_name}: {update_message}")  # Debugging

    # Introduce a small delay to ensure clients have time to receive the broadcast
    time.sleep(0.1)  # Adjust the delay as necessary

    # Send the game data to all connected clients
    for client in clients:
        try:
            client.send(update_message.encode(FORMAT))
            print(f"[BROADCAST] Sent game update to client in {lobby_name}: {client}")
        except Exception as e:
            print(f"[ERROR] Failed to send game update to client in {lobby_name}: {e}")
            
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
    #when the game just starts
    if move is None and current_player==players[0]:
        next_turn = players[0]  # First player's turn at game start
        status, winner = "ongoing", None  # Default values at game start

    #when move is not valid skip turn 
    if move is None and current_player!=players[0]: 
        next_turn_index = (players.index(current_player) + 1) % len(players)
        next_turn = players[next_turn_index]   
        
        # Check the game status
        status, winner = check_winner(game_state, players)

    if move is not None:
        # Process the move
        row, col = move
        game_state[row][col] = current_player

        # Determine the next turn
        next_turn_index = (players.index(current_player) + 1) % len(players)
        next_turn = players[next_turn_index]

        # Check the game status
        status, winner = check_winner(game_state, players)

    # Prepare the game data
    game_data = {
        "board": game_state,
        "next_turn": next_turn, 
        "status": status, 
        "winner": winner,  
    }

    return game_data

def validate_move(game_state, move): 
    """
    Validates a move sent by a client.

    Args:
        game_state (list of list): The current game board.
        move (tuple): The player's move as (row, col).

    Returns:
        bool: True if the move is valid, False otherwise.
        str: An error message if the move is invalid.
    """
    row, col = move
    board_size = len(game_state)
    print(f"[DEBUG] Validating move: {move}")
    # Check if the move is within bounds
    if not (0 <= row < board_size and 0 <= col < board_size):
        return False, "Move is out of bounds."

    # Check if the cell is empty
    if game_state[row][col] != "":
        return False, "Cell is already occupied."

    return True, "Move is valid."

def check_winner(game_state, players):  
    """
    Checks the game board to determine if there's a winner or if the game is a draw.

    Args:
        game_state (list of list): The current game board.
        players (list): List of player markers (e.g., ["X", "O", "Δ"]).

    Returns:
        str: The status of the game ("win", "draw", "ongoing").
        str or None: The winning player, if any.
    """
    board_size = len(game_state)

    # Check rows for a winner
    for row in game_state:
        for i in range(board_size - 2):  # Stop 2 cells before the end
            if row[i] == row[i + 1] == row[i + 2] != "":  # Check for 3 consecutive cells
                return "win", row[i]

    # Check columns for a winner
    for col in range(board_size):
        for i in range(board_size - 2):  # Stop 2 cells before the end
            if game_state[i][col] == game_state[i + 1][col] == game_state[i + 2][col] != "":
                return "win", game_state[i][col]

    # Check diagonals for a winner
    for i in range(board_size - 2):  # Stop 2 cells before the end
        for j in range(board_size - 2):  # Stop 2 cells before the end
            # Check diagonal top-left to bottom-right
            if game_state[i][j] == game_state[i + 1][j + 1] == game_state[i + 2][j + 2] != "":
                return "win", game_state[i][j]
            # Check diagonal top-right to bottom-left
            if game_state[i][j + 2] == game_state[i + 1][j + 1] == game_state[i + 2][j] != "":
                return "win", game_state[i][j + 2]

    # Check for a draw (no empty cells)
    if all(cell != "" for row in game_state for cell in row):
        return "draw", None

    # If no winner or draw, the game is still ongoing
    return "ongoing", None

# Main
if __name__ == '__main__':
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Opening Server socket
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Allow address reuse
    print("[STARTING] server is starting...")
    start_server()