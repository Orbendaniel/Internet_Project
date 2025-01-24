import socket
import threading
HOST = '127.0.0.1'  # Replace with the server's IP if needed
PORT = 5000  # Replace with the server's port if needed
FORMAT = 'utf-8'
game_active_event = threading.Event()  # Shared event for game state
in_lobby_event = threading.Event() # threading event for lobby state
listener_stop_event = threading.Event() # threading event for listen state

def listen_to_server(client_socket, player_marker):
    """
    Continuously listens for messages from the server.
    """
    while not listener_stop_event.is_set():
        try:
            response = receive_game_update(client_socket)
            if not response:
                print("[ERROR] Lost connection to the server.")
                break

            # Check for "game started" message
            if "game started" in response.lower():
                print("[INFO] Game has started! Entering game loop...")
                game_active_event.set()  # Signal that the game is active
                play_game(client_socket,player_marker)  # Automatically enter the game loop
                print("[GAME ENDED] Returning to communication loop.")
                game_active_event.clear()  # Reset game state after loop ends

            #Handle quit messages      
            if response.lower() == "quit": 
                break

        except Exception:
            break

def connect_to_server(host, port):
    """
    Establishes a connection to the server and allows continuous communication.
    """

    # Step 1: Create a socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Step 2: Connect to the server
    client_socket.connect((host, port))
    print(f"[CONNECTED] Successfully connected to {host}:{port}")
    
    # Step 3: Receive the assigned marker from the server
    try:
        player_marker = client_socket.recv(1024).decode(FORMAT)
        print(f"[INFO] You are assigned the marker: {player_marker}")
    except Exception as e:
        print(f"[ERROR] Failed to receive marker: {e}")
        client_socket.close()
        return

     # Step 4: Handle the pre-game lobby logic
    try:
        in_lobby_event.set()  # Set the lobby state
        while in_lobby_event.is_set():
            print("\n[INFO] Welcome! Choose an option:")
            print("1. Start a new game lobby")
            print("2. Join an existing game lobby")
            print("3. Quit")

            # Get client input
            choice = input("Enter your choice (1,2,3): ").strip()

            if choice == "1":
                client_socket.send(choice.encode(FORMAT))
                print("[WAIT] Creating a new lobby...")
                response = client_socket.recv(1024).decode(FORMAT)
                print(f"[SERVER RESPONSE] {response}")
                in_lobby_event.clear()  # Exit the lobby when a game is created

            elif choice == "2":
                client_socket.send(choice.encode(FORMAT))
                response = client_socket.recv(8192).decode(FORMAT)  # Receive available lobbies
                print(f"[SERVER RESPONSE] {response}")
                if "No active lobbies" not in response:
                    lobby_choice = input("Enter the lobby name you want to join: ").strip()
                    client_socket.send(lobby_choice.encode(FORMAT))
                    response = client_socket.recv(1024).decode(FORMAT)
                    print(f"[SERVER RESPONSE] {response}")
                    if "Joined" in response:
                        in_lobby_event.clear()  # Exit the lobby when a game is joined
                else:
                    print("[INFO] No active lobbies to join.")

            elif choice == "3":
                print("[DISCONNECT] Exiting server.")
                client_socket.send(choice.encode(FORMAT))  # Inform server of disconnection
                client_socket.close()
                listener_stop_event.set()  # Signal the listener thread to stop
                return  # Exit the function and disconnect the client

            else:
                print("[ERROR] Invalid choice. Please enter 1, 2, or 3.")

    except Exception as e:
        print(f"[ERROR] An error occurred during the lobby setup: {e}")

    # Start listening for server responses in a separate thread
    finally:
        listener_thread = threading.Thread(target=listen_to_server, args=(client_socket ,player_marker))
        listener_thread.daemon = True  # Ensure the thread exits when the main program exits
        listener_thread.start()

    # Step 5: Handle the game lobby logic
    try:
        #print(f"[DEBUG] Initial game_active state: {game_active_event.is_set()}")
        while True:
                if not game_active_event.is_set():
                    # Step 1: Take input from the user
                    # Allow non-game messages only if the game has not started
                    message = input("write 'start' to begin the game, 'quit' to disconnect, or any other message to communicate:\n")

                    # Step 2: Prevent sending non-game messages while the game is active
                    if not game_active_event.is_set():
                        client_socket.send(message.encode(FORMAT))
            
                    # Step 3: Handle 'quit' command
                    if message.lower() == "quit":
                        print("[DISCONNECT] Closing connection.")
                        client_socket.close()
                        listener_stop_event.set()  # Signal the listener thread to stop
                        break
            
                    # If the game is active, wait for it to finish
                    if game_active_event.is_set():
                        game_active_event.wait()

    except ConnectionResetError:
        print("[ERROR] Server disconnected unexpectedly.")
    finally:
        listener_stop_event.set()  # Ensure the thread stops
        listener_thread.join()     # Wait for the listener thread to exit
        client_socket.close()      #Ensure the client socket is closed

def send_move(client_socket, move):
    """
    Sends the player's move to the server.
    """
    try:
        client_socket.send(move.encode(FORMAT))
        print(f"[SENT] Move sent to server: {move}")
    except BrokenPipeError:
        print("[ERROR] Unable to send move. Connection to the server is broken.")
    except Exception as e:
        print(f"[ERROR] An unexpected error occurred while sending move: {e}")

def receive_game_update(client_socket):
    """
    Receives updates from the server.
    """
    try:
        #TO DO - make the value 8192 dynamic  
        update = client_socket.recv(8192).decode(FORMAT) #was increased from 1024 
        if not update:
            print("[ERROR] Lost connection to the server.")
            return None

        #if the update was received correctly, return the update
        return update
    except ConnectionResetError:
        print("[ERROR] Connection to the server was reset.")
        return None

def play_game(client_socket,player_marker):
    """
    Handles the main game loop when the game is active.
    """
    print("[INFO] Entering the game loop...")
    while True:
        # Step 1: Receive the current game state from the server
        update = receive_game_update(client_socket)
        #print(f"[DEBUG] Received raw game update: {update}")
        if update is None:
            print("[INFO] Closing the game due to server connection loss.")
            break

        # Step 2: Process the server's update
        try:
            game_data = eval(update)  # Convert the response string to a Python dictionary
            game_state = game_data["board"]
            status = game_data["status"]
            winner = game_data.get("winner")
            next_turn = game_data["next_turn"]

            # Step 3: Display the updated game board
            display_board(game_state)

            #Step 4: Check game status
            if status == "win":
                print(f"[GAME OVER] {winner} wins!")
                break
            elif status == "draw":
                print("[GAME OVER] It's a draw!")
                break

            # Step 5: Handle the player's turn
            if next_turn == player_marker:  
                move = input("Enter your move (row, column or 'end' to stop the game: ")
                if move.lower() == "end":
                    print("[GAME END] Exiting the game loop...")
                    break
                send_move(client_socket, move)
            else:
                print("[WAIT] Waiting for the opponent's move...")

        except Exception as e:
            print(f"[ERROR] Failed to process game state: {e}")
            break

def display_board(game_state):
    """
    Dynamically displays the game board using only vertical dividers.

    Args:
        game_state (list of list): A matrix representing the Tic-Tac-Toe board.
    """
    print("\nCurrent Board:")
    for row in game_state:
        # Join the cell values with vertical dividers, replacing empty cells with spaces
        print("| " + " | ".join(cell if cell else " " for cell in row) + " |")

if __name__ == "__main__":
    connect_to_server(HOST, PORT)