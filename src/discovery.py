import socket
import threading
import time
import uuid

BROADCAST_PORT = 50000
PEERS = {}
MY_ID = str(uuid.uuid4()) # Generate a unique ID for this instance

def broadcaster(host_ip, host_name):
    """Broadcasts the presence of the host every 3 seconds."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        message = f"{host_name}:{host_ip}:{MY_ID}".encode('utf-8')
        while True:
            s.sendto(message, ('<broadcast>', BROADCAST_PORT))
            time.sleep(3)

def listener():
    """Listens for broadcasts from other peers and updates the PEERS dictionary."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(("", BROADCAST_PORT))
        while True:
            data, addr = s.recvfrom(1024)
            message = data.decode('utf-8')
            try:
                name, ip, peer_id = message.split(":")
                if peer_id != MY_ID: # Filter out our own broadcasts
                    PEERS[ip] = {'name': name, 'last_seen': time.time(), 'id': peer_id}
            except ValueError:
                pass # Ignore malformed messages

def start_discovery():
    """Starts the broadcaster and listener threads."""
    host_name = socket.gethostname()
    host_ip = get_my_ip()

    broadcaster_thread = threading.Thread(target=broadcaster, args=(host_ip, host_name), daemon=True)
    listener_thread = threading.Thread(target=listener, daemon=True)

    broadcaster_thread.start()
    listener_thread.start()

def get_my_ip():
    """Returns the local IP address of the host."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP