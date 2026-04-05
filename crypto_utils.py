"""
Cryptographic utilities for Secure QR Authentication System.
Uses Fernet (symmetric encryption) for secure data transformation.
"""

from cryptography.fernet import Fernet
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize cipher with key
# WARNING: In production, load this from environment variables or secure vault
# To generate a new key: Fernet.generate_key()
# Store the key securely and never commit it to version control

KEY = os.getenv('ENCRYPTION_KEY', b'GOkcApSH3mlIDTWOILkmWhShr5OjEXRuRWJrHwxc8xk=')

try:
    cipher = Fernet(KEY)
except Exception as e:
    print(f"⚠️ Error initializing cipher: {e}")
    print("Generating new encryption key...")
    KEY = Fernet.generate_key()
    cipher = Fernet(KEY)
    print(f"New key generated: {KEY}")


def encrypt_data(data: str) -> str:
    """
    Encrypt a string using Fernet symmetric encryption.
    
    Args:
        data (str): Plain text string to encrypt
        
    Returns:
        str: Base64-encoded encrypted data
        
    Example:
        encrypted = encrypt_data("session_12345")
    """
    if isinstance(data, str):
        data = data.encode()
    encrypted = cipher.encrypt(data)
    return encrypted.decode()


def decrypt_data(encrypted_data: str) -> str:
    """
    Decrypt Fernet-encrypted data.
    
    Args:
        encrypted_data (str): Base64-encoded encrypted data
        
    Returns:
        str: Decrypted plain text string
        
    Raises:
        cryptography.fernet.InvalidToken: If decryption fails
        
    Example:
        decrypted = decrypt_data(encrypted)
    """
    if isinstance(encrypted_data, str):
        encrypted_data = encrypted_data.encode()
    try:
        decrypted = cipher.decrypt(encrypted_data)
        return decrypted.decode()
    except Exception as e:
        print(f"❌ Decryption error: {e}")
        raise


def generate_new_key() -> bytes:
    """
    Generate a new Fernet encryption key.
    Use this to initialize the system with a new key.
    
    Returns:
        bytes: A new Fernet key
        
    Example:
        new_key = generate_new_key()
        print(new_key)  # Store this safely
    """
    return Fernet.generate_key()
