import os
import shutil


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


def ensure_directory_exists(directory_path):
    """Ensure a directory exists, create it if it doesn't."""
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
        return True
    return os.path.isdir(directory_path)


def get_available_space(directory_path):
    """Get available space in the directory (in bytes)."""
    try:
        _, _, free_bytes = shutil.disk_usage(directory_path)
        return free_bytes
    except Exception:
        return None


def is_valid_filename(filename):
    """Check if a filename is valid for the current OS."""
    # Characters that are not allowed in filenames on most systems
    invalid_chars = '<>:"/\\|?*'

    # Check for invalid characters
    for char in invalid_chars:
        if char in filename:
            return False

    # Check for reserved names on Windows
    reserved_names = [
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    ]

    name_without_ext = os.path.splitext(filename)[0].upper()
    if name_without_ext in reserved_names:
        return False

    # Check length (most filesystems have a 255 character limit)
    if len(filename) > 255:
        return False

    return True


def sanitize_filename(filename):
    """Sanitize a filename by removing or replacing invalid characters."""
    # Replace invalid characters with underscores
    invalid_chars = '<>:"/\\|?*'
    sanitized = filename

    for char in invalid_chars:
        sanitized = sanitized.replace(char, '_')

    # Remove leading/trailing dots and spaces
    sanitized = sanitized.strip('. ')

    # Ensure it's not empty
    if not sanitized:
        sanitized = "file"

    # Truncate if too long
    if len(sanitized) > 255:
        name, ext = os.path.splitext(sanitized)
        max_name_length = 255 - len(ext)
        sanitized = name[:max_name_length] + ext

    return sanitized


def format_file_size(size_bytes):
    """Format file size in human readable format."""
    if size_bytes == 0:
        return "0 B"

    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1

    return f"{size_bytes:.1f} {size_names[i]}"