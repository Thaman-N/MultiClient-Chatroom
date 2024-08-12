import socket
import threading
import os

def listen_for_messages(sock):
    while True:
        try:
            message, _ = sock.recvfrom(4096)  # Adjust buffer size if necessary for larger messages
            print(message.decode('utf-8'))
        except OSError:
            break  # Exit the loop if the socket is closed.

def send_file(sock, filepath, server_address):
    if not os.path.isfile(filepath):
        print("\033[1;31mFile does not exist.\033[0m")
        return

    filename = os.path.basename(filepath)
    start_marker = f"START:{filename}".encode()
    sock.sendto(start_marker, server_address)  # Signal the start of a file transfer

    with open(filepath, "rb") as f:
        chunk = f.read(1024)  # Read the file in chunks
        while chunk:
            sock.sendto(chunk, server_address)
            chunk = f.read(1024)

    end_marker = f"END:{filename}".encode()
    sock.sendto(end_marker, server_address)  # Signal the end of the file transfer
    print(f"\033[1;32mSent file: {filename}\033[0m")

def receive_file(sock, server_address):
    filename = input("\033[1;35mEnter the filename to receive: \033[0m")
    request_marker = f"RECEIVE:{filename}".encode()
    sock.sendto(request_marker, server_address)
    print(f"\033[1;33mRequested file: {filename}\033[0m")

    try:
        file_data, _ = sock.recvfrom(65536)  # Adjust buffer size if necessary
        if file_data.startswith(b"\033[1;31mFile "):
            print(file_data.decode('utf-8'))
        else:
            with open(filename, "wb") as file:
                file.write(file_data)
            print(f"\033[1;32mReceived file: {filename}\033[0m")
    except OSError:
        print("\033[1;31mError receiving file.\033[0m")

def client():
    HOST = '10.30.202.143'
    PORT = 8888
    server_address = (HOST, PORT)

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Start listening for messages in a separate thread
    threading.Thread(target=listen_for_messages, args=(client_socket,), daemon=True).start()

    username = input("\033[1;35mEnter your username: \033[0m")
    print("\033[1;35mType your message or type '/sendfile <filepath>' to send a multimedia file.\033[0m")
    print("\033[1;35mType '/receivefile' to receive a file from the server.\033[0m")
    print("\033[1;35mType '/exit' to leave the chat room.\033[0m")
    print("\033[1;35mType '/list' to list all connected clients.\033[0m")

    while True:
        message = input("")
        if message.startswith("/sendfile"):
            _, filepath = message.split(" ", 1)
            send_file(client_socket, filepath, server_address)
        elif message.startswith("/receivefile"):
            receive_file(client_socket, server_address)
        elif message == "/exit":
            exit_message = f"EXIT:{username}".encode('utf-8')
            client_socket.sendto(exit_message, server_address)
            break
        elif message == "/list":
            list_message = "LIST:".encode('utf-8')
            client_socket.sendto(list_message, server_address)
        else:
            full_message = f"\033[1;33m<{username}>: \033[1;37m{message}\033[0m".encode('utf-8')
            client_socket.sendto(full_message, server_address)

    client_socket.close()

if __name__ == "__main__":
    client()