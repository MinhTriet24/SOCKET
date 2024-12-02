import socket
import os
import random
import time
import pandas as pd
from tkinter import *
from tkinter import filedialog, simpledialog, ttk
import zipfile


FORMAT ='utf-8'
SERVER = input("Server HOST: ")
if not SERVER:
        SERVER = '127.0.0.1'
PORT = 50505
ADDR = (SERVER, PORT)
CLIENT_FOLDER = "client_folder"
SIZE = 1024
CHUNK_SIZE = 1024*1024


# Tuan
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


def download_file(client_socket, file_name):
    """
    Nhận file từ server và lưu vào thư mục chỉ định.
    Nếu trùng tên file, tự động đổi tên để tránh ghi đè.
    """
    try:
        # Gửi yêu cầu file đến server
        client_socket.sendall(file_name.encode())
        print(f"Yêu cầu tải file: {file_name}")

        ack = client_socket.recv(1024).decode().strip()
        if ack != "OK":
            raise Exception("Failed to receive acknowledgment from server.")

        # Nhận phản hồi từ server
        response = client_socket.recv(1024).decode()
        if response == "NOT FOUND":
            print(f"File '{file_name}' không tồn tại trên server.")
            return

        # Nhận kích thước file
        file_size = int(client_socket.recv(1024).decode())
        client_socket.send(b"OK")
        print(f"Đang tải file '{file_name}' kích thước {file_size} bytes...")

        # Tạo thư mục tải xuống nếu chưa tồn tại
        os.makedirs(CLIENT_FOLDER, exist_ok=True)
        file_path = os.path.join(CLIENT_FOLDER, get_unique_name(file_name, CLIENT_FOLDER, False))

        # Nhận dữ liệu file
        with open(file_path, "wb") as file:
            bytes_received = 0
            while bytes_received < file_size:
                chunk_data = client_socket.recv(CHUNK_SIZE)
                file.write(chunk_data)
                bytes_received += len(chunk_data)

                # Hiển thị tiến độ tải
                progress = (bytes_received / file_size) * 100
                print(f"Đã tải: {progress:.2f}%")

        # Gửi xác nhận đã nhận xong file
        client_socket.sendall(b"OK")
        finish_time = datetime.now().strftime("%H:%M:%S %d-%m-%Y")
        print(f"File '{file_name}' đã được tải thành công vào '{file_path}'.")
        print(f"Tổng cộng: {bytes_received} bytes lúc {finish_time}.")
    except Exception as e:
        print(f"Lỗi khi tải file: {e}")


def download_folder(client_socket, folder_name):
    """
    Nhận folder từ server dưới dạng file ZIP, giải nén và lưu vào thư mục chỉ định.
    """
    try:
        # Gửi yêu cầu folder đến server
        client_socket.sendall(folder_name.encode())
        print(f"Yêu cầu tải folder: {folder_name}")

        # Nhận phản hồi từ server
        response = client_socket.recv(1024).decode()
        if response == "NOT FOUND":
            print(f"Folder '{folder_name}' không tồn tại trên server.")
            return

        # Nhận kích thước file ZIP
        client_socket.send(b"OK")
        zip_size = int(client_socket.recv(1024).decode())
        client_socket.send(b"OK")
        print(f"Đang tải folder '{folder_name}' dưới dạng file ZIP kích thước {zip_size} bytes...")

        # Tạo thư mục tải xuống nếu chưa tồn tại
        os.makedirs(CLIENT_FOLDER, exist_ok=True)
        zip_path = os.path.join(CLIENT_FOLDER, f"{folder_name}.zip")

        # Nhận dữ liệu file ZIP
        with open(zip_path, "wb") as zip_file:
            bytes_received = 0
            while bytes_received < zip_size:
                chunk_data = client_socket.recv(CHUNK_SIZE)
                zip_file.write(chunk_data)
                bytes_received += len(chunk_data)

                # Hiển thị tiến độ tải
                progress = (bytes_received / zip_size) * 100
                print(f"Đã tải: {progress:.2f}%")

        # Gửi xác nhận đã nhận xong file ZIP
        client_socket.sendall(b"OK")
        print(f"File ZIP của folder '{folder_name}' đã được tải thành công vào '{zip_path}'.")

        # Giải nén file ZIP
        extract_folder_name = get_unique_name(folder_name, CLIENT_FOLDER, is_folder=True)
        extract_folder_path = os.path.join(CLIENT_FOLDER, extract_folder_name)
        os.makedirs(extract_folder_path, exist_ok=True)

        with zipfile.ZipFile(zip_path, 'r') as zipf:
            zipf.extractall(extract_folder_path)

        # Xóa file ZIP sau khi giải nén
        os.remove(zip_path)
        finish_time = datetime.now().strftime("%H:%M:%S %d-%m-%Y")
        print(f"Folder '{folder_name}' đã được tải và giải nén vào '{extract_folder_path}'.")
        print(f"Tổng cộng: {zip_size} bytes lúc {finish_time}.")
    except Exception as e:
        print(f"Lỗi khi tải folder: {e}")
            
#Triet
def uploadFile(fileName, conn):
    #defination that file is in client folder
    filePath = os.path.join(CLIENT_FOLDER,fileName)

    #check that file is exist
    if not os.path.isfile(filePath):
        print(f"Error: The file {fileName} does not exist.")
        return 

    msg = f"UPLOAD|FILE|{SERVER}|{PORT}"
    conn.send(msg.encode(FORMAT))
    time.sleep(0.01)
    print(f"Send request upload file: {msg}")

    #send file name and file size
    parts = fileName.split("/")
    if(len(parts) > 1):
        fileNameSv = parts[len(parts)-1]
    else:
        fileNameSv = fileName
    fileSize = os.path.getsize(filePath)
    conn.send(f"{fileNameSv}|{fileSize}".encode(FORMAT))
    time.sleep(0.01)
    print(f"Send file {fileName} ({fileSize} Bytes) to server")

    cmd = conn.recv(SIZE).decode(FORMAT)
    if(cmd == "OK"):
        #send file script
        with open(filePath, "rb") as file:
            size = 0
            while chunk:= file.read(SIZE):
                conn.send(chunk)
                size+= len(chunk)
                if(size >= fileSize):
                    break
        

        msg = conn.recv(SIZE).decode(FORMAT)
        print(f"[SERVER] {msg}")
    else:
        print(f"[SERVER] Not accept request.")
        return

def uploadFolder(folderName, conn):
    #defination folder path
    folderPath = os.path.join(CLIENT_FOLDER, folderName)

    #check folder is exists
    if not os.path.isdir(folderPath):
        print(f"Error: The folder {folderName} does not exists.")
        return
    
    #send folder name and signal this is folder to server
    msg = f"UPLOAD|FOLDER|{SERVER}|{PORT}"
    conn.send(msg.encode(FORMAT))
    print(f"Send request upload folder: {msg} to server.")
    time.sleep(0.01)

    cmd = conn.recv(SIZE).decode(FORMAT)
    if(cmd == "Ok"):
        conn.send(folderName.encode(FORMAT))
        time.sleep(0.01)
        msg = conn.recv(SIZE).decode(FORMAT)
        print(msg)

    items = os.listdir(folderPath)
    for item in items:
        itemPath = os.path.join(folderPath,item)
        if os.path.isdir(itemPath):
           uploadFolder(f"{folderName}/{item}", conn)
        if os.path.isfile(itemPath):
            uploadFile(f"{folderName}/{item}",conn)
    conn.send("END FOLDER".encode(FORMAT))
    time.sleep(0.01)
    msg = conn.recv(SIZE).decode(FORMAT)
    print(f"[SERVER]: {msg}")

def login():
    success = False
    while not success:
        PIN = random.randint(1000,9999)
        print(f"CAPCHA: {PIN}")
        user = input("Input pin: ")
        if(int(user) == PIN):
            success = True
        else:
            print("Error: The pin is not valid")

def handle():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(ADDR) 
    try:
            while True:
                #Format upload messsage: request (upload) + filename/foldername or quit. Server doesn't respond for another message
                    #Format download message: request (download/ download_folder) + filename/foldername or quit
                    request = input("Input message: ").strip()
                    if (request == "quit"):
                        msg = f"QUIT|{SERVER}|{PORT}"
                        client.send(msg.encode(FORMAT))
                        client.close()
                        print("Connection closed.")
                        break
                    #if request is upload or download file
                    cmd = request.split(" ")
                    if(cmd[0] == "upload"):
                        if(os.path.isdir(os.path.join(CLIENT_FOLDER,cmd[1]))):
                            uploadFolder(cmd[1], client)
                        elif(os.path.isfile(os.path.join(CLIENT_FOLDER,cmd[1]))):
                            uploadFile(cmd[1], client)
                    elif(cmd[0] == "download "):   #có dấu space
                        #Request to download file
                        filename = command.split(" ", 1)[1]
                        download_file(client_socket, filename)
                    #Not yet
                    elif(cmd[0] == "download_folder "):
                        folder_name = command.split(" ", 1)[1]
                        download_folder(client_socket, folder_name)
                    else:
                        # Nhận phản hồi từ server
                        response = client_socket.recv(1024).decode()
                        print(f"Server: {response}")
        except Exception as e:
                print(f"Lỗi khi giao tiếp với server: {e}")
        
handle()
