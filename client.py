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

socket_lock = threading.Lock() # Da Luong

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

def merge_chunks(chunks, output_file): # Merge the chunks into a single output file
    with open(output_file, 'wb') as out_file:
        for chunk_file in chunks:
            with open(chunk_file, 'rb') as chunk:
                out_file.write(chunk.read())
            os.remove(chunk_file)

def download_file(client_socket, file_path,download_folder_path):
    """
    Yêu cầu server gửi file và lưu file vào thư mục Downloads. 
    Nếu trùng tên file, hỏi người dùng có muốn tải không.
    """
    try:
        #Send filename
        file_path=os.path.basename(file_path)
        client_socket.sendall(file_path.encode())
        print(f"Send filename to server: {file_path.encode()}")
        # ACK for receving file name
        ack = client_socket.recv(1024).decode().strip()
        if ack != "OK":
            raise Exception("Failed to receive acknowledgment from server.")
            
        # Receive the number of chunks
        num_chunks = int(client_socket.recv(1024).decode())
        print(f"Num of chunks: {num_chunks}")
            
        # Open dialog to choose destination of download folder 
        if not download_folder_path:
            print("No download folder selected.")
            return
            
        # Init list to store chunk paths and threads
        chunk_paths = []
        threads = []
        for _ in range(num_chunks):
            thread = threading.Thread(target = download_chunk, args = (file_path, client_socket, chunk_paths, num_chunks, download_folder_path, socket_lock))
            threads.append(thread)
            thread.start()
                
        for thread in threads:
            thread.join()
                
        # Merge chunks if all were downloaded successfully
        if None not in chunk_paths:
            output_file = os.path.join(download_folder_path, os.path.basename(get_unique_name(file_path, download_folder_path,False))) # ensure the file names are unique
            merge_chunks(chunk_paths, output_file)
                
            client_socket.send('OK'.encode())
            print(f"File {file_path} downloaded successfully.")
    except socket.error as E:
        print(f"Socket error: {E}")
    except Exception as E:
        print(f"Error: {E}")

def download_chunk(file_path, client_socket, chunk_paths, num_chunks, download_folder_path,socket_lock):
    try:
        with socket_lock:
            # Receive chunk info
            chunk_info = client_socket.recv(1024).decode().strip()
            chunk_index, chunk_size = map(int, chunk_info.split(':'))
            # ACK for chunk info
            client_socket.send('OK'.encode()) 
            
            # Receive chunk data
            chunk_data = b''
            while len(chunk_data) < chunk_size:
                chunk_data += client_socket.recv(min(1024, chunk_size - len(chunk_data)))
                
            #  Save the chunk data to a file
            chunk_path = os.path.join(download_folder_path, f"{file_path}_chunk_{chunk_index}")
            with open(chunk_path, 'wb') as chunk_file:
                chunk_file.write(chunk_data)
                
            # ACK for chunk data
            client_socket.send('OK'.encode())
            print(f"Received chunk_{chunk_index} size: {chunk_size} ({chunk_index + 1}/{num_chunks})")
            chunk_paths.append(chunk_path)
    except Exception as e:
        print(f"Error downloading file {file_path}: {e}")


def download_folder(client_socket, folder_name):
    """
    Yêu cầu server gửi folder và lưu folder vào thư mục Downloads bằng cách sử dụng kỹ thuật đa luồng.
    """
    try:
        # Gửi tên folder đến server
        client_socket.sendall(folder_name.encode())
        print(f"Requested folder: {folder_name}")

        # Nhận phản hồi từ server
        response = client_socket.recv(1024).decode()
        if response == "FOUND":
            client_socket.sendall(b"OK")
            file_size = int(client_socket.recv(1024).decode())

            # Nhận số lượng chunk
            num_chunks = int(client_socket.recv(1024).decode())
            print(f"Receiving folder '{folder_name}' ({num_chunks} chunks)...")

            # Tạo thư mục tạm để lưu chunk
            #temp_folder = os.path.join(DOWNLOAD_FOLDER, f"{folder_name}_temp")
            #os.makedirs(temp_folder, exist_ok=True)

            # Danh sách lưu đường dẫn các chunk
            chunk_paths = []
            threads = []

            # Tải từng chunk bằng đa luồng
            for _ in range(num_chunks):
                thread = threading.Thread(
                    target=download_chunk,
                    args=(
                        folder_name,  # Tên file ZIP tạm
                        client_socket,
                        chunk_paths,
                        num_chunks,
                        CLIENT_FOLDER,
                        socket_lock,
                    ),
                )
                threads.append(thread)
                thread.start()

            # Đợi tất cả các luồng hoàn thành
            for thread in threads:
                thread.join()

            # Kiểm tra nếu tất cả các chunk đã được tải thành công
            if None not in chunk_paths:
                # Ghép các chunk thành file ZIP
                zip_path = os.path.join(CLIENT_FOLDER, f"{folder_name}.zip")
                merge_chunks(chunk_paths, zip_path)

                # Giải nén file ZIP
                folder_name=get_unique_name(folder_name,CLIENT_FOLDER,is_folder=True)
                extract_folder = os.path.join(CLIENT_FOLDER, folder_name)
                os.makedirs(extract_folder, exist_ok=True)

                with zipfile.ZipFile(zip_path, 'r') as zipf:
                    zipf.extractall(extract_folder)

                # Xóa file ZIP sau khi giải nén
                os.remove(zip_path)
                print(f"Folder '{folder_name}' has been downloaded and extracted to '{CLIENT_FOLDER}'.")
                client_socket.sendall(b"OK")  # Gửi ACK xác nhận đã tải xong
            else:
                print(f"Error: Not all chunks for folder '{folder_name}' were downloaded.")
        else:
            print(f"Folder '{folder_name}' not found on server.")
    except Exception as e:
        print(f"Error downloading folder: {e}")
            
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
                    elif(cmd[0] == "download "):
                        #Request to download file
                        filename = command.split(" ", 1)[1]
                        download_file(client_socket, filename,CLIENT_FOLDER)
                    #Not yet
                    elif(cmd[0] == "download_folder"):
                        folder_name = command.split(" ", 1)[1]
                        download_folder(client_socket, folder_name)
                    else:
                        # Nhận phản hồi từ server
                        response = client_socket.recv(1024).decode()
                        print(f"Server: {response}")
        except Exception as e:
                print(f"Lỗi khi giao tiếp với server: {e}")
        
handle()
