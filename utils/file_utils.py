import os

def get_file_size(file_path):
    """Returns the size of a file in bytes."""
    return os.path.getsize(file_path)

def read_file_chunks(file_path, chunk_size=4096):
    """Reads a file in chunks."""
    with open(file_path, 'rb') as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            yield chunk
