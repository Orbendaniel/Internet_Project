import socket
import threading

# GLOBAL VARIABLES 
HOST = '127.0.0.1'  # Standard loopback IP address (localhost)
PORT = 5000  # Port to listen on (non-privileged ports are > 1023)
FORMAT = 'utf-8'  # Define the encoding format of messages from client-server
ADDR = (HOST, PORT)  # Creating a tuple of IP+PORT
x=1
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
        thread = threading.Thread(target=handle_client, args=(connection, address))
        thread.start()

def handle_client(conn, addr):
    print(f"[HANDLING CLIENT] {addr}")
    connected = True

    try:
        while connected:
            # Step 1: Receive a move from the client
            msg = conn.recv(1024).decode(FORMAT)

            if not msg:
                print(f"[DISCONNECT] Empty message received. Closing connection to {addr}")
                break
            
            print(f"[{addr}] {msg}")

            # Step 2: Process the client's move
            if msg.lower() == 'quit':
                print(f"[DISCONNECT] {addr} disconnected.")
                connected = False
                break

            # Here, we need to validate and update game state
            # For now, let's assume we simply echo the message back
            response = f"Server received your move: {msg}"
            
            # Step 3: Send response/update back to the client
            conn.send(response.encode(FORMAT))
        
    except ConnectionResetError:
        print(f"[ERROR] Connection with {addr} reset unexpectedly.")
    finally:
        # Step 4: Clean up the connection
        conn.close()
        print(f"[CONNECTION CLOSED] {addr}")

# Main
if __name__ == '__main__':
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Opening Server socket
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Allow address reuse
    print("[STARTING] server is starting...")
    start_server()