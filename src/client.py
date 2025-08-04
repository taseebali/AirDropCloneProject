import socket
import os
import threading
import struct
from tqdm import tqdm
from utils.crypto import encrypt_file, get_key
from utils.file_utils import get_file_size

TCP_PORT = 50001
BUFFER_SIZE = 4096
def file_sender(peer_ip, file_path):
    """Connects to a peer and sends a file."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((peer_ip, TCP_PORT))
            print(f"[+] Connected to {peer_ip}")

            file_name = os.path.basename(file_path)
            file_size = get_file_size(file_path)

            # Send file name length and name
            name_bytes = file_name.encode('utf-8')
            s.send(struct.pack('!I', len(name_bytes)))
            s.send(name_bytes)
            
            # Send file size
            s.send(struct.pack('!Q', file_size))

            # Encrypt the file first
            key = get_key()
            encrypted_data, nonce, tag = encrypt_file(file_path, key)

            # Send encryption data
            s.sendall(nonce)
            s.sendall(tag)

            with tqdm(total=len(encrypted_data), unit='B', unit_scale=True, desc=file_name) as progress:
                for i in range(0, len(encrypted_data), BUFFER_SIZE):
                    chunk = encrypted_data[i:i+BUFFER_SIZE]
                    s.sendall(chunk)
                    progress.update(len(chunk))

            print(f"\n[+] File '{file_name}' sent successfully.")

        except ConnectionRefusedError:
            print(f"[-] Connection to {peer_ip} refused. Make sure the receiver is running.")
        except Exception as e:
            print(f"[-] An error occurred: {e}")


def chat_client(peer_ip, chat_port=50002):
    """Connects to a peer for chat and returns the socket object."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.connect((peer_ip, chat_port))
        return s
    except Exception as e:
        print(f"[-] Chat client error: {e}")
        raise
