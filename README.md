# PyDrop

A simple LAN-based file sharing application inspired by Apple's AirDrop.

## Features

- Peer discovery on the local network using UDP broadcasts.
- File transfer using TCP sockets.
- AES encryption for secure file transmission.
- Command-line interface for interacting with the application.

## Project Structure

```
PyDrop/
├── src/
│   ├── __init__.py
│   ├── client.py
│   ├── discovery.py
│   └── server.py
├── utils/
│   ├── __init__.py
│   ├── crypto.py
│   └── file_utils.py
├── main.py
└── requirements.txt
```

## Setup and Usage

1.  **Install Dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

2.  **Run the Application:**

    Open two separate terminals. In each terminal, run the `main.py` script:

    ```bash
    python main.py
    ```

3.  **Using PyDrop:**

    -   The application will start by discovering other peers on the network.
    -   You can choose to list available peers or send a file from the menu.
    -   To send a file, select a peer from the list and provide the full path to the file.
    -   The receiving client will be prompted to accept or decline the incoming file.
    -   A progress bar will show the status of the file transfer.
    -   Received files are saved in the same directory where the script is running.
