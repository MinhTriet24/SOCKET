import socket
import threading
import logging
import os

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
    
def send_file(conn, filename):
    """
    Gửi file đến client nếu file tồn tại, ngược lại gửi thông báo lỗi.
    """
    if os.path.exists(filename):
        # Lấy kích thước file
        file_size = os.path.getsize(filename)
        
        # Gửi thông báo thành công kèm theo kích thước file
        conn.sendall(f"SUCCESS|{file_size}".encode(FORMAT))

        # Đọc và gửi file theo từng phần
        with open(filename, "rb") as file:
            while chunk := file.read(1024):  # Đọc file từng khối 1024 byte
                conn.sendall(chunk)
        #conn.sendall(b"END")
        print(f"Đã gửi file '{filename}' ({file_size} Bytes) thành công.")
    else:
        conn.sendall("ERROR: File không tồn tại!".encode(FORMAT))

def uploadFile(conn, folderPath):
    #revceie file name
    msg = conn.recv(SIZE).decode(FORMAT)
    try:
        fileName,fileSize = msg.split("|")
        fileSize = int(fileSize)
    except:
        conn.send(f"[SERVER] Error: Unpack message.".encode(FORMAT))
        time.sleep(0.01)
        print(f"[SERVER] Error: Unpack messages.")
        return
    
    print(f"[SERVER] Revceied file name {fileName} ({fileSize} Bytes).")
    #defination file path
    filePath = os.path.join(folderPath, fileName)
    #split  name and ext from file
    name, ext = os.path.splitext(fileName)

    #check file exist
    count = 1
    while os.path.exists(filePath):
        filePath = os.path.join(SERVER_FOLDER, f"{name}({count}){ext}")
        count+=1
    conn.send("OK".encode(FORMAT))
    print(filePath)

    #save file at server_folder
    endFile = True
    with open(filePath, "wb") as file:
        size = 0
        while chunk:= conn.recv(SIZE):
            if not chunk:
                print(f"[SERVER] Connection lost while receiving file")
                endFile = False
                break
            file.write(chunk)
            size += len(chunk)
            if(size>=fileSize):
                break   
    
    if endFile == True:
        print(f"[SERVER] Saved file: {fileName} ({size} Bytes).")
        conn.send(f"Upload successfully file {fileName} ({size} Bytes)".encode(FORMAT))
        time.sleep(0.01)
    else:
        print("[SERVER] Upload failed")
 

def uploadFolder(conn, preFolderPath):
    #receive folder name when server receive folder upload from client
    conn.send("OK".encode(FORMAT))
    folderName = conn.recv(SIZE).decode(FORMAT)
    parts = folderName.split("/")
    if(len(parts) > 1):
        folderName = parts[len(parts)-1]
    
    folderPath = os.path.join(preFolderPath, folderName)
    print(folderPath)

    #check exists
    if not os.path.exists(folderPath): #create folder if it not exists
        os.makedirs(folderPath)
        print(f"[SERVER] Create folder {folderName} successfully.")
        conn.send(f"[SERVER] Created fodler {folderName} successfully.".encode(FORMAT))
        time.sleep(0.01)
    else:
        count =0
        while os.path.exists(folderPath):
            count+=1
            folderPath = f"{SERVER_FOLDER}/{folderName}({count})"
        os.makedirs(folderPath)
        folderName = f"{folderName}({count})"
        print(f"[SERVER] Create folder {folderName} successfully.")
        conn.send(f"[SERVER] Created fodler {folderName} successfully.".encode(FORMAT))
        time.sleep(0.01)

    while True:
        msg = conn.recv(SIZE).decode(FORMAT)
        if(msg == "END FOLDER"):
            print(f"[SERVER] Saved folder {folderName}")
            conn.send(f"Uploaded successfully folder {folderName}.".encode(FORMAT))
            time.sleep(0.01)
            break
        cmd = msg.split("|")
        if(len(cmd)>0):
            if(cmd[1] == "FILE"):
                print(f"[SERVER] Receive upload file signal")
                uploadFile(conn, folderPath)
            elif(cmd[1] == "FOLDER"):
                print(f"[SERVER] Receive upload folder signal")
                uploadFolder(conn, folderPath)
        

def handle(conn):
    while True:
        msg = conn.recv(SIZE).decode(FORMAT)
        print(f"[CLIENT] Sent messages {msg}.")
        cmd = msg.split("|")
        if cmd[0] == "QUIT":
            print(f"Disconnected from {cmd[1]},{cmd[2]}")
            conn.close()
            break
        elif(cmd[0] == "UPLOAD"):
            if(cmd[1] == "FILE"):
                print(f"[SERVER] Receive upload file signal from {cmd[2]},{cmd[3]}.")
                uploadFile(conn, SERVER_FOLDER) 
            elif(cmd[1] == "FOLDER"):
                print(f"[SERVER] Receive upload folder signal from {cmd[2]},{cmd[3]}.")
                uploadFolder(conn, SERVER_FOLDER)
        elif(cmd[0] == "DOWNLOAD"):
            #send_file(...)
            continue
    return 


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
