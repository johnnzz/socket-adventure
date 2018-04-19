import socket
import sys

try:
    port = int(sys.argv[1])
except IndexError:
    print("Please include a port number, eg: python serve.py 50000")
    exit(-1)

client_socket = socket.socket()
try:
    client_socket.connect(("127.0.0.1", port))
except ConnectionRefusedError:
    print("You need to start the server first.")
    sys.exit(0)

while True:
    response = client_socket.recv(4096).decode()
    print(response)

    if "Goodbye!" in response:
        break

    # protect against empty input
    my_input = ""
    while my_input == "":
        my_input = input("> ")

    my_message = my_input.encode('utf-8')
    client_socket.sendall(my_message)
