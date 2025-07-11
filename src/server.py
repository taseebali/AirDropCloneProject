import socket
import os
import threading
import tkinter as tk
from tkinter import messagebox, filedialog
from tqdm import tqdm
from utils.crypto import decrypt_file, get_key, NONCE_SIZE, TAG_SIZE

TCP_PORT = 50001
BUFFER_SIZE = 4096

# Global variable to store the current save path
CURRENT_SAVE_PATH = os.path.expanduser("~/Downloads")  # Default to Downloads folder


def set_save_path(new_path):
    """Set the global save path for incoming files."""
    global CURRENT_SAVE_PATH
    if os.path.exists(new_path) and os.path.isdir(new_path):
        CURRENT_SAVE_PATH = new_path
        print(f"[*] Save path set to: {CURRENT_SAVE_PATH}")
        return True
    else:
        print(f"[-] Invalid path: {new_path}")
        return False


def get_save_path():
    """Get the current save path."""
    return CURRENT_SAVE_PATH


def choose_save_location():
    """Open a dialog to choose save location."""
    root = tk.Tk()
    root.withdraw()  # Hide the main window

    folder_path = filedialog.askdirectory(
        title="Choose folder to save received files",
        initialdir=CURRENT_SAVE_PATH
    )

    root.destroy()

    if folder_path:
        set_save_path(folder_path)
        return folder_path
    return None


def file_receiver(save_path_func=None, save_path=".", on_file_received=None, on_transfer_progress=None,
                  on_transfer_request=None, gui_root=None):
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

                    # Handle file acceptance based on context
                    accept_file = False
                    chosen_path = None

                    if on_transfer_request:
                        # GUI mode - use the GUI's callback for acceptance
                        accept_file = on_transfer_request(file_name, addr[0], file_size)
                        # Use the current save path from GUI
                        current_save_path = get_save_path()
                    elif gui_root:
                        # GUI mode but no callback - use built-in dialog
                        accept_file, chosen_path = show_file_acceptance_dialog(gui_root, file_name, file_size, addr[0])
                        current_save_path = chosen_path if chosen_path else get_save_path()
                    else:
                        # Command line mode
                        response = input(f"Incoming file: {file_name} ({file_size} bytes). Accept? (y/n): ")
                        accept_file = response.lower() == 'y'
                        current_save_path = get_save_path()

                    if not accept_file:
                        conn.send(b"DECLINE")
                        print("[-] File transfer declined.")
                        continue

                    conn.send(b"ACCEPT")

                    # Ensure save directory exists
                    os.makedirs(current_save_path, exist_ok=True)

                    # Handle file name conflicts
                    output_path = os.path.join(current_save_path, file_name)
                    output_path = get_unique_filename(output_path)

                    print(f"[*] Saving file to: {output_path}")

                    # Receive file data
                    key = get_key()

                    # Receive nonce and tag
                    nonce = conn.recv(NONCE_SIZE)
                    tag = conn.recv(TAG_SIZE)

                    encrypted_data = b""
                    bytes_received = 0

                    print(f"[*] Receiving file: {file_name}")

                    # Use progress bar only in command line mode
                    if not gui_root:
                        progress_bar = tqdm(total=file_size, unit='B', unit_scale=True, desc=file_name)

                    while bytes_received < file_size:
                        chunk = conn.recv(min(BUFFER_SIZE, file_size - bytes_received))
                        if not chunk:
                            break
                        encrypted_data += chunk
                        bytes_received += len(chunk)

                        # Update progress
                        if not gui_root:
                            progress_bar.update(len(chunk))
                        elif on_transfer_progress:
                            progress_percent = (bytes_received / file_size) * 100
                            on_transfer_progress(progress_percent)

                    if not gui_root:
                        progress_bar.close()

                    try:
                        decrypt_file(encrypted_data, key, nonce, tag, output_path)
                        print(f"\n[+] File '{file_name}' received and decrypted successfully.")
                        print(f"[+] Saved to: {output_path}")

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


def get_unique_filename(filepath):
    """Generate a unique filename if the file already exists."""
    if not os.path.exists(filepath):
        return filepath

    directory = os.path.dirname(filepath)
    filename = os.path.basename(filepath)
    name, ext = os.path.splitext(filename)

    counter = 1
    while True:
        new_filename = f"{name}_{counter}{ext}"
        new_filepath = os.path.join(directory, new_filename)
        if not os.path.exists(new_filepath):
            return new_filepath
        counter += 1


def show_file_acceptance_dialog(root, file_name, file_size, sender_ip):
    """Show a dialog to accept or decline file transfer with save location option."""
    result = [False, None]  # [accept, save_path]

    def on_accept():
        result[0] = True
        dialog.destroy()

    def on_decline():
        result[0] = False
        dialog.destroy()

    def on_choose_location():
        folder_path = filedialog.askdirectory(
            title="Choose folder to save file",
            initialdir=CURRENT_SAVE_PATH
        )
        if folder_path:
            result[1] = folder_path
            location_label.config(text=f"Save to: {folder_path}")
            accept_button.config(state=tk.NORMAL)

    # Create dialog window
    dialog = tk.Toplevel(root)
    dialog.title("Incoming File Transfer")
    dialog.geometry("500x300")
    dialog.resizable(False, False)
    dialog.transient(root)
    dialog.grab_set()

    # Center the dialog
    dialog.update_idletasks()
    x = (dialog.winfo_screenwidth() // 2) - (500 // 2)
    y = (dialog.winfo_screenheight() // 2) - (300 // 2)
    dialog.geometry(f"500x300+{x}+{y}")

    # Content frame
    frame = tk.Frame(dialog, padx=20, pady=20)
    frame.pack(fill=tk.BOTH, expand=True)

    # File info
    tk.Label(frame, text="Incoming File Transfer", font=("Arial", 14, "bold")).pack(pady=(0, 15))

    info_frame = tk.Frame(frame)
    info_frame.pack(fill=tk.X, pady=(0, 15))

    tk.Label(info_frame, text=f"File: {file_name}", font=("Arial", 10)).pack(anchor=tk.W)
    tk.Label(info_frame, text=f"Size: {file_size:,} bytes ({file_size / 1024 / 1024:.1f} MB)", font=("Arial", 10)).pack(
        anchor=tk.W)
    tk.Label(info_frame, text=f"From: {sender_ip}", font=("Arial", 10)).pack(anchor=tk.W)

    # Save location section
    location_frame = tk.Frame(frame)
    location_frame.pack(fill=tk.X, pady=(0, 15))

    tk.Label(location_frame, text="Save Location:", font=("Arial", 10, "bold")).pack(anchor=tk.W)
    location_label = tk.Label(location_frame, text=f"Default: {CURRENT_SAVE_PATH}", font=("Arial", 9), fg="gray")
    location_label.pack(anchor=tk.W, pady=(2, 5))

    tk.Button(location_frame, text="Choose Different Location", command=on_choose_location,
              bg="#2196F3", fg="white", width=20).pack(anchor=tk.W)

    tk.Label(frame, text="Do you want to accept this file?", font=("Arial", 11, "bold")).pack(pady=(20, 15))

    # Buttons
    button_frame = tk.Frame(frame)
    button_frame.pack(pady=(10, 0))

    accept_button = tk.Button(button_frame, text="Accept", command=on_accept,
                              bg="#4CAF50", fg="white", width=12, font=("Arial", 10))
    accept_button.pack(side=tk.LEFT, padx=(0, 10))

    tk.Button(button_frame, text="Decline", command=on_decline,
              bg="#f44336", fg="white", width=12, font=("Arial", 10)).pack(side=tk.LEFT)

    # Wait for user response
    dialog.wait_window()

    return result[0], result[1]