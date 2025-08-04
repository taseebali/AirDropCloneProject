import socket
import threading
import os
import struct
import tkinter as tk
from tkinter import filedialog
from utils.crypto import encrypt_file, decrypt_file, get_key

HOST = ''
PORT = 50001  # Default port

SAVE_PATH_FILE = os.path.expanduser("~/.pydrop_save_path.txt")
DEFAULT_SAVE_PATH = os.path.expanduser("~/Downloads")

def get_save_path():
    """Reads the current save path from the shared file or defaults."""
    if os.path.exists(SAVE_PATH_FILE):
        with open(SAVE_PATH_FILE, 'r') as f:
            path = f.read().strip()
            if os.path.isdir(path):
                return path
    return DEFAULT_SAVE_PATH

def set_save_path(path):
    """Sets and saves the new path to the shared file."""
    if os.path.isdir(path):
        with open(SAVE_PATH_FILE, 'w') as f:
            f.write(path)
        return True
    return False

def choose_save_location():
    """Opens a GUI dialog to choose the save directory."""
    root = tk.Tk()
    root.withdraw()
    path = filedialog.askdirectory(title="Choose Save Location")
    if path:
        set_save_path(path)
    return path

def save_file(path, data):
    """Writes decrypted file data to disk."""
    with open(path, 'wb') as f:
        f.write(data)

def file_receiver(port=PORT, save_path_func=None, on_file_received=None, on_transfer_request=None, on_transfer_progress=None, gui_root=None):
    """Listens for incoming encrypted files, decrypts them, and saves."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((HOST, port))
    sock.listen(5)
    print(f"[+] File receiver listening on port {port}")

    while True:
        conn, addr = sock.accept()
        threading.Thread(target=handle_file_transfer, args=(conn, addr, save_path_func, on_file_received, on_transfer_request, on_transfer_progress, gui_root), daemon=True).start()

def handle_file_transfer(conn, addr, save_path_func, on_file_received, on_transfer_request, on_transfer_progress, gui_root):
    try:
        print(f"[+] File transfer connection from {addr}")
        
        # Receive file info with proper length handling
        raw = conn.recv(4)
        if not raw:
            return
        name_len = struct.unpack('!I', raw)[0]
        file_name = conn.recv(name_len).decode()

        # Receive file size
        file_size = struct.unpack('!Q', conn.recv(8))[0]
        print(f"[+] Incoming file: {file_name} ({file_size} bytes)")

        # Receive encryption data
        nonce = conn.recv(16)
        tag = conn.recv(16)
        
        # Receive encrypted data with progress
        encrypted_data = b''
        remaining = file_size
        print("[+] Receiving encrypted data...")
        
        while remaining > 0:
            chunk = conn.recv(min(4096, remaining))
            if not chunk:
                print("[-] Connection closed unexpectedly")
                break
            encrypted_data += chunk
            remaining -= len(chunk)
            if on_transfer_progress:
                progress = (file_size - remaining) / file_size
                on_transfer_progress(progress)
            print(f"\rProgress: {(file_size - remaining) / file_size * 100:.1f}%", end="")

        if on_transfer_request:
            accepted = on_transfer_request(file_name, addr[0], file_size)
            if not accepted:
                print(f"[-] Transfer of '{file_name}' from {addr[0]} rejected.")
                return

        key = get_key()
        save_path = save_path_func() if save_path_func else get_save_path()
        full_path = os.path.join(save_path, file_name)
        
        # Decrypt file directly to the destination
        decrypt_file(encrypted_data, key, nonce, tag, full_path)

        print(f"[+] File '{file_name}' received successfully from {addr[0]} and saved to {full_path}")
        if on_file_received:
            on_file_received(file_name, addr[0])

    except Exception as e:
        print(f"[-] Error during file transfer from {addr}: {e}")
    finally:
        conn.close()

def chat_server(port=50002):
    """Starts a simple chat server for incoming peer messages."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        # For localhost testing, bind to specific address
        sock.bind(('0.0.0.0', port))
        sock.listen(1)
        print(f"[+] Chat server listening on port {port}")
        print("Waiting for incoming chat connection...")
        
        conn, addr = sock.accept()
        print(f"[+] Chat connection from {addr[0]}:{addr[1]}")
        print("Chat started! Type '/exit' to quit.")
        
        def receive_messages():
            try:
                while True:
                    data = conn.recv(1024)
                    if not data:
                        break
                    message = data.decode().strip()
                    if message == '/exit':
                        print("\n[Peer disconnected]")
                        break
                    print(f"\n[Peer]: {message}")
                    print("You: ", end="", flush=True)
            except Exception as e:
                print(f"\n[Connection error: {e}]")
        
        # Start receiving thread
        receive_thread = threading.Thread(target=receive_messages, daemon=True)
        receive_thread.start()
        
        # Main chat loop
        try:
            while True:
                response = input("You: ")
                if response.strip() == '/exit':
                    conn.sendall(response.encode())
                    break
                conn.sendall(response.encode())
        except KeyboardInterrupt:
            print("\n[Chat interrupted]")
        except Exception as e:
            print(f"[Chat error: {e}]")
            
    except Exception as e:
        print(f"[-] Chat server error: {e}")
    finally:
        try:
            conn.close()
        except:
            pass
        try:
            sock.close()
        except:
            pass