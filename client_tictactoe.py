import socket
import threading
HOST = '127.0.0.1'  # Replace with the server's IP if needed
PORT = 5000  # Replace with the server's port if needed
FORMAT = 'utf-8'

def listen_to_server(client_socket):
    """
    Continuously listens for messages from the server.
    """
    while True:
        try:
            response = receive_game_update(client_socket)
            if not response:
                print("[ERROR] Lost connection to the server.")
                break

            # Check for "game started" message
            if "game started" in response.lower():
                print("[INFO] Game has started! Entering game loop...")
                play_game(client_socket)  # Automatically enter the game loop
                print("[GAME ENDED] Returning to communication loop.")

        except Exception as e:
            print(f"[ERROR] An error occurred while listening to the server: {e}")
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

    # Start the listener thread
    listener_thread = threading.Thread(target=listen_to_server, args=(client_socket,))
    listener_thread.daemon = True  # Ensure the thread exits when the main program exits
    listener_thread.start()

    try:
        # game_running = False   Flag to indicate if the game is active

        while True:
            # Step 1: Take input from the user
            message = input("write 'start' to begin the game, 'quit' to disconnect, or any other message to communicate:\n")
            client_socket.send(message.encode(FORMAT))

            # Step 2: Handle 'quit' command
            if message.lower() == 'quit':
                print("[DISCONNECT] Closing connection.")
                break

            # # Step 3: Receive server response
            # response = client_socket.recv(1024).decode(FORMAT)
            # print(f"[SERVER RESPONSE] {response}")
            
    except ConnectionResetError:
        print("[ERROR] Server disconnected unexpectedly.")
    finally:
        client_socket.close()


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
        return update
    except ConnectionResetError:
        print("[ERROR] Connection to the server was reset.")
        return None


def play_game(client_socket):
    """
    Handles the main game loop when the game is active.
    """
    print("[INFO] Entering the game loop...")
    while True:
        # Step 1: Receive the current game state from the server
        update = receive_game_update(client_socket)
        if update is None:
            print("[INFO] Closing the game due to server connection loss.")
            break

        # Step 2: Process the server's update
        try:
            game_data = eval(update)  # Convert the response string to a Python dictionary
            game_state = game_data["board"]
            status = game_data["status"]#
            winner = game_data.get("winner")
            next_turn = game_data["next_turn"]

            # Step 3: Display the updated game board
            display_board(game_state)

            # Step 4: Check game status
            # if status == "win":
            #     print(f"[GAME OVER] {winner} wins!")
            #     break
            # elif status == "draw":
            #     print("[GAME OVER] It's a draw!")
            #     break

        #     # Step 5: Handle the player's turn
        #     if next_turn == "X":  # Adjust this logic to match the client's player marker
        #         move = input("Enter your move (row, column or 'end' to stop the game: ")
        #         if move.lower() == "end":
        #             print("[GAME END] Exiting the game loop...")
        #             break
        #         send_move(client_socket, move)
        #     else:
        #         print("[WAIT] Waiting for the opponent's move...")

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