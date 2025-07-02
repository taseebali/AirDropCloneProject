
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import os

# For simplicity, using a hardcoded key. In a real app, this should be handled securely.
# For example, using a key exchange mechanism like Diffie-Hellman.
KEY = b'mysecretpassword' # 16, 24, or 32 bytes long
SALT_SIZE = 16
NONCE_SIZE = 16
TAG_SIZE = 16

def get_key():
    """Returns the hardcoded key."""
    return KEY

def encrypt_file(file_path, key):
    """
    Encrypts a file using AES GCM mode.

    Args:
        file_path (str): The path to the file to encrypt.
        key (bytes): The encryption key.

    Returns:
        tuple: A tuple containing the encrypted data, nonce, and tag.
    """
    with open(file_path, 'rb') as f:
        data = f.read()
    
    cipher = AES.new(key, AES.MODE_GCM)
    ciphertext, tag = cipher.encrypt_and_digest(data)
    
    return ciphertext, cipher.nonce, tag

def decrypt_file(encrypted_data, key, nonce, tag, output_path):
    """
    Decrypts a file using AES GCM mode.

    Args:
        encrypted_data (bytes): The encrypted file data.
        key (bytes): The decryption key.
        nonce (bytes): The nonce used during encryption.
        tag (bytes): The authentication tag.
        output_path (str): The path to save the decrypted file.
    """
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    decrypted_data = cipher.decrypt_and_verify(encrypted_data, tag)
    
    with open(output_path, 'wb') as f:
        f.write(decrypted_data)
