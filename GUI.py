import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import time
import os
from pathlib import Path
import socket
from src.discovery import start_discovery, PEERS
from src.server import file_receiver
from src.client import file_sender


class PyDropGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("PyDrop - File Transfer")
        self.root.geometry("800x600")
        self.root.configure(bg='#f0f0f0')

        # Default save location
        self.save_location = str(Path.home() / "Downloads")

        # Initialize discovery
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

    def browse_save_location(self):
        """Open a dialog to select save location."""
        folder = filedialog.askdirectory(initialdir=self.save_location, title="Select Save Location")
        if folder:
            self.save_location = folder
            self.save_location_var.set(folder)
            self.log_status(f"Save location changed to: {folder}")

    def open_save_folder(self):
        """Open the current save location in file explorer."""
        if os.path.exists(self.save_location):
            os.startfile(self.save_location) if os.name == 'nt' else os.system(f'open "{self.save_location}"')
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
            self.log_status(f"Save location changed to: {folder}")
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

    def file_receiver_wrapper(self):
        """Wrapper for file receiver to handle GUI updates."""
        try:
            from src.server import file_receiver
            file_receiver(self.save_location, self.on_file_received, self.on_transfer_progress, self.root)
        except Exception as e:
            self.log_status(f"Error in file receiver: {e}")

    def on_file_received(self, filename, sender_ip):
        """Callback when a file is received."""
        if filename.startswith("FAILED:"):
            self.log_status(f"File transfer failed: {filename[7:]} from {sender_ip}")
        else:
            self.log_status(f"File received: {filename} from {sender_ip}")
            self.log_status(f"Saved to: {os.path.join(self.save_location, filename)}")
        self.progress_var.set(0)

    def on_transfer_progress(self, progress):
        """Callback for transfer progress updates."""
        self.progress_var.set(progress)
        self.root.update_idletasks()

    def refresh_peers(self):
        """Refresh the peers list."""
        self.peers_listbox.delete(0, tk.END)

        current_time = time.time()
        active_peers = {}

        for ip, data in PEERS.items():
            if current_time - data['last_seen'] <= 10:  # Peer is active
                active_peers[ip] = data
                self.peers_listbox.insert(tk.END, f"{data['name']} ({ip})")

        # Update PEERS to remove inactive peers
        PEERS.clear()
        PEERS.update(active_peers)

        if not PEERS:
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

        if self.peers_listbox.get(selection[0]) == "No peers found...":
            messagebox.showwarning("No Peers", "No peers available to send files to.")
            return

        # Get selected peer IP
        peer_info = self.peers_listbox.get(selection[0])
        peer_ip = peer_info.split('(')[1].split(')')[0]

        # Select file to send
        file_path = filedialog.askopenfilename(
            title="Select File to Send",
            filetypes=[("All Files", "*.*")]
        )

        if file_path:
            # Send file in a separate thread
            self.log_status(f"Sending file: {os.path.basename(file_path)} to {peer_ip}")
            send_thread = threading.Thread(
                target=self.send_file_wrapper,
                args=(peer_ip, file_path),
                daemon=True
            )
            send_thread.start()

    def send_file_wrapper(self, peer_ip, file_path):
        """Wrapper for file sender to handle GUI updates."""
        try:
            self.progress_var.set(0)
            file_sender(peer_ip, file_path)
            self.log_status(f"File sent successfully: {os.path.basename(file_path)}")
            self.progress_var.set(100)
        except Exception as e:
            self.log_status(f"Error sending file: {e}")
            self.progress_var.set(0)

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