import socket
import threading
import os
from tkinter import *
from tkinter import filedialog, messagebox, simpledialog, scrolledtext
import random
import zipfile
from datetime import datetime
import os
import shutil
from tkinter import Toplevel, Listbox, Button, messagebox
from tkinter import ttk
from tkinter import filedialog, messagebox, END
import time
from tkinter import scrolledtext,Label

FORMAT = 'utf-8'
SERVER = None
PORT = 50505
ADDR = (SERVER, PORT)
SIZE = 1024
CLIENT_FOLDER = "client_folder"
SERVER_FOLDER = "server_folder"
CHUNK_SIZE = 1024*1024
connected=False
#client_socket = None

def login():
    """
    Hiển thị giao diện đăng nhập với mã CAPTCHA
    """
    
    def verify_captcha():
        user_captcha = int(entry_captcha.get())
        
        if user_captcha == captcha_code:
            login_window.destroy()

        else:
            messagebox.showerror("Error", "Incorrect CAPTCHA")

    login_window = Tk()
    login_window.title("Login")
    login_window.geometry("300x150")
    login_window.resizable(False, False)

    # Tạo mã CAPTCHA
    captcha_code = random.randint(1000, 9999)

    Label(login_window, text="Enter the CAPTCHA code:").pack(pady=10)
    Label(login_window, text=str(captcha_code), font=("Arial", 16, "bold")).pack(pady=5)

    entry_captcha = Entry(login_window, width=10)
    entry_captcha.pack(pady=5)

    Button(login_window, text="Submit", command=verify_captcha).pack(pady=10)
    
    login_window.mainloop()
def on_close():
    """Hàm được gọi khi cửa sổ chính được đóng."""
    global connected
    if connected:
        disconnect_from_server()
    root.destroy()  # Hủy cửa sổ chính
def main():
    login()

    # Giao diện chính
    global root
    root = Tk()
    root.title("Client Application")
    root.geometry("600x500")  # Tăng chiều cao để chứa thêm thanh tiến trình

    # Liên kết sự kiện khi cửa sổ được đóng
    root.protocol("WM_DELETE_WINDOW", on_close)

    # IP và trạng thái kết nối
    frame_top = Frame(root)
    frame_top.pack(pady=10)

    Label(frame_top, text="Server IP:").pack(side=LEFT, padx=5)
    global entry_ip
    entry_ip = Entry(frame_top, width=20)
    entry_ip.pack(side=LEFT, padx=5)

    Button(frame_top, text="Connect", command=connect_to_server, bg="#2ecc71", fg="white").pack(side=LEFT, padx=5)
    Button(frame_top, text="Disconnect", command=disconnect_from_server, bg="#e74c3c", fg="white").pack(side=LEFT, padx=5)

    global lbl_status
    lbl_status = Label(frame_top, text="Not connected", fg="red")
    lbl_status.pack(side=LEFT, padx=10)

    # Nút tải file
    frame_actions = Frame(root)
    frame_actions.pack(pady=10)

    Button(frame_actions, text="Download File", command=choose_and_download_file, bg="#3498db", fg="white").pack(side=LEFT, padx=10)
    Button(frame_actions, text="Download Folder", command=choose_and_download_folder, bg="#3498db", fg="white").pack(side=LEFT, padx=10)
    Button(frame_actions, text="Upload File", command=choose_and_upload_file, bg="#9b59b6", fg="white").pack(side=LEFT, padx=10)
    Button(frame_actions, text="Upload Folder", command=choose_and_upload_folder, bg="#9b59b6", fg="white").pack(side=LEFT, padx=10)

    # Khung chat
    global txt_chat
    txt_chat = scrolledtext.ScrolledText(root, height=15, width=70)
    txt_chat.pack(pady=10)

    # Thanh tiến trình và nhãn trạng thái (ẩn mặc định)
    global progress_bar, lbl_progress_status
    progress_frame = Frame(root)
    progress_frame.pack(pady=10)

    lbl_progress_status = Label(progress_frame, text="", fg="blue")
    lbl_progress_status.pack(pady=5)

    progress_bar = ttk.Progressbar(progress_frame, orient="horizontal", length=400, mode="determinate")
    progress_bar.pack(pady=5)

    progress_frame.pack_forget()   # Ẩn khung tiến trình

    # Gửi tin nhắn
    frame_chat = Frame(root)
    frame_chat.pack(pady=10)
    global txt_message
    txt_message = Entry(frame_chat, width=60)
    txt_message.pack(side=LEFT, padx=10)

    Button(frame_chat, text="Send", command=send_message, bg="#f1c40f", fg="black").pack(side=LEFT, padx=5)

    root.mainloop()



"""
OS
"""
def free_bytes():
    total, used, free = shutil.disk_usage("/")
    return free
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
def is_valid(fpath):
   #xử lí các lỗi ngoại lệ khi client nhận được 1 yêu cầu upload file nào đó
    try: 
        max_length = 260 #set up chiều dài tối đa cho đường dẫn mà hệ thống có thể truy cập  
        fpath = os.path.join(CLIENT_FOLDER, fpath) #tạo đường dẫn trong thư mục
        #tạo một ngoại lệ khi không tìm thấy file/folder
        
        if not os.path.exists(fpath):
            raise FileNotFoundError("[CLIENT] Error: This file/folder does not exists.")
        #tạo một ngoại lệ khi không có quyền truy cập file/folder
        if not os.access(fpath, os.W_OK):
            raise IOError("[CLIENT] Error: This file/folder can not access.")
        #tạo một ngoại lệ khi chiều dài đường dẫn người dùng nhập quá dài
        if len(fpath) > max_length:
            raise OSError(f"[CLIENT] Error: The file/folder path is too long.")
        
        return True

    except FileExistsError as e:
        update_chat(f"{e}")
        return False
    except IOError as e:
        update_chat(f"{e}")
        return False
    except OSError as e:
        update_chat(f"{e}")
        return False
    except Exception as e:
        update_chat(f"[CLIENT] Error: {e}")
        return False
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
def send_chunk(file_path, file_size, connection, is_display_progress_bar = False):
    connection.settimeout(10)
    update_chat("Start send chnk")
    # Khởi tạo thanh tiến trình
    progress_bar.master.pack(pady=10)
    progress_bar["value"] = 0  # Đặt lại giá trị
    progress_bar["maximum"] = file_size
    lbl_progress_status.config(text="Starting Upload...")
    progress_bar.update_idletasks()

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
                    return 
                
                """
                Tại sao lại có 2 dòng này ???
                """
                if is_display_progress_bar == True:
                    progress_bar["value"] = bytes_sent
                    thread_safe_update_progress(bytes_sent, file_size)
                
    except TimeoutError as e:
        update_chat(f"[CLIENT] Error: Timeout")
        return
    except ConnectionError as e:
        update_chat(e)
        return
    except Exception as e:
        update_chat(f"[CLIENT] {e}")
        return
    finally:
        connection.settimeout(None)
def receive_chunk(file_path, file_size, connection, is_display_progress_bar = False):
    connection.settimeout(10)
    # Khởi tạo thanh tiến trình
    progress_bar.master.pack(pady=10)
    progress_bar["value"] = 0  # Đặt lại giá trị
    progress_bar["maximum"] = file_size
    lbl_progress_status.config(text="Starting Upload...")
    progress_bar.update_idletasks()
    
    try:
        with open(file_path, "wb") as file:
            bytes_received = 0
            while bytes_received < file_size:

                offset_data = connection.recv(CHUNK_SIZE + 50) #50 là dự phòng cho offset
                if not offset_data:
                    connection.sendall("[SERVER] Error: Connection lost while receiving data.".encode(FORMAT))
                    raise ConnectionError(f"[CLIENT] Error: Connection lost while receiving data.")
                
                offset, chunk_data = offset_data.split(b"|",1)
                offset = int(offset)
                bytes_received += len(chunk_data)
                file.write(chunk_data)

                if offset != bytes_received:
                    file.truncate(bytes_received-len(chunk_data))
                    bytes_received -= len(chunk_data)
                    
                connection.sendall(f"{bytes_received}".encode(FORMAT))

                #cập nhật thanh tiến trình
                if is_display_progress_bar == True:
                    progress_bar["value"] = bytes_received
                    thread_safe_update_progress(bytes_received, file_size)
                
                
        
        if bytes_received != file_size:
            raise EOFError(f"[CLIENT] Error: File transfer incomplete.")

        return bytes_received

    except TimeoutError as e:
        update_chat("Error: Timeout")
        return 0
    except ConnectionError as e:
        update_chat(e)
        os.remove(file_path)
        return 0
    except EOFError as e:
        update_chat(e)
        os.remove(file_path)
        return 0
    except Exception as e:
        update_chat(f"[SERVER] Error: {e}.")
        connection.sendall(f"[SERVER] Error: Unexpected error during receive data.".encode(FORMAT))
        return 0
    finally:
        connection.settimeout(None)

"""
Connect
"""
def connect_to_server():
    """
    Kết nối đến server từ địa chỉ IP nhập vào.
    """
    global client_socket, connected,SERVER
    try:
        ip_address = entry_ip.get().strip()
        if not ip_address:
            messagebox.showwarning("Warning", "Please enter server IP address!")
            return

        SERVER = ip_address
        ADDR = (SERVER, PORT)
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.settimeout(10)
        client_socket.connect(ADDR)
        connected = True
        update_status(f"Connected to server","green")
        update_chat("Connected to server")
    except Exception as e:
        update_chat(f"Failed to connect: {e}")
        return
    except TimeoutError as e:
        update_chat(f"[CLIENT] Error: Can not connect to server")
def disconnect_from_server():
    """
    Ngắt kết nối với server.
    """
    global client_socket, connected
    if connected:
        try:
            msg = f"QUIT|{SERVER}|{PORT}"
            client_socket.send(msg.encode(FORMAT))
            update_chat("Connection closed.")
            connected=False
            client_socket.close()
            update_status("Disconnected from server", "red")
        except Exception as e:
            update_status(f"Error during disconnection: {e}", "red")



"""
Display
"""
def update_status(message, color):
    """
    Cập nhật trạng thái trên giao diện.
    """
    lbl_status.config(text=message, fg=color)
def update_progress_bar(current, total):
    """Cập nhật thanh tiến trình."""
    progress = (current / total) * 100
    progress_bar["value"] = current
    progress_bar.update_idletasks()
    lbl_progress_status.config(text=f"Downloading: {progress:.2f}%")
    if current >= total:
        lbl_progress_status.config(text="Download complete!")
def thread_safe_update_progress(current, total):
    root.after(0, update_progress_bar, current, total)
def update_chat(message):
    txt_chat.config(state="normal")
    txt_chat.insert("end", f"{message}\n")
    txt_chat.see("end")
    txt_chat.config(state="disabled")



"""
Download file
"""
def choose_and_download_file():
    """
    Hiển thị hộp thoại chọn file giống Windows để người dùng chọn và tải về.
    """
    if not connected:
        messagebox.showwarning("Warning", "Not connected to server!")
        return

    try:
        # Mở hộp thoại chọn file
        file_path = filedialog.askopenfilename(
            initialdir=SERVER_FOLDER,  # Thư mục khởi tạo
            title="Choose File to Download",
            filetypes=(("All Files", "*.*"),)  # Lọc loại file (tất cả file ở đây)
        )
        if not file_path:  # Nếu người dùng đóng hộp thoại hoặc không chọn file
            return

        # Thực hiện tải file
        try:
            client_socket.send(f"DOWNLOAD|{file_path}".encode(FORMAT))
            update_chat(f"DOWNLOAD {file_path}")
            download_file_thread = threading.Thread(target=download_file, args=(client_socket, file_path))
            download_file_thread.start()
        except Exception as e:
            update_chat(f"Error downloading file: {e}")

    except Exception as e:
        update_chat(f"Error accessing server folder: {e}")
def download_file(client_socket, file_path):
    """
    Xử lý việc tải file từ server với thanh tiến trình.
    """
    global progress_bar, lbl_progress_status
    try:
        client_socket.settimeout(10)
        update_chat(f"Request to download file: '{file_path}' from server")
        file_name = os.path.basename(file_path)

        # Nhận phản hồi từ server
        response = client_socket.recv(1024).decode()
        if response == "NOT FOUND":
            update_chat(f"File '{file_path}' doesn't exist ")
            return

        # Nhận kích thước file
        file_size = int(client_socket.recv(SIZE).decode(FORMAT))
        client_socket.sendall("OK".encode(FORMAT))

        # Tạo thư mục lưu file
        os.makedirs(CLIENT_FOLDER, exist_ok=True)
        file_path_save = os.path.join(CLIENT_FOLDER, get_unique_name(file_name, CLIENT_FOLDER, False))
        bytes_received = receive_chunk(file_path_save, file_size, client_socket, is_display_progress_bar= True)
        if bytes_received == 0:
            raise ValueError(f"[CLIENT] Download file fail from server.")

        # Hoàn thành
        client_socket.sendall(b"OK")
        finish_time = datetime.now().strftime("%H:%M:%S %d-%m-%Y")
        update_chat(f"Downloaded '{file_name}' successfully and saved to '{file_path_save}'.")
        update_chat(f"Sum size {bytes_received} bytes at {finish_time}.")
        lbl_progress_status.config(text="Download complete!")
    
    except ValueError as e:
        update_chat(e)
        return
    except Exception as e:
        update_chat(f"Error during file download: {e}")
        lbl_progress_status.config(text="Error during download")
    finally:
        client_socket.settimeout(None)
        progress_bar.master.pack_forget()



"""
Download folder
"""
def choose_and_download_folder():
    """
    Hiển thị hộp thoại chọn folder giống Windows để người dùng chọn và tải về.
    """
    if not connected:
        messagebox.showwarning("Warning", "Not connected to server!")
        return

    try:
        # Mở hộp thoại chọn folder
        folder_path = filedialog.askdirectory(
            initialdir=SERVER_FOLDER,  # Thư mục khởi tạo
            title="Choose Folder to Download"
        )
        if not folder_path:  # Nếu người dùng đóng hộp thoại hoặc không chọn folder
            return

        # Tách tên folder từ đường dẫn
        #folder_name = os.path.basename(folder_path)

        # Thực hiện tải folder
        try:
            client_socket.send(f"DOWNLOAD|{folder_path}".encode(FORMAT))
            update_chat( f"DOWNLOAD {folder_path}")
            download_folder_thread = threading.Thread(target=download_folder, args=(client_socket, folder_path))
            download_folder_thread.start()  # Hàm tải folder từ server (tùy chỉnh)
        except Exception as e:
            update_chat(f"Error downloading folder: {e}")

    except Exception as e:
        update_chat(f"Error accessing server folder: {e}")
def download_folder(client_socket,folder_path):
    """
    Nhận và tải toàn bộ thư mục từ server.
    """
    global progress_bar, lbl_progress_status
    try:
        client_socket.settimeout(10)
        # Gửi tên folder đến server
        update_chat(f"Request downloading folder: {folder_path}")
        folder_name=os.path.basename(folder_path)
        response = client_socket.recv(SIZE).decode(FORMAT)
        if response == "NOT FOUND":
            update_chat("Error : ", f"Folder '{folder_path}' not found on server.")
            return

        # Nhận kích thước file ZIP
        client_socket.sendall(b"OK")
        zip_size = int(client_socket.recv(1024).decode())
        client_socket.sendall(b"OK")
        update_chat(f"Downloading folder '{folder_path}' dưới dạng file ZIP size {zip_size} bytes...")

         # Tạo thư mục tải xuống nếu chưa tồn tại
        os.makedirs(CLIENT_FOLDER, exist_ok=True)
        zip_path = os.path.join(CLIENT_FOLDER, f"{folder_name}.zip")       
        
        bytes_received = receive_chunk(zip_path, zip_size, client_socket, is_display_progress_bar= True)
        if bytes_received != zip_size:
            return

        # Gửi xác nhận đã nhận xong file ZIP
        client_socket.sendall(b"OK")
        update_chat(f"Downloaded file ZIP folder '{folder_name}' successfully at '{zip_path}'.")

        # Giải nén file ZIP
        extract_folder_name = get_unique_name(folder_name, CLIENT_FOLDER, is_folder=True)
        extract_folder_path = os.path.join(CLIENT_FOLDER, extract_folder_name)
        os.makedirs(extract_folder_path, exist_ok=True)

        with zipfile.ZipFile(zip_path, 'r') as zipf:
            zipf.extractall(extract_folder_path)

        # Xóa file ZIP sau khi giải nén
        os.remove(zip_path)
        finish_time = datetime.now().strftime("%H:%M:%S %d-%m-%Y")
        update_chat(f"Folder '{folder_path}' was downloaded and compressed to '{extract_folder_path}'.\n")
        update_chat(f"Sum size {zip_size} bytes at {finish_time}.")
    except Exception as e:
        update_chat(f"Eror: {e}")
    finally:
        client_socket.settimeout(None)
        progress_bar.master.pack_forget()



"""
Upload file
"""
def choose_and_upload_file():
    """
    Hiển thị hộp thoại chọn file giống Windows để người dùng chọn và tải về.
    """
    if not connected:
        messagebox.showwarning("Warning", "Not connected to server!\n")
        return

    try:
        # Mở hộp thoại chọn file
        file_path = filedialog.askopenfilename(
            initialdir="D:/",  # Thư mục khởi tạo
            title="Choose File to Download",
            filetypes=(("All Files", "*.*"),)  # Lọc loại file (tất cả file ở đây)
        )
        if not file_path:  # Nếu người dùng đóng hộp thoại hoặc không chọn file
            return

        # Tách tên file từ đường dẫn
        file_name = os.path.basename(file_path)

        # Thực hiện tải file
        try:
            update_chat(f"UPLOAD_FILE {file_name}")
            upload_file_thread = threading.Thread(target=upload_file, args=(client_socket, file_path))
            upload_file_thread.start()
        except Exception as e:
            update_chat(f"Error uploading file: {e}")

    except Exception as e:
        update_chat(f"Error accessing server folder: {e}")
def upload_file(connection, file_name):
    #kiểm tra tính hợp lệ của đường dẫn
    file_path = os.path.join(CLIENT_FOLDER,file_name)
    valid = is_valid(file_path)
    if not valid:
        return

    global progress_bar, lbl_progress_status

    file_size = os.path.getsize(file_path) #lấy kích thước của file
    msg = f"UPLOAD|FILE|{file_name}|{file_size}|{SERVER}|{PORT}"
    connection.send(msg.encode(FORMAT))

    try:
        response = connection.recv(SIZE).decode(FORMAT)
        if(response != "OK"): #nếu yêu cầu gửi không được đồng ý
            raise ValueError("Upload request has refuse by server")
        
        send_chunk(file_path, file_size, connection, is_display_progress_bar= True )
        
        msg = connection.recv(SIZE).decode(FORMAT)
        update_chat(f"{msg}")

    except ValueError as e:
        update_chat(f"Server response error: {e}")
        return
    finally:
        client_socket.settimeout(None)
        progress_bar.master.pack_forget()



"""
Upload fodler
"""
def choose_and_upload_folder():
    """
    Hiển thị hộp thoại chọn folder giống Windows để người dùng chọn và tải về.
    """
    if not connected:
        messagebox.showwarning("Warning", "Not connected to server!")
        return

    try:
        # Mở hộp thoại chọn folder
        folder_path = filedialog.askdirectory(
            initialdir="D:/",  # Thư mục khởi tạo
            title="Choose Folder to Download"
        )
        if not folder_path:  # Nếu người dùng đóng hộp thoại hoặc không chọn folder
            return

        # Tách tên folder từ đường dẫn
        folder_name = os.path.basename(folder_path)

        # Thực hiện tải folder
        try:
            update_chat(f"UPLOAD_FOLDER {folder_name}")
            upload_folder_thread = threading.Thread(target=upload_folder, args=(client_socket, folder_path))
            upload_folder_thread.start()
        except Exception as e:
            update_chat(f"Error uploading folder: {e}")

    except Exception as e:
        update_chat(f"Error accessing server folder: {e}")
def upload_folder(connection, folder_name):
    #tạo 1 đường dẫn đến thư mục cần upload
    folder_path = os.path.join(CLIENT_FOLDER, folder_name)
    valid = is_valid(folder_path)
    if not valid:
        return
    
    zip_name = f"{folder_name}.zip"
    zip_name = get_unique_name(zip_name,CLIENT_FOLDER, is_folder= False)
    zip_path = os.path.join(CLIENT_FOLDER, zip_name)
    zip_size = zip_folder(folder_path,zip_path)
    msg = f"UPLOAD|FOLDER|{folder_name}|{zip_size}|{SERVER}|{PORT}"
    connection.send(msg.encode(FORMAT))

    #nhận phản hồi từ server xem có đồng ý yêu cầu upload hay không
    try:
        response = connection.recv(SIZE).decode(FORMAT)
        update_chat(response)
        if(response != "OK"):
            raise ValueError(f"Server has refuse upload folder.")
        
        send_chunk(zip_path, zip_size, connection, is_display_progress_bar= True)
        if os.path.exists(zip_path):
            os.remove(zip_path)

        response = connection.recv(SIZE).decode(FORMAT)
        update_chat(f"{response}")

    except ValueError as e:
        update_chat(f"Exception error: {e}.")
        update_chat(f"[SERVER] {response}.")
        return
    except Exception as e:
        update_chat(f"Unexpected error during upload folder.")
    finally:
        if os.path.exists(zip_path):
            os.remove(zip_path)


"""
Run with CLI
"""
def receive_message():
    """
    Nhận tin nhắn từ server và hiển thị lên khung chat.
    """
    global connected
    while connected:
        try:
            message = client_socket.recv(1024).decode(FORMAT)
            if message=="QUIT":
                disconnect_from_server()
            elif message!="QUIT":
                update_chat( f"Server: {message}\n")
            else:
                break
        except Exception as e:
            update_status(f"Error receiving message: {e}", "red")
            break
def send_message():
    """
    Gửi tin nhắn tới server và hiển thị lên khung chat.
    """
    if not connected:
        messagebox.showwarning("Warning", "Not connected to server!")
        return

    message = txt_message.get().strip()
    if not message:
        return
    try:
        cmd=message.split(" ",1)
        if(cmd[0]=="QUIT"):
            disconnect_from_server()
        elif(cmd[0]=="UPLOAD"):
            if is_valid(cmd[1] == True):
                if os.path.isfile(cmd[1]):
                    upload_file(client_socket, cmd[1])
                elif os.path.isdir(cmd[1]):
                    upload_folder(client_socket, cmd[1])
        elif(cmd[0]=="DOWNLOAD"):
            download(cmd[1],client_socket)
        else:
            client_socket.send(message.encode(FORMAT))
            update_chat( f"CLIENT: {message}\n")
            txt_message.delete(0, END)  # Xóa nội dung trong Entry sau khi gửi
    except Exception as e:
        update_status(f"Error sending message: {e}", "red")
def download(fpath,client):
    try:
        size = os.path.getsize(fpath)
        store = free_bytes()
        if store < size:
            raise OSError("[CLIENT] Error: No space left on device.")
        client_socket.send(f"DOWNLOAD|{fpath}".encode(FORMAT))
        #trường hợp đủ dung lượng
        if os.path.isdir(os.path.join(fpath)):
            download_folder(client,fpath)
        elif os.path.isfile(os.path.join(fpath)):
            download_file(client,fpath)

    except OSError as e: #xử lý khi server hết dung lượng
        update_chat(f"OS Error: {e}")
        client.send("No space left on client.".encode(FORMAT))
        return
    except Exception as e:
        update_chat(f"Exception caught: {e}")


if __name__ == "__main__":
    main()
