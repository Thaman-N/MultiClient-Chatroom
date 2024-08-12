import socket
import os

def server():
    HOST = '10.30.202.143'
    PORT = 8080
    clients = []
    client_usernames = {}  # Dictionary to store client addresses and usernames
    file_chunks = {}  # Dictionary to store file chunks for each client

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((HOST, PORT))
    print("UDP Chat Server Started. Waiting for clients...")

    received_files_dir = 'Server_Storage'
    if not os.path.exists(received_files_dir):
        os.makedirs(received_files_dir)

    while True:
        try:
            message, client_address = server_socket.recvfrom(65536)
            if client_address not in clients:
                clients.append(client_address)
                print(f"New client joined: {client_address}")

            if message.startswith(b"START:"):
                filename = message[len(b"START:"):].decode()
                assembling_file = True
                file_chunks[client_address] = []
                print(f"\033[1;32mStarting to receive file: {filename}\033[0m")

            elif message.startswith(b"END:") and client_address in file_chunks:
                filename = message[len(b"END:"):].decode()
                file_path = os.path.join(received_files_dir, filename)
                with open(file_path, "wb") as file:
                    for chunk in file_chunks[client_address]:
                        file.write(chunk)
                print(f"\033[1;32mFile received and saved: {file_path}\033[0m")
                del file_chunks[client_address]
                broadcast(f"\033[1;32mFile {filename} received and saved.\033[0m".encode(), client_address, clients, server_socket)

            elif client_address in file_chunks:
                file_chunks[client_address].append(message)

            elif message.startswith(b"RECEIVE:"):
                filename = message[len(b"RECEIVE:"):].decode()
                file_path = os.path.join(received_files_dir, filename)
                if os.path.isfile(file_path):
                    with open(file_path, "rb") as file:
                        file_data = file.read()
                        server_socket.sendto(file_data, client_address)
                        print(f"\033[1;32mSent file: {filename} to {client_address}\033[0m")
                else:
                    error_message = f"\033[1;31mFile {filename} not found on the server.\033[0m".encode()
                    server_socket.sendto(error_message, client_address)

            elif message.startswith(b"EXIT:"):
                username = message[len(b"EXIT:"):].decode()
                client_usernames.pop(client_address, None)  # Remove the username from the dictionary
                clients.remove(client_address)
                print(f"\033[1;31mClient {client_address} ({username}) left the chat room.\033[0m")
                broadcast(f"\033[1;31m{username} left the chat room.\033[0m".encode(), client_address, clients, server_socket)

            elif message.startswith(b"LIST:"):
                client_list = "\n".join([f"{client_address} ({client_usernames.get(client_address, 'Unknown')})" for client_address in clients])
                list_message = f"Connected clients:\n{client_list}".encode()
                server_socket.sendto(list_message, client_address)

            else:
                username = message.decode('utf-8').split(">:", 1)[0][2:]
                client_usernames[client_address] = username  # Store the username for the client
                print(f"{message.decode('utf-8')}")
                broadcast(message, client_address, clients, server_socket)

        except KeyboardInterrupt:
            print("\n \033[1;31mServer is shutting down.\033[0m")
            break
        except Exception as e:
            print(f"\033[1;31mAn error occurred: {e}\033[0m")
            break

    server_socket.close()

def broadcast(message, sender_address, clients, server_socket):
    """Broadcasts a message to all clients except the sender."""
    for client in clients:
        #if client != sender_address:
        #print(client)
        server_socket.sendto(message, client)

if __name__ == "__main__":
    server()