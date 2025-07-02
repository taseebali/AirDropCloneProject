import socket
import os
from tqdm import tqdm
from utils.crypto import decrypt_file, get_key, NONCE_SIZE, TAG_SIZE

TCP_PORT = 50001
BUFFER_SIZE = 4096

def file_receiver(save_path="."):
    """Listens for incoming file transfers and handles them."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(("", TCP_PORT))
        s.listen()
        print(f"[*] Listening for file transfers on port {TCP_PORT}")

        conn, addr = s.accept()
        with conn:
            print(f"[+] Connection from {addr}")

            # Receive file info
            file_info = conn.recv(1024).decode('utf-8')
            file_name, file_size_str = file_info.split("|")
            file_size = int(file_size_str)

            # Prompt user to accept or decline
            response = input(f"Incoming file: {file_name} ({file_size} bytes). Accept? (y/n): ")
            if response.lower() != 'y':
                conn.send(b"DECLINE")
                print("[-] File transfer declined.")
                return

            conn.send(b"ACCEPT")

            # Receive file data
            output_path = os.path.join(save_path, file_name)
            key = get_key()
            
            # Receive nonce and tag
            nonce = conn.recv(NONCE_SIZE)
            tag = conn.recv(TAG_SIZE)

            encrypted_data = b""
            with tqdm(total=file_size, unit='B', unit_scale=True, desc=file_name) as progress:
                while len(encrypted_data) < file_size:
                    chunk = conn.recv(BUFFER_SIZE)
                    if not chunk:
                        break
                    encrypted_data += chunk
                    progress.update(len(chunk))

            try:
                decrypt_file(encrypted_data, key, nonce, tag, output_path)
                print(f"\n[+] File '{file_name}' received and decrypted successfully.")
            except Exception as e:
                print(f"\n[-] Decryption failed: {e}")
