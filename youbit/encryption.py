"""
Encryption module for YouBit using AES-256-GCM with password-based key derivation.

This module provides password-based encryption with authenticated encryption,
ensuring both confidentiality and data integrity.
"""
from __future__ import annotations
import os
from typing import Tuple
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.backends import default_backend


# Constants
SALT_LENGTH = 16  # bytes
NONCE_LENGTH = 12  # bytes for GCM
KEY_LENGTH = 32  # bytes for AES-256
PBKDF2_ITERATIONS = 100_000


def generate_salt() -> bytes:
    """Generate a random salt for key derivation.
    
    Returns:
        bytes: Random salt of SALT_LENGTH bytes
    """
    return os.urandom(SALT_LENGTH)


def derive_key_from_password(password: str, salt: bytes) -> bytes:
    """Derive an encryption key from a password using PBKDF2.
    
    Args:
        password: User password string
        salt: Salt bytes for key derivation
        
    Returns:
        bytes: Derived encryption key of KEY_LENGTH bytes
        
    Raises:
        ValueError: If password or salt are invalid
    """
    if not password:
        raise ValueError("Password cannot be empty")
    if not salt or len(salt) != SALT_LENGTH:
        raise ValueError(f"Salt must be exactly {SALT_LENGTH} bytes")
    
    password_bytes = password.encode('utf-8')
    
    kdf = PBKDF2(
        algorithm=hashes.SHA256(),
        length=KEY_LENGTH,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
        backend=default_backend()
    )
    
    key = kdf.derive(password_bytes)
    return key


def encrypt_data(data: bytes, password: str) -> Tuple[bytes, bytes, bytes]:
    """Encrypt data using AES-256-GCM with password-based key derivation.
    
    Args:
        data: Plain bytes to encrypt
        password: User password for key derivation
        
    Returns:
        Tuple of (salt, nonce, ciphertext_with_tag):
            - salt: Random salt used for key derivation
            - nonce: Random nonce used for encryption
            - ciphertext_with_tag: Encrypted data with authentication tag
            
    Raises:
        ValueError: If data or password are invalid
    """
    if not data:
        raise ValueError("Data cannot be empty")
    if not password:
        raise ValueError("Password cannot be empty")
    
    # Generate random salt and nonce
    salt = generate_salt()
    nonce = os.urandom(NONCE_LENGTH)
    
    # Derive key from password
    key = derive_key_from_password(password, salt)
    
    # Encrypt with GCM (provides authentication tag)
    cipher = AESGCM(key)
    ciphertext = cipher.encrypt(nonce, data, None)  # None = no associated data
    
    return salt, nonce, ciphertext


def decrypt_data(data: bytes, password: str, salt: bytes, nonce: bytes) -> bytes:
    """Decrypt data using AES-256-GCM with password-based key derivation.
    
    Args:
        data: Encrypted data with authentication tag
        password: User password for key derivation
        salt: Salt used during original encryption
        nonce: Nonce used during original encryption
        
    Returns:
        bytes: Decrypted plain data
        
    Raises:
        ValueError: If inputs are invalid
        cryptography.exceptions.InvalidTag: If authentication fails (data corrupted/tampered)
    """
    if not data:
        raise ValueError("Data cannot be empty")
    if not password:
        raise ValueError("Password cannot be empty")
    if not salt or len(salt) != SALT_LENGTH:
        raise ValueError(f"Salt must be exactly {SALT_LENGTH} bytes")
    if not nonce or len(nonce) != NONCE_LENGTH:
        raise ValueError(f"Nonce must be exactly {NONCE_LENGTH} bytes")
    
    # Derive key from password
    key = derive_key_from_password(password, salt)
    
    # Decrypt with GCM (verifies authentication tag)
    cipher = AESGCM(key)
    try:
        plaintext = cipher.decrypt(nonce, data, None)  # None = no associated data
    except Exception as e:
        raise ValueError(
            f"Decryption failed. Possible causes: wrong password, corrupted data, or tampering. "
            f"Details: {str(e)}"
        )
    
    return plaintext


def pack_encrypted_data(salt: bytes, nonce: bytes, ciphertext: bytes) -> bytes:
    """Pack salt, nonce, and ciphertext into a single binary blob.
    
    Format: [2-byte length of salt][salt][2-byte length of nonce][nonce][ciphertext]
    
    Args:
        salt: Salt bytes
        nonce: Nonce bytes
        ciphertext: Encrypted data bytes
        
    Returns:
        bytes: Packed binary data
    """
    if len(salt) > 0xFFFF or len(nonce) > 0xFFFF:
        raise ValueError("Salt and nonce too large")
    
    packed = bytearray()
    packed.extend(len(salt).to_bytes(2, byteorder='big'))
    packed.extend(salt)
    packed.extend(len(nonce).to_bytes(2, byteorder='big'))
    packed.extend(nonce)
    packed.extend(ciphertext)
    
    return bytes(packed)


def unpack_encrypted_data(packed_data: bytes) -> Tuple[bytes, bytes, bytes]:
    """Unpack salt, nonce, and ciphertext from a binary blob.
    
    Args:
        packed_data: Binary data from pack_encrypted_data()
        
    Returns:
        Tuple of (salt, nonce, ciphertext)
        
    Raises:
        ValueError: If data is malformed
    """
    if len(packed_data) < 8:  # Minimum: 2 + 2 + 4 bytes for empty salt/nonce
        raise ValueError("Packed data too short")
    
    offset = 0
    
    # Read salt length and salt
    salt_len = int.from_bytes(packed_data[offset:offset+2], byteorder='big')
    offset += 2
    
    if offset + salt_len > len(packed_data):
        raise ValueError("Malformed packed data: salt length exceeds data size")
    
    salt = packed_data[offset:offset+salt_len]
    offset += salt_len
    
    # Read nonce length and nonce
    nonce_len = int.from_bytes(packed_data[offset:offset+2], byteorder='big')
    offset += 2
    
    if offset + nonce_len > len(packed_data):
        raise ValueError("Malformed packed data: nonce length exceeds data size")
    
    nonce = packed_data[offset:offset+nonce_len]
    offset += nonce_len
    
    # Rest is ciphertext
    ciphertext = packed_data[offset:]
    
    if not ciphertext:
        raise ValueError("Malformed packed data: no ciphertext")
    
    return salt, nonce, ciphertext
