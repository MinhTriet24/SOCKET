import socket

FORMAT ='utf-8'
SERVER = input("Server HOST: ")
PORT = 50505
ADDR = (SERVER, PORT)

if not SERVER:
    SERVER = '127.0.0.1'

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(ADDR)


client.send("Hello World".encode(FORMAT))
input()
message_recv = client.recv(2048).decode(FORMAT)
print(f"Server: {message_recv}")
input()
client.send("quit".encode(FORMAT))
