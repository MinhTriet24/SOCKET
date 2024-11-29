import socket

FORMAT ='utf-8'
SERVER = input("Server HOST: ")
PORT = 50505
ADDR = (SERVER, PORT)

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

def download_file(client, filename):
    """
    Yêu cầu server gửi file và lưu file vào thư mục Downloads. 
    Nếu trùng tên file, hỏi người dùng có muốn tải không.
    """
    try:
        # Gửi yêu cầu tải file
        client.sendall(f"download {filename}".encode())

        # Nhận phản hồi từ server
        response = client.recv(1024).decode(FORMAT, errors="replace")
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



if not SERVER:
    SERVER = '127.0.0.1'

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(ADDR)


client.send("Hello World".encode(FORMAT))
message_recv = client.recv(2048).decode(FORMAT)
print(f"Server: {message_recv}")
input()
client.send("quit".encode(FORMAT))
