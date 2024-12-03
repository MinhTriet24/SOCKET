import shutil
import socket
import threading
import logging
import os
import time
import zipfile
from tkinter import filedialog
from datetime import datetime

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
CHUNK_SIZE = 1024*1024


server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)
logger.info("Create server successfully")

# Dictionary để lưu thông tin client
clients = {}

#Tuan
def get_unique_name(name, parent_folder_path, is_folder=False):
    """
    Đảm bảo tên file hoặc thư mục là duy nhất trong thư mục cha bằng cách thêm số vào cuối nếu cần.
    
    Args:
        name (str): Tên file hoặc thư mục cần đảm bảo duy nhất.
        parent_folder_path (str): Đường dẫn đến thư mục cha.
        is_folder (bool): Nếu True thì xử lý như thư mục, nếu False thì xử lý như file.
    
    Returns:
        str: Tên file hoặc thư mục duy nhất.
    """
    base, ext = os.path.splitext(name)  # Tách tên và phần mở rộng nếu là file
    counter = 1
    unique_name = name
    
    if is_folder:
        # Nếu là thư mục, không cần phần mở rộng
        unique_path = os.path.join(parent_folder_path, unique_name)
        
        while os.path.exists(unique_path):  # Kiểm tra sự tồn tại của thư mục
            unique_name = f"{name}({counter})"
            unique_path = os.path.join(parent_folder_path, unique_name)
            counter += 1
            
    else:
        # Nếu là file, kiểm tra sự tồn tại và xử lý phần mở rộng
        unique_path = os.path.join(parent_folder_path, unique_name)
        
        while os.path.exists(unique_path):  # Kiểm tra sự tồn tại của file
            unique_name = f"{base}({counter}){ext}"
            unique_path = os.path.join(parent_folder_path, unique_name)
            counter += 1
    
    return unique_name

def zip_folder(folder_path, zip_name):
    """
    Nén folder thành file zip.
    """
    with zipfile.ZipFile(zip_name, 'w') as zipf:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path, os.path.relpath(file_path, folder_path))
    return os.path.getsize(zip_name)  # Trả về kích thước file zip

def send_file(conn, address):
    """
    Gửi file từ server tới client theo từng chunk mà không cần lưu các chunk tạm thời.
    """
    try:
        # Nhận yêu cầu từ client
        file_name = conn.recv(1024).decode().strip()
        conn.sendall("OK".encode())
        logger.info(f"Received request from client: {address} and responded")

        # Lấy đường dẫn file
        file_path = os.path.join(SERVER_FOLDER, file_name)
        if not os.path.exists(file_path):
            conn.sendall("NOT FOUND".encode())
            logger.info(f"Sent respond: Didn't find file from {address}")
            raise FileNotFoundError(f"File {file_name} doesn't exist.")
        else:
            conn.sendall("FOUND".encode())
            logger.info(f"Sent respond: Found file from {address}")
        # Lấy kích thước file
        file_size = os.path.getsize(file_path)
        conn.sendall(f"{file_size}".encode())  # Gửi kích thước file
        ack = conn.recv(10).decode().strip()  # Nhận ACK từ client
        logger.info(f"Received ACK from {address}")
        if ack != "OK":
            raise Exception("Client didn't consider size of file.")

        # Gửi dữ liệu file theo từng chunk
        with open(file_path, "rb") as file:
            bytes_sent = 0
            while bytes_sent < file_size:
                chunk_data = file.read(CHUNK_SIZE)
                conn.sendall(chunk_data)
                bytes_sent += len(chunk_data)

                # Hiển thị tiến độ gửi
                progress = (bytes_sent / file_size) * 100
                print(f"Sent: {progress:.2f}%")

        # Nhận xác nhận từ client sau khi gửi xong
        ack = conn.recv(10).decode().strip()
        if ack != "OK":
            logger.info(f"Failed sent file '{file_name} for {address} ")
            raise Exception("Client didn't consider enoough size of file.")
        else:
            print(f"Sent file '{file_name}' succesfully ")
            logger.info(f"Sent file '{file_name}' succesfully for {address} ")
    except Exception as e:
        conn.sendall(b"NOT OK")
        print(f"Eror {file_name}: {e}")

def send_folder(server_socket, address):
    """
    Xử lý yêu cầu từ client và gửi folder dưới dạng file ZIP trực tiếp, không sử dụng đa luồng.
    """
    try:
        # Nhận tên folder từ client
        folder_name = server_socket.recv(1024).decode().strip()
        folder_path = os.path.join(SERVER_FOLDER, folder_name)
        logger.info(f"Received folder '{folder_name} successfully from {address}")

        if os.path.exists(folder_path) and os.path.isdir(folder_path):
            # Nén folder thành file zip
            zip_name = f"{folder_name}.zip"
            zip_path = os.path.join(SERVER_FOLDER, zip_name)
            zip_name = get_unique_name(zip_name, SERVER_FOLDER, is_folder=False)
            zip_size = zip_folder(folder_path, zip_path)
            logger.info(f"ZIP folder successfully for {address}")

            # Gửi thông báo rằng folder tồn tại
            server_socket.send(b"FOUND")
            logger.info(f"Found folder from {address}")
            ack = server_socket.recv(1024).decode().strip()
            if ack != "OK":
                logger.info(f"Didn't find folder from {address}")
                raise Exception("Client didn't consider ZIP file was existed.")

            # Gửi kích thước file ZIP
            server_socket.send(str(zip_size).encode())
            ack = server_socket.recv(1024).decode().strip()
            if ack != "OK":
                raise Exception("Client didn't consider size of file.")

            # Gửi dữ liệu file ZIP trực tiếp
            with open(zip_path, "rb") as zip_file:
                bytes_sent = 0
                while bytes_sent < zip_size:
                    chunk_data = zip_file.read(CHUNK_SIZE)  # Đọc dữ liệu theo chunk
                    server_socket.sendall(chunk_data)
                    bytes_sent += len(chunk_data)

                    # Hiển thị tiến độ gửi
                    progress = (bytes_sent / zip_size) * 100
                    print(f"Sent: {progress:.2f}%")

            # Nhận xác nhận từ client sau khi gửi xong
            ack = server_socket.recv(1024).decode().strip()
            if ack != "OK":
                raise Exception("Client didn't consider to receive enough ZIP file.")
            else:
                print(f"Sent folder '{folder_name}' successfully")
                logger.info(f"Sent folder '{folder_name}' successfully")


            # Xóa file ZIP sau khi gửi
            if os.path.exists(zip_path):
                os.remove(zip_path)
                logger.info(f"Removed file ZIP folder from {address}")
        else:
            # Thông báo rằng folder không tồn tại
            server_socket.send(b"NOT FOUND")
            logger.info(f"Didn't find file ZIP folder from {address}")
    except Exception as e:
        print(f"Eror: {e}")

#Triet
def free_bytes():
    total, used, free = shutil.disk_usage("/")
    return free

def uploadFile(conn, folder_path, address):
    #nhận tên file và kích thước file
    msg = conn.recv(SIZE).decode(FORMAT)
    try:
        file_name,file_size = msg.split("|")
        file_size = int(file_size)
    except:
        conn.send(f"[SERVER]: Error unpack message.".encode(FORMAT))
        print(f"[SERVER] Error: Unpack messages from {address}.")
        logger.info(f"Eror unpack message from {address} and notify it")
        return
    
    logger.info(f"Receive file {file_name} ({file_size} from {address})")
    
    #tạo đường dẫn file mới theo tên file nhận được từ server
    file_path = os.path.join(folder_path, get_unique_name(file_name,folder_path,os.path.isdir(file_name)))
    conn.send("OK".encode(FORMAT))

    #nhận các gói chunk và ghi vào file đã tạo
    try:
        success = False
        with open(file_path, "wb") as file:
            bytes_recv = 0
            while chunk:= conn.recv(SIZE):
                if not chunk:
                    print(f"Connection lost while receiving file from {address}")
                    logger.info(f"Connection lost while receiving file from {address}")
                    break
                file.write(chunk)
                bytes_recv += len(chunk)
                if(bytes_recv>=file_size):
                    success = True
                    break 
        
        if success: #trường hợp đã gửi file thành công
            print(f"Upload file {file_name} successfully to {address}")
            conn.send(f"Uploaded successfull file {file_name}.".encode(FORMAT))

        elif bytes_recv != file_size: #trường hợp up file không hoàn chỉnh do mất gói hay mất kết nối 
            logger.info(f"File {file_path} incomplete: expected {file_size}, received {bytes_recv}")
            conn.send(f"[SERVER]: File transfer incomplete.".encode(FORMAT))
            os.remove(file_path)  # Xóa file không hoàn chỉnh
            return

    #trường hợp lỗi khi mở file để ghi
    except OSError as e:
        logger.info(f"Error writing to file {file_path} from {address}")
        conn.send(f"[SERVER]: Error writing to file.".encode(FORMAT))
        return  
    except Exception as e:
        # Xử lý các lỗi không mong muốn khác
        logger.info(f"Unexpected error during file upload from {address}")
        conn.send(f"[SERVER]: Unexpected error during file upload.".encode(FORMAT))
        return
    
def uploadFolder(conn, pre_folder_path, address):
    #nhận tên folder từ máy client
    folder_name = conn.recv(SIZE).decode(FORMAT)
    print(f"Received folder '{folder_name}' from {address}")
    logger.info(f"Received folder '{folder_name}' from {address}")
    folder_name = os.path.basename(folder_name) #tên của folder

    folder_path = os.path.join(pre_folder_path, folder_name)

    #kiểm tra folder đã tồn tại hay chưa
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        logger.info(f"Created folder {folder_name} successfully for {address}.")
    else:
        count = 0
        while os.path.exists(folder_path):
            count+=1
            folder_path = f"{SERVER_FOLDER}/{folder_name}({count})"
        os.makedirs(folder_path)
        folder_name = f"{folder_name}({count})"
        logger.info(f"Created folder {folder_name} successfully for {address}.")

    #sau khi đã tạo được thư mục
    while True:
        try:
            msg = conn.recv(SIZE).decode(FORMAT)
            print(msg)
            #xử lý khi nhận được tín hiệu kết thúc folder
            if(msg == "END FOLDER"):
                print(f"Saved folder {folder_name} successfully from {address}")
                logger.info(f"Saved folder {folder_name} successfully from {address}")
                conn.send(f"Uploaded successfully folder: {folder_name}.".encode(FORMAT))
                break
            
            #khi tín hiệu là gửi file, foler hay thông báo lỗi
            cmd = msg.split("|")
            if(len(cmd)== 1 and cmd!="END FOLDER"):
                raise OSError(f"{msg}.")
            
            if cmd[1] == "FILE":
                uploadFile(conn, folder_path,address)
            elif cmd[1] == "FOLDER":
                uploadFolder(conn,folder_path,address)
            else:
                raise ValueError("Unknown type.")
        
        #trường hợp client bị lỗi trong quá trình gửi
        except OSError as e:
           print(f"Received '{msg}' from {address}")
           return
        except ValueError as e:
            print(f"Error: {e} from {address}")
        except Exception as e:
           print(f"Exception caught: {e} from {address}")
           return

def upload(type, size, connection, address):
    try:
        store = free_bytes()
        if store <size:
            raise OSError("No space left on device.")
        
        #trường hợp đủ dung lượng
        if(type == "FILE"):
            uploadFile(connection, SERVER_FOLDER, address)
        elif type == "FOLDER":
            connection.send("Ok".encode(FORMAT))
            uploadFolder(connection,SERVER_FOLDER,address)
            logger.info(f"Notify server ready for uploading folder from {address}")

    except OSError as e: #xử lý khi server hết dung lượng
        print(f"OS Error: {e}")
        connection.send("No space left on server.".encode(FORMAT))
        return
    except Exception as e:
        print(f"Exception caught: {e}")
        return
        
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
                upload(cmd[1],int(cmd[2]),connection,address)
            elif(cmd[0] == "download_file"):
                send_file(connection, address)
            elif(cmd[0] =="download_folder"):
                send_folder(connection, address)
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
#10.0.240.114