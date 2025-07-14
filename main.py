import threading
import time
import os
from src.discovery import start_discovery, PEERS
from src.server import file_receiver, choose_save_location, get_save_path, set_save_path, chat_server
from src.client import file_sender, chat_client

def main():
    print("Welcome to PyDrop!")
    print("Discovering peers on your network...")

    try:
        port_input = input("Enter server listening port (default 50001): ").strip()
        tcp_port = int(port_input) if port_input else 50001
    except ValueError:
        print("Invalid port number, defaulting to 50001")
        tcp_port = 50001

    print(f"Files will be saved to: {get_save_path()}")
    start_discovery()

    receiver_thread = threading.Thread(target=file_receiver, args=(tcp_port,), daemon=True)
    receiver_thread.start()

    try:
        while True:
            print("\n--- MENU ---")
            print("1. List available peers")
            print("2. Send a file")
            print("3. Change save location")
            print("4. Show current save location")
            print("5. Chat with peer")
            print("6. Exit")

            choice = input("Enter your choice: ")

            if choice == '1':
                print("\n--- AVAILABLE PEERS ---")
                if not PEERS:
                    print("No peers found yet. Keep waiting or check your network.")
                else:
                    peers_copy = dict(PEERS)
                    for ip, data in peers_copy.items():
                        if time.time() - data['last_seen'] > 10:
                            if ip in PEERS:
                                del PEERS[ip]
                        else:
                            print(f"- {data['name']} ({ip})")

            elif choice == '2':
                if not PEERS:
                    print("No peers to send to. Discover some first.")
                    continue

                print("\n--- AVAILABLE PEERS ---")
                valid_peers = {}
                for ip, data in PEERS.items():
                    if time.time() - data['last_seen'] <= 10:
                        valid_peers[ip] = data
                        print(f"- {data['name']} ({ip})")

                if not valid_peers:
                    print("No active peers found.")
                    continue

                peer_ip = input("Enter the IP address of the peer you want to send to: ")
                if peer_ip not in valid_peers:
                    print("Invalid IP address or peer not active.")
                    continue

                file_path = input("Enter the full path of the file you want to send: ")
                if not os.path.exists(file_path):
                    print("File not found.")
                    continue

                if not os.path.isfile(file_path):
                    print("Path is not a file.")
                    continue

                print(f"Sending file to {valid_peers[peer_ip]['name']} ({peer_ip})...")
                send_thread = threading.Thread(target=file_sender, args=(peer_ip, file_path))
                send_thread.start()
                send_thread.join()

            elif choice == '3':
                print("\n--- CHANGE SAVE LOCATION ---")
                print("1. Enter path manually")
                print("2. Use file dialog (requires GUI)")

                location_choice = input("Choose option (1 or 2): ")

                if location_choice == '1':
                    new_path = input("Enter the full path where you want to save files: ")
                    if new_path:
                        new_path = os.path.expanduser(new_path)
                        if set_save_path(new_path):
                            print(f"Save location changed to: {new_path}")
                        else:
                            print("Failed to set save location. Please check if the path exists.")
                    else:
                        print("No path entered.")

                elif location_choice == '2':
                    try:
                        new_path = choose_save_location()
                        if new_path:
                            print(f"Save location changed to: {new_path}")
                        else:
                            print("No location selected.")
                    except Exception as e:
                        print(f"Error opening file dialog: {e}")
                        print("You can try option 1 to enter the path manually.")

                else:
                    print("Invalid choice.")

            elif choice == '4':
                print(f"\nCurrent save location: {get_save_path()}")

            elif choice == '5':
                if not PEERS:
                    print("No peers to chat with. Discover some first.")
                    continue

                print("\n--- AVAILABLE PEERS ---")
                valid_peers = {}
                for ip, data in PEERS.items():
                    if time.time() - data['last_seen'] <= 10:
                        valid_peers[ip] = data
                        print(f"- {data['name']} ({ip})")

                if not valid_peers:
                    print("No active peers found.")
                    continue

                peer_ip = input("Enter the IP address of the peer you want to chat with: ")
                if peer_ip not in valid_peers:
                    print("Invalid IP address or peer not active.")
                    continue

                choice_chat = input("Host or Join chat? (h/j): ").strip().lower()
                if choice_chat == 'h':
                    print("Starting chat server... (type '/exit' to quit chat)")
                    chat_server()
                elif choice_chat == 'j':
                    print(f"Connecting to chat at {peer_ip}... (type '/exit' to quit chat)")
                    chat_client(peer_ip)
                else:
                    print("Invalid choice.")

            elif choice == '6':
                print("Exiting PyDrop. Goodbye!")
                break

            else:
                print("Invalid choice. Please try again.")

    except KeyboardInterrupt:
        print("\nExiting PyDrop. Goodbye!")

if __name__ == "__main__":
    main()
