import socket
import threading
import logging
import os
import time

logging.basicConfig(level=logging.INFO, filename="log_server.txt", filemode="w",
                    format="%(asctime)s - %(message)s")
logger = logging.getLogger(__name__)


# Khởi tạo IP server là máy đang chạy file server.py
PORT = 50505
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)
FORMAT = 'utf-8'
SERVER_FOLDER = "server_folder"
SIZE = 1024


server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)
logger.info("Create server successfully")

# Dictionary để lưu thông tin client
clients = {}

#Tuan
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

#Triet
def uploadFile(conn, folderPath, address):
    #revceie file name
    msg = conn.recv(SIZE).decode(FORMAT)
    try:
        fileName,fileSize = msg.split("|")
        fileSize = int(fileSize)
    except:
        conn.send(f"[SERVER]: Error.Unpack message.".encode(FORMAT))
        time.sleep(0.01)
        print(f"Error: Unpack messages from {address}.")
        print("\n")
        logger.info(f"Eror unpack message from {address} and notify it")
        return
    
    print(f"Received file {fileName} ({fileSize} Bytes) from {address}.")
    logger.info(f"Receive file {fileName} ({fileSize} from {address})")
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

    #save file at server_folder
    endFile = True
    with open(filePath, "wb") as file:
        size = 0
        while chunk:= conn.recv(SIZE):
            if not chunk:
                print(f"Connection lost while receiving file from {address}")
                logger.info(f"Connection lost while receiving file from {address}")
                endFile = False
                break
            file.write(chunk)
            size += len(chunk)
            if(size>=fileSize):
                break   
    
    if endFile == True:
        print(f"Saved successfully file: {fileName} ({size} Bytes) from {address}.")
        print(f"\n")
        conn.send(f"Upload successfully file {fileName} ({size} Bytes)".encode(FORMAT))
        logger.info(f"Saved and notify successfully file: {fileName} ({size} Bytes) from {address}.")
        time.sleep(0.01)
    else:
        print(f"Upload file failed from {address}")
        print("\n")
        logger.info(f"Upload file failed from {address}")
 
def uploadFolder(conn, preFolderPath, address):
    #receive folder name when server receive folder upload from client
    conn.send("Ok".encode(FORMAT))
    logger.info(f"Notify server ready for uploading folder from {address}")
    folderName = conn.recv(SIZE).decode(FORMAT)
    parts = folderName.split("/")
    if(len(parts) > 1):
        folderName = parts[len(parts)-1]
    
    folderPath = os.path.join(preFolderPath, folderName)
    # print(folderPath)

    #check exists
    if not os.path.exists(folderPath): #create folder if it not exists
        os.makedirs(folderPath)
        print(f"Created folder {folderName} successfully for {address}.")
        logger.info(f"Created folder {folderName} successfully for {address}.")
        conn.send(f"[SERVER]: Created folder {folderName} successfully.".encode(FORMAT))
        time.sleep(0.01)
    else:
        count = 0
        while os.path.exists(folderPath):
            count+=1
            folderPath = f"{SERVER_FOLDER}/{folderName}({count})"
        os.makedirs(folderPath)
        folderName = f"{folderName}({count})"
        print(f"Created folder {folderName} successfully for {address}.")
        logger.info(f"Created folder {folderName} successfully for {address}.")
        conn.send(f"[SERVER]: Created fodler {folderName} successfully.".encode(FORMAT))
        time.sleep(0.01)

    while True:
        msg = conn.recv(SIZE).decode(FORMAT)
        if(msg == "END FOLDER"):
            print(f"Saved folder {folderName} successfully from {address}")
            logger.info(f"Saved folder {folderName} successfully from {address}")
            conn.send(f"Uploaded successfully folder: {folderName}.".encode(FORMAT))
            time.sleep(0.01)
            break
        cmd = msg.split("|")
        if(len(cmd)>0):
            if(cmd[1] == "FILE"):
                print(f"Received upload file signal")
                uploadFile(conn, folderPath)
            elif(cmd[1] == "FOLDER"):
                print(f"Received upload folder signal")
                uploadFolder(conn, folderPath)
        
# Work_directly_with_client
def handle(connection, address):
    # Thông báo client mới kết nối và thêm vào dictionary
    print(f"New connection: {address} connected")
    logger.info(f"New connection: {address} connected")
    clients[address] = connection

    connected = True
    while True:
        try:
            msg = connection.recv(SIZE).decode(FORMAT)
            logger.info(f"Receive message from {address} : {msg}")
            print(f"Receive message from {address} : {msg}")
            cmd = msg.split("|")
            if (cmd[0] == "QUIT"):
                connected = False
                break
            elif(cmd[0] == "UPLOAD"):
                if(cmd[1] == "FILE"):
                    uploadFile(connection, SERVER_FOLDER, address) 
                elif(cmd[1] == "FOLDER"):
                    uploadFolder(connection, SERVER_FOLDER, address)
            elif(cmd[0] == "DOWNLOAD"):
                #send_file(...)
                continue
        except Exception as e:
            print(f"Error with client {address}")
            logger.info(f"Error with client {address}")
            connected = False
            break

    # Xóa client khỏi dictionary khi ngắt kết nối
    if connected == False:
        del clients[address]
        print(f"Client {address} disconnected.")
        logger.info(f"Client {address} disconnected.")
        logger.info(f"Remove {address}")
    connection.close()

# 
def main():
    server.listen()
    print(f"Server is listening on {SERVER}")
    print("STARTING...")
    logger.info("Ready to connect")
    while True:
        connection, address = server.accept()
        thread = threading.Thread(target=handle, args=(connection, address))
        logger.info(f"Create new thread for {address}")
        thread.start()
        print(f"Active connections: {len(clients) + 1}")
        print("\n")


main()