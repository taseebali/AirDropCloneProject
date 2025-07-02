
import threading
import time
import os
from src.discovery import start_discovery, PEERS
from src.server import file_receiver
from src.client import file_sender

def main():
    """Main function to run the PyDrop application."""
    # Start discovery and server in the background
    start_discovery()
    receiver_thread = threading.Thread(target=file_receiver, daemon=True)
    receiver_thread.start()

    print("Welcome to PyDrop!")
    print("Discovering peers on your network...")

    try:
        while True:
            print("\n--- MENU ---")
            print("1. List available peers")
            print("2. Send a file")
            print("3. Exit")

            choice = input("Enter your choice: ")

            if choice == '1':
                print("\n--- AVAILABLE PEERS ---")
                if not PEERS:
                    print("No peers found yet. Keep waiting or check your network.")
                else:
                    for ip, data in PEERS.items():
                        # Prune peers that haven't been seen in a while
                        if time.time() - data['last_seen'] > 10:
                            del PEERS[ip]
                        else:
                            print(f"- {data['name']} ({ip})")

            elif choice == '2':
                if not PEERS:
                    print("No peers to send to. Discover some first.")
                    continue

                peer_ip = input("Enter the IP address of the peer you want to send to: ")
                if peer_ip not in PEERS:
                    print("Invalid IP address.")
                    continue

                file_path = input("Enter the full path of the file you want to send: ")
                if not os.path.exists(file_path):
                    print("File not found.")
                    continue
                
                # Create a dummy file for testing if it doesn't exist
                if not os.path.exists("test.txt"):
                    with open("test.txt", "w") as f:
                        f.write("This is a test file.")
                
                send_thread = threading.Thread(target=file_sender, args=(peer_ip, file_path))
                send_thread.start()
                send_thread.join() # Wait for the send to complete

            elif choice == '3':
                print("Exiting PyDrop. Goodbye!")
                break

            else:
                print("Invalid choice. Please try again.")

    except KeyboardInterrupt:
        print("\nExiting PyDrop. Goodbye!")

if __name__ == "__main__":
    main()
