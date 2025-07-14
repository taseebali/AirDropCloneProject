import os

DEFAULT_SAVE_PATH = os.path.expanduser("~/Downloads")
save_path = DEFAULT_SAVE_PATH


def get_save_path():
    """Return the current save path for received files."""
    return save_path


def set_save_path(path):
    """Set a new save path for received files.

    Returns True if successful, False if path does not exist.
    """
    global save_path
    if os.path.isdir(path):
        save_path = path
        return True
    return False
