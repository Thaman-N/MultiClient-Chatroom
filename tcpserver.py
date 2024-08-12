import socket
import ssl
import threading
import random
import os

def broadcast(message, sender_socket, clients):
    for client in clients:
        if client != sender_socket:  # Don't send the message back to the sender
            try:
                client.send(message)
            except:
                client.close()
                clients.remove(client)

def handle_client(client_socket, client_address, clients, pin, multimedia_dir):
    print(f"Accepted connection from {client_address}")
    username = client_socket.recv(1024).decode()
    print(f"{client_address} is now known as '{username}'")

    while True:
        try:
            data = client_socket.recv(1024)
            if not data:
                break
            if data.startswith(b"FILE:"):
                filename = data[len("FILE:"):]
                file_path = os.path.join(multimedia_dir, filename.decode())
                with open(file_path, "wb") as f:
                    while True:
                        file_data = client_socket.recv(1024)
                        if not file_data or file_data.endswith(b"EOF"):
                            break
                        f.write(file_data)
                print(f"Received multimedia file: {filename.decode()}")
                broadcast(f"{username} sent a file: {filename.decode()}".encode(), client_socket, clients)
            # Inside handle_client function, after other if-else blocks
            elif data.startswith(b"/receive "):
                requested_filename = data.decode().split(' ', 1)[1]
                requested_file_path = os.path.join(multimedia_dir, requested_filename)
                if os.path.exists(requested_file_path):
                    client_socket.send(f"FILE:{requested_filename}".encode())
                    with open(requested_file_path, "rb") as file:
                        chunk = file.read(1024)
                        while chunk:
                            client_socket.send(chunk)
                            chunk = file.read(1024)
                    client_socket.send(b"EOF")
                    print(f"Sent {requested_filename} to {client_address}")
                else:
                    client_socket.send("File not found.".encode())
            
            elif data.decode() == "/exit":
                username_left = username
                try:
                    clients.remove(client_socket)
                except Exception as e:
                    pass  # Client socket not found in the list
                client_socket.close()
                print(f"{username_left} has left the chatroom.")
                broadcast(f"{username_left} has left the chatroom.".encode(), client_socket, clients)
                break

            else:
                message = f"<{username}> {data.decode()}"
                print(message)
                broadcast(message.encode(), client_socket, clients)
            
        except Exception as e:
            print(f"Error: {e}")
            break

    clients.remove(client_socket)
    client_socket.close()
    print(f"Connection from {client_address} closed")

def main():
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile="server.crt", keyfile="server.key")

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('10.30.202.143', 8888))
    server_socket.listen(5)

    secure_server_socket = context.wrap_socket(server_socket, server_side=True)
    pin = str(random.randint(1000, 9999))
    print(f"Chatroom server is listening for connections. PIN: {pin}")
    clients = []
    multimedia_dir = "received_files"
    if not os.path.exists(multimedia_dir):
        os.makedirs(multimedia_dir)

    while True:
        client_socket, client_address = secure_server_socket.accept()
        client_socket.send(pin.encode())
        clients.append(client_socket)
        client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address, clients, pin, multimedia_dir))
        client_thread.start()

if __name__ == "__main__":
    main()