import socket
import os
import random
import time
import pandas as pd
from tkinter import *
from tkinter import filedialog, simpledialog, ttk
import zipfile
from datetime import datetime

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
def uploadFile(file_name, conn):
    #tạo 1 đường dẫn tới file cần upload từ thư mục gốc
    file_path = os.path.join(CLIENT_FOLDER,file_name)

    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File {file_name} does not exist.")
    except FileNotFoundError as e:
        print(f"Exception caught: {e}")
        return

    #khi tìm thấy file, đóng gói tín hiệu cần upload file lên cho server
    file_size = os.path.getsize(file_path) #lấy kích thước của file
    msg = f"UPLOAD|FILE|{file_size}|{SERVER}|{PORT}"
    conn.send(msg.encode(FORMAT))
    time.sleep(0.01)

    #gửi tên file và kích thước file cần upload
    file_name_server = os.path.basename(file_name) #lấy tên file, do file_name có thể là 1 đường dẫn
    conn.send(f"{file_name_server}|{file_size}".encode(FORMAT))
    time.sleep(0.01)

    try:
        response = conn.recv(SIZE).decode(FORMAT)
        if(response != "OK"): #nếu yêu cầu gửi không được đồng ý
            raise ValueError("Upload request has refuse by server")
        
        #nếu được sẽ thực hiện gửi file theo dạng gửi từng chunk
        with open(file_path, "rb") as file:
            bytes_sent = 0
            while chunk:= file.read(SIZE):
                conn.send(chunk)
                bytes_sent+= len(chunk)
                if(bytes_sent >= file_size):
                    break
        
        msg = conn.recv(SIZE).decode(FORMAT)
        print(f"[SERVER] {msg}")
    except ValueError as e:
        print(f"Server response error: {e}")
        return
    except ConnectionError as e: #lỗi do kết nối trong quá trình truyền file
        print(f"Connection error during file upload: {e}")
        return
    except IOError as e: #lỗi khi không thể đọc được file do không có quyền truy cập hay gì đó
        print(f"File I/O error: {e}")
        return
    except Exception as e: #Các lỗi không mong đợi khác
        print(f"Unexpected error: {e}")
        return

#gửi folder theo cách gửi tuần tự từng tập tin
def uploadFolder(folder_name, conn):
    #tạo 1 đường dẫn đến thư mục cần upload
    folder_path = os.path.join(CLIENT_FOLDER, folder_name)

    #kiểm tra nó có tồn tại hay không
    try:
        if not os.path.exists(folder_path):
            raise FileNotFoundError(f"Folder {folder_name} does not exist.")
    except FileNotFoundError as e: #nếu folder không tồn tại thì return để người dùng nhập lại
        print(f"Exception caught: {e}.")
        return
    
    #gửi tín hiệu upload folder và tên,kích thước folder cho server
    folder_size = os.path.getsize(folder_path)
    msg = f"UPLOAD|FOLDER|{folder_size}|{SERVER}|{PORT}"
    conn.send(msg.encode(FORMAT))

    #nhận phản hồi từ server xem có đồng ý yêu cầu upload hay không
    try:
        response = conn.recv(SIZE).decode(FORMAT)
        if(response != "Ok"):
            raise ValueError("Server has refuse upload folder.")
        
        #trường hợp server OK yêu cầu upload folder
        conn.send(folder_name.encode(FORMAT)) #client gửi tên folder

    except ValueError as e:
        print(f"Exception error: {e}.")
        print(f"[SERVER] {response}.")
        return
    except Exception as e:
        print(f"Unexpected error: {e}.")

    #liệt kê tất cả các file và các folder con trong folder cần gửi
    try:
        items = os.listdir(folder_path)
    except OSError as e:
        print(f"Error ascending folder {folder_name}: {e}")
        conn.send(f"[CLIENT] Error ascending folder {folder_name}: {e}.".encode(FORMAT))
        return
    
    for item in items:
        try:
            item_path = os.path.join(folder_path, item)
            if os.path.isdir(item_path):
                uploadFolder(f"{folder_name}/{item}", conn)
            elif os.path.isfile(item_path):
                uploadFile(f"{folder_name}/{item}", conn)
        except OSError as e:
            print(f"Error processing item {item} in folder {folder_path}: {e}")
            conn.send(f"[SERVER]: Error processing item {item}.".encode(FORMAT))
            continue  # Tiếp tục xử lý các item khác

    conn.send("END FOLDER".encode(FORMAT))
    time.sleep(0.01)

    msg = conn.recv(SIZE).decode(FORMAT)
    print(f"[SERVER] {msg}")

def upload(fpath, connection):
    if not os.path.exists(os.path.join(CLIENT_FOLDER,fpath)):
        print(f"[CLIENT] Error: File/Folder does not exists.")
        return

    #trường hợp file.folder cần upload có tồn tại
    if os.path.isdir(os.path.join(CLIENT_FOLDER,fpath)):
        uploadFolder(fpath, connection)
    elif os.path.isfile(os.path.join(CLIENT_FOLDER,fpath)):
        uploadFile(fpath, connection)

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
                    if(cmd[0].lower() == "upload"):
                        upload(cmd[1],client)
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
