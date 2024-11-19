import socket
import threading

PORT = 50505
# Khởi tạo IP server là máy đang chạy file server.py
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)
FORMAT = 'utf-8'

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)

# Dictionary để lưu thông tin client
clients = {}

# Hàm làm việc trực tiếp với client
def work_with_client(connection, address):
    print(f"New connection: {address} connected")

    # Thêm client vào dictionary
    clients[address] = connection
    print(f"Current clients: {list(clients.keys())}")

    connected = True
    while True:
        try:
            message = connection.recv(2048).decode(FORMAT)
            if message == "quit":
                connected = False
                break
            else:
                print(f"[{address}]: {message}")
        except Exception as e:
            print(f"Error with client {address}: {e}")
            connected = False
            break

    # Xóa client khỏi dictionary khi ngắt kết nối
    if connected == False:
        del clients[address]
        print(f"Client {address} disconnected.")

    connection.close()

# Hàm gửi tin nhắn riêng từ server đến client
def send_message_to_client(target_address, message):
    client_socket = clients.get(target_address)
    if client_socket:
        client_socket.send(message.encode(FORMAT))
        print(f"Message sent {target_address} : {message}")
    else:
        print(f"Doesn't find this {target_address}")

# Hàm in ra info clients trong dictionary
def print_info_clients():
    print("Current connected clients:")
    for address in clients.items():
        print(f"Client {address}")

def start():
    server.listen()
    print(f"Server is listening on {SERVER}")
    print("STARTING...")
    while True:
        connection, address = server.accept()
        thread = threading.Thread(target=work_with_client, args=(connection, address), daemon=True)
        thread.start()
        print(f"Active connections: {len(clients) + 1}")

        # Test server nói chuyện riêng với một client
        user_ip = input("User_IP: ").strip()
        user_port = input("User port: ").strip()
        try:
            user_port = int(user_port)
        except ValueError:
            print("Port phải là số nguyên. Vui lòng nhập lại.")
            continue
        
        target_address = (user_ip, user_port)
        if target_address:
            mess = input("Message : ")
            send_message_to_client(target_address, mess)
        else:
            print(f"Target_address nhập sai")
            
        

start()
