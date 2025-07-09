import socket
import os
import threading
import tkinter as tk
from tkinter import messagebox
from tqdm import tqdm
from utils.crypto import decrypt_file, get_key, NONCE_SIZE, TAG_SIZE

TCP_PORT = 50001
BUFFER_SIZE = 4096


def file_receiver(save_path=".", on_file_received=None, on_transfer_progress=None, gui_root=None):
    """Listens for incoming file transfers and handles them."""
    while True:  # Keep listening for connections
        try:
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

                    # Show GUI dialog for file acceptance
                    if gui_root:
                        accept_file = show_file_acceptance_dialog(gui_root, file_name, file_size, addr[0])
                    else:
                        # Fallback to command line
                        response = input(f"Incoming file: {file_name} ({file_size} bytes). Accept? (y/n): ")
                        accept_file = response.lower() == 'y'

                    if not accept_file:
                        conn.send(b"DECLINE")
                        print("[-] File transfer declined.")
                        continue

                    conn.send(b"ACCEPT")

                    # Receive file data
                    output_path = os.path.join(save_path, file_name)
                    key = get_key()

                    # Receive nonce and tag
                    nonce = conn.recv(NONCE_SIZE)
                    tag = conn.recv(TAG_SIZE)

                    encrypted_data = b""
                    bytes_received = 0

                    while bytes_received < file_size:
                        chunk = conn.recv(min(BUFFER_SIZE, file_size - bytes_received))
                        if not chunk:
                            break
                        encrypted_data += chunk
                        bytes_received += len(chunk)

                        # Update progress
                        if on_transfer_progress:
                            progress = (bytes_received / file_size) * 100
                            on_transfer_progress(progress)

                    try:
                        decrypt_file(encrypted_data, key, nonce, tag, output_path)
                        print(f"\n[+] File '{file_name}' received and decrypted successfully.")

                        # Notify GUI of successful reception
                        if on_file_received:
                            on_file_received(file_name, addr[0])

                    except Exception as e:
                        print(f"\n[-] Decryption failed: {e}")
                        if on_file_received:
                            on_file_received(f"FAILED: {file_name}", addr[0])

        except Exception as e:
            print(f"[-] Server error: {e}")
            continue


def show_file_acceptance_dialog(root, file_name, file_size, sender_ip):
    """Show a dialog to accept or decline file transfer."""
    result = [False]  # Use list to allow modification in nested function

    def on_accept():
        result[0] = True
        dialog.destroy()

    def on_decline():
        result[0] = False
        dialog.destroy()

    # Create dialog window
    dialog = tk.Toplevel(root)
    dialog.title("Incoming File Transfer")
    dialog.geometry("400x200")
    dialog.resizable(False, False)
    dialog.transient(root)
    dialog.grab_set()

    # Center the dialog
    dialog.update_idletasks()
    x = (dialog.winfo_screenwidth() // 2) - (400 // 2)
    y = (dialog.winfo_screenheight() // 2) - (200 // 2)
    dialog.geometry(f"400x200+{x}+{y}")

    # Content frame
    frame = tk.Frame(dialog, padx=20, pady=20)
    frame.pack(fill=tk.BOTH, expand=True)

    # File info
    tk.Label(frame, text="Incoming File Transfer", font=("Arial", 12, "bold")).pack(pady=(0, 10))
    tk.Label(frame, text=f"File: {file_name}").pack(anchor=tk.W)
    tk.Label(frame, text=f"Size: {file_size:,} bytes ({file_size / 1024 / 1024:.1f} MB)").pack(anchor=tk.W)
    tk.Label(frame, text=f"From: {sender_ip}").pack(anchor=tk.W)

    tk.Label(frame, text="Do you want to accept this file?", font=("Arial", 10, "bold")).pack(pady=(20, 10))

    # Buttons
    button_frame = tk.Frame(frame)
    button_frame.pack(pady=(10, 0))

    tk.Button(button_frame, text="Accept", command=on_accept, bg="#4CAF50", fg="white", width=10).pack(side=tk.LEFT,
                                                                                                       padx=(0, 10))
    tk.Button(button_frame, text="Decline", command=on_decline, bg="#f44336", fg="white", width=10).pack(side=tk.LEFT)

    # Wait for user response
    dialog.wait_window()

    return result[0]