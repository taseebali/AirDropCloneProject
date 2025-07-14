import socket
import os
import threading
from tqdm import tqdm
from utils.crypto import encrypt_file, get_key
from utils.file_utils import get_file_size

TCP_PORT = 50001
BUFFER_SIZE = 4096
CHAT_PORT = 50010  # Added chat port


def file_sender(peer_ip, file_path):
    """Connects to a peer and sends a file."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((peer_ip, TCP_PORT))
            print(f"[+] Connected to {peer_ip}")

            file_name = os.path.basename(file_path)  # Correctly get filename
            file_size = get_file_size(file_path)

            # Send file info
            s.send(f"{file_name}|{file_size}".encode('utf-8'))

            # Wait for confirmation
            response = s.recv(1024)
            if response == b"DECLINE":
                print("[-] Peer declined the file transfer.")
                return

            # Encrypt and send file
            key = get_key()
            encrypted_data, nonce, tag = encrypt_file(file_path, key)

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


def chat_client(peer_ip, chat_port=CHAT_PORT):
    import sys
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.connect((peer_ip, chat_port))
            print(f"[*] Chat client connected to {peer_ip}:{chat_port}")
            print("Type '/exit' to quit chat.")

            def receive_messages():
                while True:
                    try:
                        data = s.recv(1024)
                        if not data:
                            print("\n[*] Peer disconnected.")
                            break
                        print(f"\nPeer: {data.decode('utf-8')}\nYou: ", end="", flush=True)
                    except:
                        break

            recv_thread = threading.Thread(target=receive_messages, daemon=True)
            recv_thread.start()

            while True:
                msg = input("You: ")
                if msg.strip() == "/exit":
                    print("[*] Exiting chat client.")
                    break
                try:
                    s.sendall(msg.encode('utf-8'))
                except:
                    print("[*] Connection closed unexpectedly.")
                    break

    except Exception as e:
        print(f"[-] Chat client error: {e}")
        sys.exit(1)
