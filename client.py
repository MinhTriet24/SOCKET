import socket
import os
import random
import time

FORMAT ='utf-8'
SERVER = input("Server HOST: ")
if not SERVER:
        SERVER = '127.0.0.1'
PORT = 50505
ADDR = (SERVER, PORT)
CLIENT_FOLDER = "client_folder"
SIZE = 1024


# Tuan
def get_unique_filename(directory, filename):       
    """
    Trả về tên file duy nhất trong thư mục bằng cách thêm số thứ tự nếu file đã tồn tại.
    """
    base, ext = os.path.splitext(filename)  # Tách phần tên và đuôi file
    unique_filename = filename
    count = 1

    while os.path.exists(os.path.join(directory, unique_filename)):
        unique_filename = f"{base}({count}){ext}"
        count += 1

    return unique_filename

#Tuan
def download_file(client, filename):
    """
    Yêu cầu server gửi file và lưu file vào thư mục Downloads. 
    Nếu trùng tên file, hỏi người dùng có muốn tải không.
    """
    try:
        # Gửi yêu cầu tải file
        client.sendall(f"download {filename}".encode())

        # Nhận phản hồi từ server
        response = client.recv(SIZE).decode(FORMAT, errors="replace")
        if response.startswith("SUCCESS"):
            file_size = int(response.split("|")[1])  # Lấy kích thước file từ phản hồi

            # Lấy đường dẫn thư mục Downloads
            download_dir = os.path.join(os.path.expanduser("~"), "Downloads")
            if not os.path.exists(download_dir):
                os.makedirs(download_dir)  # Tạo thư mục nếu chưa tồn tại

            
            # Xử lý kiểm tra tên file
            filepath = os.path.join(download_dir, os.path.basename(filename))
            if os.path.exists(filepath):
                # Hỏi người dùng nếu file đã tồn tại
                user_response = input(f"File '{filename}' đã tồn tại. Bạn có muốn tải lại không? (yes/no): ").strip().lower()
                if user_response != 'yes':
                    print("Hủy yêu cầu tải file.")
                    return
                
                # Nếu người dùng muốn lưu lại với tên khác
                filepath = get_unique_filename(download_dir, filename)

            # Lưu file
            with open(filepath, "wb") as file:
                total_received = 0
                while total_received < file_size:
                    data = client.recv(1024)
                    #if data == b"END":
                    #    break
                    total_received += len(data)
                    file.write(data)

            print(f"Đã tải file '{filepath}' thành công vào thư mục {download_dir}.")
        else:
            print(response)  # Hiển thị lỗi từ server
    except Exception as e:
        print(f"Lỗi khi tải file: {e}")

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
            elif(cmd[0] == "download"):
                #Request to download file
                filename = request.split(" ", 1)[1]
                download_file(client, filename)
            #Not yet
            #elif(cmd[0] == "download_folder"):
                #foldername = request.split(" ",1)[1]
                #download_folder(client, foldername)
handle()