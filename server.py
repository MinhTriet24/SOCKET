import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import threading
import os
import socket
import logging
import zipfile
import shutil
from datetime import datetime
from PIL import Image, ImageTk

# Logging configuration
logging.basicConfig(level=logging.INFO, filename="log_server.txt", filemode="w",
                    format="%(asctime)s - %(message)s")
logger = logging.getLogger(__name__)

# Default accounts
ACCOUNTS = {
    "cqt": "cqt",
    "hlmt": "hlmt",
    "tntt": "tntt"
}

# Khởi tạo IP server là máy đang chạy file server.py
SERVER = socket.gethostbyname(socket.gethostname())
PORT = 50505
ADDR = (SERVER, PORT)
FORMAT = 'utf-8'
SERVER_FOLDER = "D:/server_folder"
CLIENT_FOLDER = "client_folder"
SIZE = 1024
CHUNK_SIZE = 1024*1024


server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)
logger.info("Create server successfully")

# Dictionary để lưu thông tin client
clients = {}

# Global variables
current_user = None
login_frame = None
main_frame = None
chat_log = None
message_entry = None
server_running = True
# def create_login_frame(root):
#     global login_frame
#     login_frame = tk.Frame(root)
#     login_frame.pack(fill="both", expand=True)

#     tk.Label(login_frame, text="Server Login", font=("Arial", 20)).pack(pady=20)
#     tk.Label(login_frame, text="Username:", font=("Arial", 12)).pack(pady=5)
#     username_entry = tk.Entry(login_frame, font=("Arial", 12))
#     username_entry.pack()

#     tk.Label(login_frame, text="Password:", font=("Arial", 12)).pack(pady=5)
#     password_entry = tk.Entry(login_frame, show="*", font=("Arial", 12))
#     password_entry.pack()

#     login_button = tk.Button(login_frame, text="Login", font=("Arial", 12),
#                              command=lambda: handle_login(username_entry, password_entry))
#     login_button.pack(pady=20)


def create_login_frame(root):
    global login_frame, background_image
    # Tạo frame login
    login_frame = tk.Frame(root)
    login_frame.pack(fill="both", expand=True)

    # Thêm ảnh nền
    try:
        background_image = tk.PhotoImage(file="C:\\Users\\MSI TUAN\\Downloads\\background.png")  # Đảm bảo đường dẫn chính xác
        bg_label = tk.Label(login_frame, image=background_image)
        bg_label.place(relwidth=1, relheight=1)  # Ảnh nền phủ toàn bộ giao diện
    except Exception as e:
        bg_label = None

        # Thêm container để đặt các widget
    content_frame = tk.Frame(login_frame, bg="#ecf0f1")  # Khung trong suốt, trên ảnh nền
    content_frame.place(relx=0.5, rely=0.5, anchor="center")  # Canh giữa

    # Thêm các widget lên trên ảnh nền
    tk.Label(login_frame, text="Server Login", font=("Arial", 30), bg="#ecf0f1", fg="#333333").pack(pady=20)
    tk.Label(login_frame, text="Username:", font=("Arial", 15), bg="#ecf0f1", fg="#333333").pack(pady=5)

    username_entry = tk.Entry(login_frame, font=("Arial", 15))
    username_entry.pack()

    tk.Label(login_frame, text="Password:", font=("Arial", 15), bg="#ecf0f1", fg="#333333").pack(pady=5)
    password_entry = tk.Entry(login_frame, show="*", font=("Arial", 15))
    password_entry.pack()

    login_button = tk.Button(
        login_frame, 
        text="Login", 
        font=("Arial", 12), 
        command=lambda: handle_login(username_entry, password_entry)
    )
    login_button.pack(pady=20)
def on_close():
    # Ngắt kết nối hoặc dừng server ở đây
    stop_server()
    root.destroy()  # Đóng cửa sổ chính
def create_main_frame(root):
    global main_frame, chat_log
    main_frame = tk.Frame(root)

    tk.Label(main_frame, text="Server Manager", font=("Arial", 20)).pack(pady=10)

    server_info_frame = tk.Frame(main_frame)
    server_info_frame.pack(pady=10)

    tk.Label(server_info_frame, text="Server IP:", font=("Arial", 12)).grid(row=0, column=0, padx=10)
    tk.Label(server_info_frame, text=SERVER, font=("Arial", 12)).grid(row=0, column=1, padx=10)

    tk.Label(server_info_frame, text="Port:", font=("Arial", 12)).grid(row=1, column=0, padx=10)
    tk.Label(server_info_frame, text=PORT, font=("Arial", 12)).grid(row=1, column=1, padx=10)

    control_frame = tk.Frame(main_frame)
    control_frame.pack(pady=10)

    start_button = tk.Button(
        control_frame,
        text="Start Server",
        font=("Arial", 12),
        command=start_server,
        bg="#2ecc71",
        fg="white"
    )
    start_button.grid(row=0, column=0, padx=10)

    stop_button = tk.Button(
        control_frame,
        text="Stop Server",
        font=("Arial", 12),
        command=stop_server,
        bg="#e74c3c",  # Đỏ
        fg="white"     # Chữ trắng
    )
    stop_button.grid(row=0, column=1, padx=10)

    log_button = tk.Button(
        control_frame,
        text="View Logs",
        font=("Arial", 12),
        command=view_logs,
        bg="#3498db",
        fg="white"
    )
    log_button.grid(row=2, column=0, columnspan=2, pady=10)

    chat_frame = tk.Frame(main_frame)
    chat_frame.pack(pady=10)

    tk.Label(chat_frame, text="Chat Box", font=("Arial", 12)).pack()
    chat_log = tk.Text(chat_frame, height=15, width=70, state="disabled", font=("Arial", 12))
    chat_log.pack(pady=10)

    # Gán hàm xử lý sự kiện cửa sổ đóng
    root.protocol("WM_DELETE_WINDOW", on_close)



"""
System
"""
def handle_login(username_entry, password_entry):
    global current_user
    username = username_entry.get()
    password = password_entry.get()

    if ACCOUNTS.get(username) == password:
        current_user = username
        logger.info(f"User {username} logged in.")
        login_frame.pack_forget()
        main_frame.pack(fill="both", expand=True)

    else:
        messagebox.showerror("Login Error", "Invalid username or password.")
def start_server():
    thread = threading.Thread(target=run_server)
    thread.start()
def run_server():
    server.listen()
    messagebox.showinfo("Server", "Server started successfully!")
    logger.info("Server started.")
    update_chat("Server started successfully!")

    while True:
        try:
            connection, address = server.accept()
            thread = threading.Thread(target=handle, args=(connection, address))
            logger.info(f"Create new thread for {address}")
            thread.start()
            update_chat(f"Active connections: {len(clients) + 1}")
        except socket.error:
            break 
def stop_server():
    global server_running
    if server_running:
        server_running = False  # Dừng server bằng cách thay đổi flag
        try:
            server.close()  # Đóng server socket
            logger.info("Server stopped.")
            update_chat("Server stopped successfully!")
            remove_clients()
            messagebox.showinfo("Server", "Server stopped successfully!")
        except:
            messagebox.showerror("Server Error", "Unable to stop the server.")
def view_logs():
    log_window = tk.Toplevel()
    log_window.title("Client Logs")
    log_window.geometry("500x400")

    log_text = tk.Text(log_window, wrap="word", font=("Arial", 12))
    log_text.pack(expand=True, fill="both")

    with open("log_server.txt", "r") as log_file:
        log_text.insert("1.0", log_file.read())
    log_text.config(state="disabled")
"""
def update_chat(message):
    global chat_log
    chat_log.config(state="normal")
    chat_log.insert("end", f"{message}\n")
    chat_log.see("end")
    chat_log.config(state="disabled")
"""
def update_chat(message):
    # Thực hiện cập nhật giao diện thông qua root.after
    if threading.current_thread() != threading.main_thread():
        root.after(0, _update_chat_ui, message)
    else:
        _update_chat_ui(message)

def _update_chat_ui(message):
    # Cập nhật giao diện
    chat_log.config(state="normal")
    chat_log.insert("end", message + "\n")
    chat_log.config(state="disabled")
    chat_log.see("end")
def remove_clients():
    """
    Gửi thông báo đến tất cả các client đang kết nối.
    """
    for client_socket in clients.keys():
        try:
            client_socket.send("QUIT".encode())
            del clients[client_socket]
        except Exception as e:
            messagebox.showerror("Error",f"Không thể gửi thông báo tới {client_socket}: {e}")



"""
Reuse
"""
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
def free_bytes():
    total, used, free = shutil.disk_usage("/")
    return free
def receive_chunk(file_path, file_size, connection, address):
    connection.settimeout(10)
    try:
        with open(file_path, "wb") as file:
            bytes_received = 0
            while bytes_received < file_size:

                offset_data = connection.recv(CHUNK_SIZE + 50) #50 là dự phòng cho offset
                if not offset_data:
                    connection.sendall("[SERVER] Error: Connection lost while receiving data.".encode(FORMAT))
                    raise ConnectionError(f"[CLIENT] Error: Connection lost while receiving data from {address}.")
                
                offset, chunk_data = offset_data.split(b"|",1)
                offset = int(offset)
                bytes_received += len(chunk_data)
                
                if offset != bytes_received:
                    file.truncate(bytes_received-len(chunk_data))
                    bytes_received = offset

                file.write(chunk_data)
                connection.sendall(f"{bytes_received}".encode(FORMAT))
        
        if bytes_received != file_size:
            os.remove(file_path)
            raise EOFError(f"[SERVER] Error: File transfer incomplete.")

        return bytes_received

    except ConnectionError as e:
        update_chat(e)
        logger.info(f"Connection lost while receiving file from {address}")
        os.remove(file_path)
        return 0
    except EOFError as e:
        update_chat(e)
        logger.info(f"{e}")
        os.remove(file_path)
        return 0
    except TimeoutError as e:
        update_chat(f"[SERVER] Error: Timeout.")
        logger.info(f"[SERVER] {e}")
        os.remove(file_path)
        return 0
    except Exception as e:
        update_chat(f"[SERVER] {e}.")
        logger.info(f"[SERVER] {e}")
        connection.sendall(f"[SERVER] Error: Unexpected error during receive data.".encode(FORMAT))
        return 0
    finally:
        connection.settimeout(None)
def send_chunk(file_path, file_size, connection, address):
    connection.settimeout(10)
    try:
        with open(file_path, "rb") as file:
            bytes_sent = 0
            retry_count = 0
            max_retry = 3
            while bytes_sent < file_size:
                chunk_data = file.read(CHUNK_SIZE)
                bytes_sent += len(chunk_data)
                offset_data = f"{bytes_sent}|".encode(FORMAT) +chunk_data
                connection.sendall(offset_data)

                """
                Giả sử server nhận không đủ gói tin
                """
                try:
                    ack = connection.recv(SIZE).decode(FORMAT)
                    if int(ack) != bytes_sent:
                        retry_count +=1
                        if(retry_count > max_retry):
                            raise ValueError(f"[CLIENT] Error: Maximum retries reached. Lost data during transfer.")
                        
                        bytes_sent -= len(chunk_data)
                        file.seek(bytes_sent)
                    else:
                        retry_count = 0
                except ValueError as e:
                    update_chat(e)
                    logger.info(e)
                    return
        
    except TimeoutError as e:
        update_chat(f"[SERVER] Error: Timeout")
        logger.info(f"[SERVER] Error: Timeout")
        return
    except ConnectionError as e:
        update_chat(e)
        logger.info(f"[SERVER] {e}")
        return
    except Exception as e:
        update_chat(f"[CLIENT] {e}")
        logger.info(f"[SERVER] {e}")
        return
    finally:
        connection.settimeout(None)



"""
Download
"""
def send_file(file_path, connection, address):
    """
    Gửi file từ server tới client theo từng chunk mà không cần lưu các chunk tạm thời.
    """
    try:
        logger.info(f"Sent respond: Found file from {address}")
        
        # Lấy kích thước file
        file_size = os.path.getsize(file_path)
        connection.sendall(f"{file_size}".encode())  # Gửi kích thước file
        ack = connection.recv(SIZE).decode().strip()  # Nhận ACK từ client
        logger.info(f"Received ACK from {address}")
        
        if ack != "OK":
            raise Exception("Client didn't consider size of file.")
        send_chunk(file_path, file_size, connection, address)

        # Nhận xác nhận từ client sau khi gửi xong
        file_name=os.path.basename(file_path)
        ack = connection.recv(10).decode().strip()
        if ack != "OK":
            logger.info(f"Failed sent file '{file_name} for {address} ")
            raise Exception("Client didn't consider enough size of file.")
        else:
            update_chat(f"Sent file '{file_name}' succesfully ")
            logger.info(f"Sent file '{file_name}' succesfully for {address} ")
    except FileNotFoundError as e:
        update_chat(f"Error: {str(e)}")
    except Exception as e:
        connection.sendall(b"NOT OK")
        update_chat(f"Eror {file_name}: {e}")
def send_folder(folder_path, connection, address):
    """
    Xử lý yêu cầu từ client và gửi folder dưới dạng file ZIP trực tiếp, không sử dụng đa luồng.
    """
    try:

        folder_name=os.path.basename(folder_path)
        logger.info(f"Received folder '{folder_path} successfully from {address}")

        if os.path.exists(folder_path) and os.path.isdir(folder_path):
            # Nén folder thành file zip
            zip_name = f"{folder_name}.zip"
            zip_path = os.path.join(SERVER_FOLDER, zip_name)
            zip_name = get_unique_name(zip_name, SERVER_FOLDER, is_folder=False)
            zip_size = zip_folder(folder_path, zip_path)
            logger.info(f"ZIP folder successfully for {address}")

            # Gửi thông báo rằng folder tồn tại
            connection.send(b"FOUND")
            logger.info(f"Found folder from {address}")
            ack = connection.recv(1024).decode().strip()
            if ack != "OK":
                logger.info(f"Didn't find folder from {address}")
                update_chat("Client didn't consider ZIP file was existed.")
                return

            # Gửi kích thước file ZIP
            connection.send(str(zip_size).encode())
            ack = connection.recv(1024).decode().strip()
            if ack != "OK":
                update_chat("Client didn't consider size of file.")
                return

            send_chunk(zip_path, zip_size, connection, address)

            # Nhận xác nhận từ client sau khi gửi xong
            ack = connection.recv(1024).decode().strip()
            if ack != "OK":
                update_chat("Client didn't consider to receive enough ZIP file.")
                return
            else:
                update_chat(f"Sent folder '{folder_path}' successfully")
                logger.info(f"Sent folder '{folder_path}' successfully")


            # Xóa file ZIP sau khi gửi
            if os.path.exists(zip_path):
                os.remove(zip_path)
                logger.info(f"Removed file ZIP folder from {address}")
        else:
            # Thông báo rằng folder không tồn tại
            connection.send(b"NOT FOUND")
            logger.info(f"Didn't find file ZIP folder from {address}")
    except Exception as e:
        update_chat(f"Eror: {e}")


"""
Upload
"""
def receive_file(file_name, file_size, connection, address):  
    logger.info(f"Receive file {file_name} ({file_size} from {address})")
    if not os.path.exists(SERVER_FOLDER):
        os.makedirs(SERVER_FOLDER, exist_ok= True)
    file_path = os.path.join(SERVER_FOLDER, get_unique_name(file_name, SERVER_FOLDER, False))

    #nhận các gói chunk và ghi vào file đã tạo
    receive_chunk(file_path, file_size, connection, address)
    connection.sendall(f"[SERVER] Upload success file {file_name} from {address}.".encode(FORMAT))
    update_chat(f"[SERVER] Upload success {file_name} from {address}")
    logger.info(f"[SERVER] Upload success {file_name} from {address}")
def receive_folder(folder_name, zip_size, connection, address):
    if not os.path.exists(SERVER_FOLDER):
        os.makedirs(SERVER_FOLDER, exist_ok= True)
    folder_path = os.path.join(SERVER_FOLDER, get_unique_name(folder_name, SERVER_FOLDER, is_folder=True))
    os.makedirs(folder_path, exist_ok=True)
    zip_path = os.path.join(SERVER_FOLDER, f"{folder_name}.zip")

    bytes_received = receive_chunk(zip_path, zip_size, connection, address)
    if bytes_received != zip_size:
        return

    connection.sendall(f"[SERVER] Upload success {folder_name}".encode(FORMAT))
    logger.info(f"[SERVER] Upload success {folder_name} from {address}")
    update_chat(f"[SERVER] Upload success {folder_name} from {address}")

    #giai nen folder
    with zipfile.ZipFile(zip_path,'r') as zipf:
        zipf.extractall(folder_path)

    #xoa file zip sau khi giai nen
    os.remove(zip_path)
def receive(type, fname, fsize, connection, address):
    try:
        store = free_bytes()
        if store < fsize:
            #thoát hàm và thông báo khi server hết bộ nhớ để lưu trữ
            raise OSError("[SERVER] Error: No space left on device.")
        
        #trường hợp đủ dung lượng
        connection.sendall("OK".encode(FORMAT))

        if type == "FILE": #khi client yêu cầu upload file
            receive_file(fname, fsize, connection, address)
            logger.info(f"Notify server ready for uploading file from {address}")
        elif type == "FOLDER": #khi client yêu cầu upload folder
            receive_folder(fname, fsize, connection, address)
            logger.info(f"Notify server ready for uploading folder from {address}")
        else:
            raise ValueError(f"[SERVER] Error: Receive invalid value.")

    except ValueError as e:
        update_chat(e)
        return
    except OSError as e: #xử lý khi server hết dung lượng
        update_chat(f"OS Error: {e}")
        connection.sendll(f"{e}".encode(FORMAT))
        return
    except Exception as e: #xử lí trường hợp không mong muốn khác
        update_chat(f"Exception caught: {e}")
        return

def handle(connection, address):
    # Thông báo client mới kết nối và thêm vào dictionary
        update_chat(f"New connection: {address} connected")
        logger.info(f"New connection: {address} connected")
        clients[address] = connection

        connected = True
        while True:
            try:
                msg = connection.recv(SIZE).decode(FORMAT)
                logger.info(f"Receive message from {address} : {msg}")
                update_chat(f"Receive message from {address} : {msg}")
                cmd = msg.split("|")
                if (cmd[0] == "QUIT"):
                    connected = False
                    break
                elif(cmd[0] == "UPLOAD"):
                    receive(cmd[1],cmd[2],int(cmd[3]),connection,address)
                elif(cmd[0] == "DOWNLOAD"):
                    if not os.path.exists(cmd[1]):
                        connection.sendall("NOT FOUND".encode())
                        logger.info(f"Sent respond: Didn't find file from {address}")
                        continue
                    else:
                        connection.sendall("FOUND".encode())
                    
                    if os.path.isdir(os.path.join(cmd[1])):
                        send_folder(cmd[1], connection,address)
                    elif os.path.isfile(os.path.join(cmd[1])):
                        send_file(cmd[1], connection,address)
                else:
                    update_chat(msg.decode())
            except Exception as e:
                update_chat(f"Error with client {address}: {e}")
                logger.info(f"Error with client {address}: {e}")
                connected = False
                break

        # Xóa client khỏi dictionary khi ngắt kết nối
        if connected == False:
            clients.pop(address, None)
            update_chat(f"Client {address} disconnected.")
            logger.info(f"Client {address} disconnected.")
            logger.info(f"Remove {address}")
        connection.close()        
    
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Server Application")
    root.geometry("800x600")
    root.resizable(False, False)

    create_login_frame(root)
    create_main_frame(root)

    root.mainloop()
