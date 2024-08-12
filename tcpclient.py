import socket
import ssl
import threading
import os

def receive_messages(client_socket):
    assembling_file = False
    file_chunks = []
    filename = ""

    while True:
        try:
            data = client_socket.recv(1024)
            # Check if we are currently assembling a file
            if assembling_file:
                if data.endswith(b"EOF"):
                    # Remove EOF from the last chunk
                    data = data[:-3]
                    file_chunks.append(data)
                    # Save the file
                    with open(filename, "wb") as f:
                        for chunk in file_chunks:
                            f.write(chunk)
                    print(f"File {filename} has been downloaded.")
                    assembling_file = False
                    file_chunks = []
                else:
                    file_chunks.append(data)
            elif data.startswith(b"FILE:"):
                assembling_file = True
                filename = data[5:].decode()  # Extract the filename
                # Prepare to save the file in the current directory
                filename = os.path.join(os.getcwd(), "received_" + filename)
            else:
                print(data.decode())
        except Exception as e:
            print(f"Error: {e}")
            break


def send_file(client_socket, filepath):
    if not os.path.isfile(filepath):
        print("File does not exist.")
        return
    
    filename = os.path.basename(filepath)
    client_socket.send(f"FILE:{filename}".encode())  # Signal the start of a file transfer
    
    with open(filepath, "rb") as f:
        chunk = f.read(1024)
        while chunk:
            client_socket.send(chunk)
            chunk = f.read(1024)
    
    client_socket.send(b"EOF")  # Signal the end of the file transfer
    print(f"Sent file: {filename}")

def client():
    HOST = '10.30.202.143'
    PORT = 8888

    # Create an unverified SSL context
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    secure_client_socket = context.wrap_socket(client_socket, server_hostname=HOST)
    secure_client_socket.connect((HOST, PORT))
    
    # Receive and verify PIN
    pin = secure_client_socket.recv(1024).decode()
    while True:
        user_pin = input("Enter the 4-digit PIN to join the chatroom: ")
        if user_pin == pin:
            break
        else:
            print("Incorrect PIN. Please try again.")

    # Start listening for messages
    threading.Thread(target=receive_messages, args=(secure_client_socket,), daemon=True).start()

    username = input("Enter your username: ")
    secure_client_socket.send(username.encode())  # Send username to server
    print("Type your message or type '/sendfile <filepath>' to send a multimedia file.")

    while True:
        message = input("")
        if message.startswith("/sendfile"):
            _, filepath = message.split(" ", 1)
            send_file(secure_client_socket, filepath)
        elif message.startswith("/receive"):
            secure_client_socket.send(message.encode())
        elif message == "/exit":
                secure_client_socket.send(message.encode())
                print("You have left the chatroom.")
                break
        else:
            secure_client_socket.send(message.encode())

if __name__ == "__main__":
    client()