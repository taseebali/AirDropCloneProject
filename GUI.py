import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import time
import os
import sys
from pathlib import Path
import socket

# Add the current directory and src directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# Try different import paths
try:
    # Try importing from src directory first
    from src.discovery import start_discovery, PEERS
    from src.server import file_receiver, set_save_path, get_save_path
    from src.client import file_sender
except ImportError:
    try:
        # Try importing from current directory
        from discovery import start_discovery, PEERS
        from server import file_receiver, set_save_path, get_save_path
        from client import file_sender
    except ImportError:
        # Try importing with relative imports
        import discovery
        import server
        import client

        start_discovery = discovery.start_discovery
        PEERS = discovery.PEERS
        file_receiver = server.file_receiver
        set_save_path = server.set_save_path
        get_save_path = server.get_save_path
        file_sender = client.file_sender


class PyDropGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("PyDrop - File Transfer")
        self.root.geometry("800x600")
        self.root.configure(bg='#f0f0f0')

        # Default save location
        self.save_location = str(Path.home() / "Downloads")
        # Set the global save path immediately
        if not set_save_path(self.save_location):
            # If Downloads doesn't exist, try Documents
            self.save_location = str(Path.home() / "Documents")
            if not set_save_path(self.save_location):
                # If Documents doesn't exist, use home directory
                self.save_location = str(Path.home())
                set_save_path(self.save_location)

        # Pending transfer confirmation
        self.pending_transfer = None
        self.confirmation_dialog = None

        # Initialize UI and services
        self.setup_ui()
        self.start_services()

    def setup_ui(self):
        """Create the main UI components."""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Title
        title_label = ttk.Label(main_frame, text="PyDrop", font=("Arial", 24, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))

        # Save location frame
        save_frame = ttk.LabelFrame(main_frame, text="Save Location", padding="10")
        save_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 20))

        self.save_location_var = tk.StringVar(value=self.save_location)
        ttk.Label(save_frame, text="Files will be saved to:").grid(row=0, column=0, sticky=tk.W)

        location_frame = ttk.Frame(save_frame)
        location_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 0))

        self.location_entry = ttk.Entry(location_frame, textvariable=self.save_location_var, state="readonly", width=50)
        self.location_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))

        ttk.Button(location_frame, text="Browse", command=self.browse_save_location).grid(row=0, column=1)
        ttk.Button(location_frame, text="Open Folder", command=self.open_save_folder).grid(row=0, column=2, padx=(5, 0))

        location_frame.columnconfigure(0, weight=1)

        # Quick location buttons
        quick_frame = ttk.Frame(save_frame)
        quick_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))

        ttk.Button(quick_frame, text="Desktop", command=lambda: self.set_quick_location("Desktop")).grid(row=0,
                                                                                                         column=0,
                                                                                                         padx=(0, 5))
        ttk.Button(quick_frame, text="Downloads", command=lambda: self.set_quick_location("Downloads")).grid(row=0,
                                                                                                             column=1,
                                                                                                             padx=5)
        ttk.Button(quick_frame, text="Documents", command=lambda: self.set_quick_location("Documents")).grid(row=0,
                                                                                                             column=2,
                                                                                                             padx=5)

        # Peers frame
        peers_frame = ttk.LabelFrame(main_frame, text="Available Peers", padding="10")
        peers_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 20))

        # Peers listbox with scrollbar
        peers_list_frame = ttk.Frame(peers_frame)
        peers_list_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.peers_listbox = tk.Listbox(peers_list_frame, height=8, selectmode=tk.SINGLE)
        peers_scrollbar = ttk.Scrollbar(peers_list_frame, orient=tk.VERTICAL, command=self.peers_listbox.yview)
        self.peers_listbox.configure(yscrollcommand=peers_scrollbar.set)

        self.peers_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        peers_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        peers_list_frame.columnconfigure(0, weight=1)
        peers_list_frame.rowconfigure(0, weight=1)

        # Refresh button
        ttk.Button(peers_frame, text="Refresh Peers", command=self.refresh_peers).grid(row=1, column=0, pady=(10, 0))

        # Send file frame
        send_frame = ttk.LabelFrame(main_frame, text="Send File", padding="10")
        send_frame.grid(row=2, column=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(20, 0), pady=(0, 20))

        ttk.Button(send_frame, text="Select File to Send", command=self.select_and_send_file, width=20).grid(row=0,
                                                                                                             column=0,
                                                                                                             pady=(0,
                                                                                                                   10))

        # Status frame
        status_frame = ttk.LabelFrame(main_frame, text="Status", padding="10")
        status_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 20))

        self.status_text = tk.Text(status_frame, height=8, state=tk.DISABLED)
        status_scrollbar = ttk.Scrollbar(status_frame, orient=tk.VERTICAL, command=self.status_text.yview)
        self.status_text.configure(yscrollcommand=status_scrollbar.set)

        self.status_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        status_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))

        # Configure grid weights
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        peers_frame.columnconfigure(0, weight=1)
        peers_frame.rowconfigure(0, weight=1)
        status_frame.columnconfigure(0, weight=1)
        status_frame.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # Auto-refresh peers
        self.refresh_peers()
        self.root.after(3000, self.auto_refresh_peers)

    def show_file_transfer_confirmation(self, filename, sender_ip, file_size):
        """Show confirmation dialog for incoming file transfer."""

        def on_accept():
            self.log_status(f"File transfer accepted: {filename} from {sender_ip}")
            if self.pending_transfer:
                self.pending_transfer['accepted'] = True
            self.confirmation_dialog.destroy()
            self.confirmation_dialog = None

        def on_reject():
            self.log_status(f"File transfer rejected: {filename} from {sender_ip}")
            if self.pending_transfer:
                self.pending_transfer['accepted'] = False
            self.confirmation_dialog.destroy()
            self.confirmation_dialog = None

        # Create confirmation dialog
        self.confirmation_dialog = tk.Toplevel(self.root)
        self.confirmation_dialog.title("Incoming File Transfer")
        self.confirmation_dialog.geometry("400x200")
        self.confirmation_dialog.resizable(False, False)
        self.confirmation_dialog.grab_set()  # Modal dialog

        # Center the dialog on the main window
        self.confirmation_dialog.transient(self.root)
        self.confirmation_dialog.geometry("+%d+%d" % (
            self.root.winfo_rootx() + 50,
            self.root.winfo_rooty() + 50
        ))

        # Main frame
        main_frame = ttk.Frame(self.confirmation_dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Icon and message
        ttk.Label(main_frame, text="📁", font=("Arial", 24)).pack(pady=(0, 10))

        ttk.Label(main_frame, text="Incoming File Transfer",
                  font=("Arial", 12, "bold")).pack(pady=(0, 10))

        # File details
        details_frame = ttk.Frame(main_frame)
        details_frame.pack(pady=(0, 20))

        ttk.Label(details_frame, text=f"File: {filename}").pack(anchor=tk.W)
        ttk.Label(details_frame, text=f"From: {sender_ip}").pack(anchor=tk.W)
        if file_size:
            size_str = self.format_file_size(file_size)
            ttk.Label(details_frame, text=f"Size: {size_str}").pack(anchor=tk.W)
        ttk.Label(details_frame, text=f"Save to: {get_save_path()}").pack(anchor=tk.W)

        ttk.Label(main_frame, text="Do you want to accept this file?").pack(pady=(0, 20))

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack()

        ttk.Button(button_frame, text="Yes", command=on_accept, width=10).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="No", command=on_reject, width=10).pack(side=tk.LEFT)

        # Handle dialog close
        self.confirmation_dialog.protocol("WM_DELETE_WINDOW", on_reject)

        # Set pending transfer info
        self.pending_transfer = {
            'filename': filename,
            'sender_ip': sender_ip,
            'file_size': file_size,
            'accepted': None
        }

    def format_file_size(self, size_bytes):
        """Format file size in human readable format."""
        if size_bytes == 0:
            return "0 B"
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024
            i += 1
        return f"{size_bytes:.1f} {size_names[i]}"

    def browse_save_location(self):
        """Open a dialog to select save location."""
        folder = filedialog.askdirectory(initialdir=self.save_location, title="Select Save Location")
        if folder:
            self.save_location = folder
            self.save_location_var.set(folder)
            # Update the global save path
            if set_save_path(folder):
                self.log_status(f"Save location changed to: {folder}")
                print(f"[GUI] Save location changed to: {folder}")  # Debug print
            else:
                self.log_status(f"Failed to set save location: {folder}")
                print(f"[GUI] Failed to set save location: {folder}")  # Debug print

    def open_save_folder(self):
        """Open the current save location in file explorer."""
        current_path = get_save_path()  # Get the actual current path
        if os.path.exists(current_path):
            if os.name == 'nt':  # Windows
                os.startfile(current_path)
            elif os.name == 'posix':  # macOS and Linux
                os.system(
                    f'open "{current_path}"' if os.uname().sysname == 'Darwin' else f'xdg-open "{current_path}"')
        else:
            messagebox.showerror("Error", "Save location does not exist!")

    def set_quick_location(self, location):
        """Set save location to a quick location."""
        locations = {
            "Desktop": str(Path.home() / "Desktop"),
            "Downloads": str(Path.home() / "Downloads"),
            "Documents": str(Path.home() / "Documents")
        }

        folder = locations.get(location)
        if folder and os.path.exists(folder):
            self.save_location = folder
            self.save_location_var.set(folder)
            # Update the global save path
            if set_save_path(folder):
                self.log_status(f"Save location changed to: {folder}")
                print(f"[GUI] Save location changed to: {folder}")  # Debug print
            else:
                self.log_status(f"Failed to set save location: {folder}")
                print(f"[GUI] Failed to set save location: {folder}")  # Debug print
        else:
            messagebox.showerror("Error", f"{location} folder not found!")

    def start_services(self):
        """Start discovery and file receiver services."""
        # Start discovery
        start_discovery()

        # Start file receiver in a separate thread
        self.receiver_thread = threading.Thread(target=self.file_receiver_wrapper, daemon=True)
        self.receiver_thread.start()

        self.log_status("PyDrop started successfully!")
        self.log_status("Discovering peers on your network...")
        self.log_status(f"Files will be saved to: {get_save_path()}")

    def file_receiver_wrapper(self):
        """Wrapper for file receiver to handle GUI updates."""
        try:
            # Use the existing file_receiver function with GUI parameters
            file_receiver(
                on_file_received=self.on_file_received,
                on_transfer_progress=self.on_transfer_progress,
                on_transfer_request=self.on_transfer_request,
                gui_root=self.root
            )
        except Exception as e:
            self.log_status(f"Error in file receiver: {e}")
            print(f"[GUI] Error in file receiver: {e}")

    def on_transfer_request(self, filename, sender_ip, file_size):
        """Callback when a file transfer is requested."""
        print(f"[GUI] Transfer request: {filename} from {sender_ip}, current save path: {get_save_path()}")  # Debug print

        def show_dialog():
            self.show_file_transfer_confirmation(filename, sender_ip, file_size)

        # Schedule GUI update on main thread
        self.root.after(0, show_dialog)

        # Wait for user response
        while self.pending_transfer and self.pending_transfer['accepted'] is None:
            time.sleep(0.1)

        if self.pending_transfer:
            result = self.pending_transfer['accepted']
            self.pending_transfer = None
            return result
        return False

    def on_file_received(self, filename, sender_ip):
        """Callback when a file is received."""

        def update_gui():
            if filename.startswith("FAILED:"):
                self.log_status(f"File transfer failed: {filename[7:]} from {sender_ip}")
            else:
                self.log_status(f"File received: {filename} from {sender_ip}")
                self.log_status(f"Saved to: {os.path.join(get_save_path(), filename)}")
            self.progress_var.set(0)

        # Schedule GUI update on main thread
        self.root.after(0, update_gui)

    def on_transfer_progress(self, progress):
        """Callback for transfer progress updates."""

        def update_progress():
            self.progress_var.set(progress)

        # Schedule GUI update on main thread
        self.root.after(0, update_progress)

    def refresh_peers(self):
        """Refresh the peers list."""
        self.peers_listbox.delete(0, tk.END)

        current_time = time.time()
        active_peers = []

        # Create a copy of PEERS to avoid modification during iteration
        peers_copy = dict(PEERS)

        for ip, data in peers_copy.items():
            if current_time - data['last_seen'] <= 10:  # Peer is active
                active_peers.append((ip, data))
                self.peers_listbox.insert(tk.END, f"{data['name']} ({ip})")
            else:
                # Remove inactive peer
                if ip in PEERS:
                    del PEERS[ip]

        if not active_peers:
            self.peers_listbox.insert(tk.END, "No peers found...")

    def auto_refresh_peers(self):
        """Automatically refresh peers every 3 seconds."""
        self.refresh_peers()
        self.root.after(3000, self.auto_refresh_peers)

    def select_and_send_file(self):
        """Select a file and send it to the selected peer."""
        # Check if a peer is selected
        selection = self.peers_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Peer Selected", "Please select a peer to send the file to.")
            return

        selected_text = self.peers_listbox.get(selection[0])
        if selected_text == "No peers found...":
            messagebox.showwarning("No Peers", "No peers available to send files to.")
            return

        # Get selected peer IP
        try:
            peer_ip = selected_text.split('(')[1].split(')')[0]
        except IndexError:
            messagebox.showerror("Error", "Could not parse peer IP address.")
            return

        # Check if peer is still active
        if peer_ip not in PEERS:
            messagebox.showwarning("Peer Unavailable", "Selected peer is no longer available.")
            self.refresh_peers()
            return

        # Select file to send
        file_path = filedialog.askopenfilename(
            title="Select File to Send",
            filetypes=[("All Files", "*.*")]
        )

        if file_path:
            if not os.path.exists(file_path):
                messagebox.showerror("Error", "Selected file does not exist.")
                return

            if not os.path.isfile(file_path):
                messagebox.showerror("Error", "Selected path is not a file.")
                return

            # Send file in a separate thread
            self.log_status(f"Sending file: {os.path.basename(file_path)} to {PEERS[peer_ip]['name']} ({peer_ip})")
            send_thread = threading.Thread(
                target=self.send_file_wrapper,
                args=(peer_ip, file_path),
                daemon=True
            )
            send_thread.start()
    def send_file_wrapper(self, peer_ip, file_path):
        """Wrapper for file sender to handle GUI updates."""
        try:
            self.root.after(0, lambda: self.progress_var.set(0))
            file_sender(peer_ip, file_path)
            self.root.after(0, lambda: self.log_status(f"File sent successfully: {os.path.basename(file_path)}"))
            self.root.after(0, lambda: self.progress_var.set(100))
            # Reset progress bar after 3 seconds
            self.root.after(3000, lambda: self.progress_var.set(0))
        except Exception as e:
            self.root.after(0, lambda: self.log_status(f"Error sending file: {e}"))
            self.root.after(0, lambda: self.progress_var.set(0))

    def log_status(self, message):
        """Add a message to the status log."""
        self.status_text.config(state=tk.NORMAL)
        timestamp = time.strftime("%H:%M:%S")
        self.status_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.status_text.see(tk.END)
        self.status_text.config(state=tk.DISABLED)


def main():
    """Main function to run the PyDrop GUI application."""
    root = tk.Tk()
    app = PyDropGUI(root)

    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("Exiting PyDrop...")


if __name__ == "__main__":
    main()