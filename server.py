import socket
import threading
import logging

logging.basicConfig(level=logging.INFO, filename="log_server.txt", filemode="w",
                    format="%(asctime)s - %(message)s")
logger = logging.getLogger(__name__)


# Khởi tạo IP server là máy đang chạy file server.py
PORT = 50505
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)
FORMAT = 'utf-8'

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)
logger.info("Create server successfully")

# Dictionary để lưu thông tin client
clients = {}

#Hàm kiểm tra các clients đang kết nối
def print_client_present():
    print(f"Current clients: {list(clients.keys())}")


# Hàm làm việc trực tiếp với client
def work_with_client(connection, address):
    # Thông báo client mới kết nối và thêm vào dictionary
    print(f"New connection: {address} connected")
    logger.info(f"New connection: {address} connected")
    clients[address] = connection

    connected = True
    while True:
        try:
            message = connection.recv(2048).decode(FORMAT)
            logger.info(f"Server receive: ({message}) from {address}")
            if message == "quit":
                connected = False
                break
            else:
                print(f"[{address}]: {message}")
        except Exception as e:
            print(f"Error with client {address}")
            connected = False
            break

    # Xóa client khỏi dictionary khi ngắt kết nối
    if connected == False:
        del clients[address]
        print(f"Client {address} disconnected.")
        logger.info(f"Client {address} disconnected.")
    connection.close()


# Hàm gửi tin nhắn riêng từ server đến client
def send_message_to_client(target_address, message):
    client_socket = clients.get(target_address)
    if client_socket:
        client_socket.send(message.encode(FORMAT))
        logger.info(f"Message sent {target_address} : {message}")
        print(f"Message sent {target_address} : {message}")
    else:
        print(f"Doesn't find this {target_address}")
        logger.info(f"Doesn't find this {target_address}")
    

def start():
    server.listen()
    print(f"Server is listening on {SERVER}")
    print("STARTING...")
    logger.info("Ready to connect")
    while True:
        connection, address = server.accept()
        thread = threading.Thread(target=work_with_client, args=(connection, address))
        thread.start()
        print(f"Active connections: {len(clients) + 1}")

        # Test server nói chuyện riêng với một client
        user_ip = input("User_IP: ").strip()
        logger.info(f"Input user_ip: {user_ip}")
        user_port = input("User port: ").strip()
        logger.info(f"Input user_port: {user_port}")
        try:
            user_port = int(user_port)
        except ValueError:
            print("Error port")
            continue
        
        target_address = (user_ip, user_port)
        if target_address:
            mess = input("Message : ")
            send_message_to_client(target_address, mess)
        else:
            print(f"Target_address nhập sai")
            
        

start()
