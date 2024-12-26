import socket
# Define client parameters
HOST = '127.0.0.1'
PORT = 5000
FORMAT = 'utf-8'

def start_client():
    # Step 1: Connect to the server
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((HOST, PORT))
    print(f"[CONNECTED] Connected to server at {HOST}:{PORT}")
    
    try:
        while True:
            # Step 2: Send a move/message to the server
            message = input("Enter your move (or 'quit' to disconnect): ")
            client.send(message.encode(FORMAT))
            
            # Step 3: Receive server response
            response = client.recv(1024).decode(FORMAT)
            print(f"[SERVER RESPONSE] {response}")
            
            # Step 4: Handle quit command
            if message.lower() == 'quit':
                print("[DISCONNECT] Closing connection.")
                break
                
    except ConnectionResetError:
        print("[ERROR] Server disconnected unexpectedly.")
    finally:
        client.close()         


if __name__ == "__main__":
    start_client()