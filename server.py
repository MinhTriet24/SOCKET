import socket
import threading

PORT = 50505
# Khởi tạo IP server là máy đang chạy file server.py
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)
HEADER = 64
FORMAT = 'utf-8'

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)

# Hàm làm việc trực tiếp với client
def work_with_client(connection, address):
    print(f"New connection: {address} connected")
    connected = True
    # Demo xử lý chat đa luồng
    while connected:
        message = connection.recv(2048).decode(FORMAT)
        if message == "quit":
            connected = False

        print(f"[{address} : {message}]")
    connection.close()

def start():
    server.listen()
    print(f"Server is listening on {SERVER}")
    print("STARTING")
    while True:
        connection, address = server.accept()
        # Xử lý đa luồng
        thread = threading.Thread(target=work_with_client, args=(connection, address))
        thread.start()
        # Thông báo đang kết nối với client thứ i
        print(f"Active connections: {threading.active_count() - 1}")




start()


