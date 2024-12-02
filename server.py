import socket
import threading
import logging
import os
import time
import zipfile
from tkinter import filedialog


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

socket_lock = threading.Lock()

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

def split_file(file_path, chunk_size):
    chunks = []
    with open(file_path, 'rb') as file:
        while True:
            chunk = file.read(chunk_size)
            if not chunk:
                break
            chunk_filename = f"{file_path}_part_{len(chunks)}"
            with open(chunk_filename, 'wb') as chunk_file:
                chunk_file.write(chunk)
            chunks.append(chunk_filename)
    return chunks

def send_file(conn, file_name, folder_path):
    try:
        data = conn.recv(1024).decode().strip()
        conn.sendall("OK".encode())
        # Get file path
        file_path = os.path.join(folder_path, file_name)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File {file_name} not found.")

        #  Split the file into chunks
        chunks = split_file(file_path, CHUNK_SIZE)
        num_chunks = len(chunks)
        conn.sendall(f"{num_chunks}".encode())  
        
        # Send chunks to the client
       
        threads = []
        for index, chunk_path in enumerate(chunks):
            thread = threading.Thread(target= send_chunk, args=(conn, index, chunk_path, num_chunks))
            threads.append(thread)
            thread.start()
            
        for thread in threads:
            thread.join()
        # ACK for send all chunks

        for chunk in chunks:
            if os.path.exists(chunk):
                os.remove(chunk)
        ack = conn.recv(10).decode().strip()

        if ack != 'OK':
            raise Exception("Failed to receive acknowledgment from client.")
        else:
            print(f"File {file_name} downloaded successfully.")
    except Exception as e:
        conn.sendall(b"NOT OK")
        print(f"Error handling download: {e}")


def send_chunk(conn, chunk_index, chunk_path, num_chunks):
    try:
        
        with socket_lock:
            # Get chunk size
            chunk_size = os.path.getsize(chunk_path)
            conn.sendall(f"{chunk_index}:{chunk_size}\n".encode())
            # ACK for chunk size
            ack = conn.recv(10).decode().strip()
            if ack != 'OK':
                raise Exception("Failed to receive acknowledgment from client.")
            
            # Send chunk data
            with open(chunk_path, 'rb') as chunk_file:
                chunk_data = chunk_file.read()
                conn.sendall(chunk_data)
            # ACK for chunk data
            ack = conn.recv(10).decode().strip()
            if ack != 'OK':
                raise Exception("Failed to receive acknowledgment from client.")
            else:
                print(f"sent chunk_{chunk_index} size: {os.path.getsize(chunk_path)} ({chunk_index + 1}/{num_chunks})")
    except Exception as e:
        print(f"Error sending chunk {chunk_index}: {e}")

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

def send_folder(server_socket):
    """
    Xử lý yêu cầu từ client và gửi folder dưới dạng file ZIP, sử dụng kỹ thuật đa luồng để gửi các chunk.
    """
    try:
        # Nhận tên folder từ client
        folder_name = server_socket.recv(1024).decode().strip()
        folder_path = os.path.join(SERVER_FOLDER, folder_name)

        
        if os.path.exists(folder_path) and os.path.isdir(folder_path):
            # Nén folder thành file zip
            zip_name = f"{folder_name}.zip"
            zip_name=get_unique_name(zip_name,folder_path,True)
            zip_size = zip_folder(folder_path, zip_name)

            # Gửi phản hồi và kích thước file zip
            server_socket.send(b"FOUND")
            rep=server_socket.recv(1024).decode().strip()
            if rep != "OK" :
                raise Exception("DON'T FOUND FILE")
            
            
            server_socket.send(str(zip_size).encode())

            # Chia file ZIP thành các chunk
            chunks = split_file(zip_name, CHUNK_SIZE)
            num_chunks = len(chunks)

            # Gửi số lượng chunk cho client
            server_socket.sendall(f"{num_chunks}".encode())

            # Gửi từng chunk sử dụng đa luồng
            threads = []
            for index, chunk_path in enumerate(chunks):
                thread = threading.Thread(
                    target=send_chunk, 
                    args=(server_socket, index, chunk_path, num_chunks)
                )
                threads.append(thread)
                thread.start()

            # Đợi tất cả các luồng hoàn thành
            for thread in threads:
                thread.join()

            # Nhận ACK từ client sau khi tất cả các chunk đã được gửi
            ack = server_socket.recv(10).decode().strip()
            if ack != 'OK':
                raise Exception("Failed to receive acknowledgment for all chunks.")
            else:
                print(f"Folder '{folder_name}' has been sent successfully.")

            # Dọn dẹp các file tạm
            for chunk in chunks:
                if os.path.exists(chunk):
                    os.remove(chunk)
            os.remove(zip_name)
        else:
              server_socket.sendall(b"NOT FOUND")
    except Exception as e:
        
        print(f"Error handling folder request: {e}")


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
