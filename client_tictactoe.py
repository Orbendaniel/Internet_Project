import socket
HOST = '127.0.0.1'  # Replace with the server's IP if needed
PORT = 5000         # Replace with the server's port if needed
FORMAT = 'utf-8'

def connect_to_server(host, port):
        # Step 1: Create a socket
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Step 2: Connect to the server
        client_socket.connect((host, port))
        print(f"[CONNECTED] Successfully connected to {host}:{port}")
        try:
            while True:
                # Step 1: Encode and send the move
                message = input("write 'quit' to disconnect\n")
                client_socket.send(message.encode('utf-8'))

                # Step 3: Receive server response
                response = client_socket.recv(1024).decode('utf-8')
                print(f"[SERVER RESPONSE] {response}")

                # Step 4: Handle quit command
                if message.lower() == 'quit':
                    print("[DISCONNECT] Closing connection.")
                    break
                
        except ConnectionResetError:
            print("[ERROR] Server disconnected unexpectedly.")
        finally:
            client_socket.close()        

if __name__ == "__main__":
    connect_to_server(HOST, PORT)