"""
Comprehensive unit tests for the encryption module.

Tests cover:
- Happy path encryption/decryption
- Edge cases (large files, empty data)
- Error handling (wrong password, corrupted data)
- Data integrity (packing/unpacking)
- Determinism (reproducible key derivation)
"""
import pytest
import os
from youbit.encryption import (
    generate_salt,
    derive_key_from_password,
    encrypt_data,
    decrypt_data,
    pack_encrypted_data,
    unpack_encrypted_data,
    SALT_LENGTH,
    NONCE_LENGTH,
    KEY_LENGTH,
)


class TestSaltGeneration:
    """Test salt generation."""
    
    def test_generate_salt_length(self):
        """Generated salt should be correct length."""
        salt = generate_salt()
        assert len(salt) == SALT_LENGTH
        assert isinstance(salt, bytes)
    
    def test_generate_salt_randomness(self):
        """Generated salts should be different each time."""
        salt1 = generate_salt()
        salt2 = generate_salt()
        assert salt1 != salt2


class TestKeyDerivation:
    """Test password-based key derivation."""
    
    def test_derive_key_length(self):
        """Derived key should be correct length."""
        password = "test_password"
        salt = generate_salt()
        key = derive_key_from_password(password, salt)
        assert len(key) == KEY_LENGTH
        assert isinstance(key, bytes)
    
    def test_derive_key_deterministic(self):
        """Same password + salt should produce same key."""
        password = "test_password"
        salt = generate_salt()
        
        key1 = derive_key_from_password(password, salt)
        key2 = derive_key_from_password(password, salt)
        
        assert key1 == key2
    
    def test_derive_key_different_passwords(self):
        """Different passwords should produce different keys."""
        salt = generate_salt()
        
        key1 = derive_key_from_password("password1", salt)
        key2 = derive_key_from_password("password2", salt)
        
        assert key1 != key2
    
    def test_derive_key_different_salts(self):
        """Different salts should produce different keys."""
        password = "same_password"
        
        key1 = derive_key_from_password(password, generate_salt())
        key2 = derive_key_from_password(password, generate_salt())
        
        assert key1 != key2
    
    def test_derive_key_empty_password_fails(self):
        """Empty password should raise ValueError."""
        salt = generate_salt()
        with pytest.raises(ValueError, match="Password cannot be empty"):
            derive_key_from_password("", salt)
    
    def test_derive_key_invalid_salt_fails(self):
        """Invalid salt should raise ValueError."""
        password = "test_password"
        
        # Too short
        with pytest.raises(ValueError, match="Salt must be exactly"):
            derive_key_from_password(password, b"short")
        
        # Too long
        with pytest.raises(ValueError, match="Salt must be exactly"):
            derive_key_from_password(password, b"x" * 32)
        
        # Empty
        with pytest.raises(ValueError, match="Salt must be exactly"):
            derive_key_from_password(password, b"")


class TestEncryption:
    """Test encryption functionality."""
    
    def test_encrypt_returns_correct_types(self):
        """encrypt_data should return salt, nonce, ciphertext."""
        data = b"test data"
        password = "test_password"
        
        salt, nonce, ciphertext = encrypt_data(data, password)
        
        assert isinstance(salt, bytes)
        assert isinstance(nonce, bytes)
        assert isinstance(ciphertext, bytes)
        assert len(salt) == SALT_LENGTH
        assert len(nonce) == NONCE_LENGTH
    
    def test_encrypt_different_ciphertexts(self):
        """Same data encrypted twice should produce different ciphertexts (different nonce)."""
        data = b"test data"
        password = "test_password"
        
        salt1, nonce1, ct1 = encrypt_data(data, password)
        salt2, nonce2, ct2 = encrypt_data(data, password)
        
        # Different random components
        assert salt1 != salt2
        assert nonce1 != nonce2
        assert ct1 != ct2
    
    def test_encrypt_empty_data_fails(self):
        """Encrypting empty data should raise ValueError."""
        with pytest.raises(ValueError, match="Data cannot be empty"):
            encrypt_data(b"", "password")
    
    def test_encrypt_empty_password_fails(self):
        """Encrypting with empty password should raise ValueError."""
        with pytest.raises(ValueError, match="Password cannot be empty"):
            encrypt_data(b"data", "")
    
    def test_encrypt_large_data(self):
        """Should handle large data (10MB)."""
        data = b"x" * (10 * 1024 * 1024)  # 10MB
        password = "test_password"
        
        salt, nonce, ciphertext = encrypt_data(data, password)
        
        assert len(salt) == SALT_LENGTH
        assert len(nonce) == NONCE_LENGTH
        assert len(ciphertext) > len(data)  # Includes authentication tag
    
    def test_encrypt_binary_data(self):
        """Should handle arbitrary binary data."""
        data = bytes(range(256)) * 100  # All possible byte values
        password = "test_password"
        
        salt, nonce, ciphertext = encrypt_data(data, password)
        
        assert isinstance(ciphertext, bytes)
        assert len(ciphertext) > 0


class TestDecryption:
    """Test decryption functionality."""
    
    def test_decrypt_returns_bytes(self):
        """decrypt_data should return bytes."""
        data = b"test data"
        password = "test_password"
        
        salt, nonce, ciphertext = encrypt_data(data, password)
        decrypted = decrypt_data(ciphertext, password, salt, nonce)
        
        assert isinstance(decrypted, bytes)
    
    def test_decrypt_empty_ciphertext_fails(self):
        """Decrypting empty ciphertext should fail."""
        salt = generate_salt()
        nonce = os.urandom(NONCE_LENGTH)
        
        with pytest.raises(ValueError, match="Data cannot be empty"):
            decrypt_data(b"", "password", salt, nonce)
    
    def test_decrypt_invalid_salt_fails(self):
        """Decrypting with wrong salt format should fail."""
        data = b"test data"
        password = "test_password"
        salt, nonce, ciphertext = encrypt_data(data, password)
        
        with pytest.raises(ValueError, match="Salt must be exactly"):
            decrypt_data(ciphertext, password, b"short", nonce)
    
    def test_decrypt_invalid_nonce_fails(self):
        """Decrypting with wrong nonce format should fail."""
        data = b"test data"
        password = "test_password"
        salt, nonce, ciphertext = encrypt_data(data, password)
        
        with pytest.raises(ValueError, match="Nonce must be exactly"):
            decrypt_data(ciphertext, password, salt, b"short")


class TestEncryptDecryptRoundtrip:
    """Test that data survives encryption and decryption."""
    
    def test_roundtrip_simple_data(self):
        """Simple text data should roundtrip."""
        data = b"Hello, World!"
        password = "test_password"
        
        salt, nonce, ciphertext = encrypt_data(data, password)
        decrypted = decrypt_data(ciphertext, password, salt, nonce)
        
        assert decrypted == data
    
    def test_roundtrip_binary_data(self):
        """Binary data with all byte values should roundtrip."""
        data = bytes(range(256)) * 100
        password = "test_password"
        
        salt, nonce, ciphertext = encrypt_data(data, password)
        decrypted = decrypt_data(ciphertext, password, salt, nonce)
        
        assert decrypted == data
    
    def test_roundtrip_large_data(self):
        """Large data should roundtrip."""
        data = b"x" * (10 * 1024 * 1024)  # 10MB
        password = "test_password"
        
        salt, nonce, ciphertext = encrypt_data(data, password)
        decrypted = decrypt_data(ciphertext, password, salt, nonce)
        
        assert decrypted == data
        assert len(decrypted) == len(data)
    
    def test_roundtrip_empty_password_fails(self):
        """Empty password should fail during decryption."""
        data = b"test"
        password = "correct"
        
        salt, nonce, ciphertext = encrypt_data(data, password)
        
        with pytest.raises(ValueError, match="Password cannot be empty"):
            decrypt_data(ciphertext, "", salt, nonce)


class TestDataTamperingDetection:
    """Test that tampering with ciphertext is detected."""
    
    def test_tampered_ciphertext_detected(self):
        """Modified ciphertext should fail decryption."""
        data = b"secret message"
        password = "test_password"
        
        salt, nonce, ciphertext = encrypt_data(data, password)
        
        # Tamper with ciphertext
        tampered = bytearray(ciphertext)
        tampered[0] ^= 0xFF  # Flip first byte
        
        with pytest.raises(ValueError, match="Decryption failed"):
            decrypt_data(bytes(tampered), password, salt, nonce)
    
    def test_wrong_password_detected(self):
        """Wrong password should fail decryption."""
        data = b"secret message"
        password = "correct_password"
        
        salt, nonce, ciphertext = encrypt_data(data, password)
        
        with pytest.raises(ValueError, match="Decryption failed"):
            decrypt_data(ciphertext, "wrong_password", salt, nonce)
    
    def test_wrong_nonce_detected(self):
        """Wrong nonce should fail decryption."""
        data = b"secret message"
        password = "test_password"
        
        salt, nonce, ciphertext = encrypt_data(data, password)
        
        # Use different nonce
        wrong_nonce = os.urandom(NONCE_LENGTH)
        
        with pytest.raises(ValueError, match="Decryption failed"):
            decrypt_data(ciphertext, password, salt, wrong_nonce)
    
    def test_wrong_salt_detected(self):
        """Wrong salt should fail decryption (produces wrong key)."""
        data = b"secret message"
        password = "test_password"
        
        salt, nonce, ciphertext = encrypt_data(data, password)
        
        # Use different salt
        wrong_salt = generate_salt()
        
        with pytest.raises(ValueError, match="Decryption failed"):
            decrypt_data(ciphertext, password, wrong_salt, nonce)


class TestPackingUnpacking:
    """Test packing and unpacking encrypted data."""
    
    def test_pack_unpack_roundtrip(self):
        """Packed data should unpack to original components."""
        salt = b"a" * SALT_LENGTH
        nonce = b"b" * NONCE_LENGTH
        ciphertext = b"encrypted_data_here"
        
        packed = pack_encrypted_data(salt, nonce, ciphertext)
        unpacked_salt, unpacked_nonce, unpacked_ct = unpack_encrypted_data(packed)
        
        assert unpacked_salt == salt
        assert unpacked_nonce == nonce
        assert unpacked_ct == ciphertext
    
    def test_pack_large_ciphertext(self):
        """Should handle large ciphertext."""
        salt = b"a" * SALT_LENGTH
        nonce = b"b" * NONCE_LENGTH
        ciphertext = b"x" * (10 * 1024 * 1024)  # 10MB
        
        packed = pack_encrypted_data(salt, nonce, ciphertext)
        unpacked_salt, unpacked_nonce, unpacked_ct = unpack_encrypted_data(packed)
        
        assert unpacked_ct == ciphertext
        assert len(unpacked_ct) == len(ciphertext)
    
    def test_unpack_malformed_data_fails(self):
        """Malformed packed data should raise ValueError."""
        # Data too short
        with pytest.raises(ValueError, match="Packed data too short"):
            unpack_encrypted_data(b"x")
        
        # Missing ciphertext
        packed = bytearray()
        packed.extend((0).to_bytes(2, byteorder='big'))  # salt length = 0
        packed.extend((0).to_bytes(2, byteorder='big'))  # nonce length = 0
        
        with pytest.raises(ValueError, match="Malformed packed data: no ciphertext"):
            unpack_encrypted_data(bytes(packed))
        
        # Salt length exceeds data
        packed = bytearray()
        packed.extend((100).to_bytes(2, byteorder='big'))  # claim 100 bytes salt
        packed.extend(b"x" * 10)  # but only have 10
        
        with pytest.raises(ValueError, match="Malformed packed data: salt length exceeds"):
            unpack_encrypted_data(bytes(packed))


class TestIntegrationWithEncryption:
    """Integration tests combining encryption with packing."""
    
    def test_full_encrypt_pack_unpack_decrypt(self):
        """Full workflow: encrypt → pack → unpack → decrypt."""
        original_data = b"This is a test message with important data!"
        password = "my_secure_password_123"
        
        # Encrypt
        salt, nonce, ciphertext = encrypt_data(original_data, password)
        
        # Pack
        packed = pack_encrypted_data(salt, nonce, ciphertext)
        
        # Unpack
        unpacked_salt, unpacked_nonce, unpacked_ct = unpack_encrypted_data(packed)
        
        # Decrypt
        decrypted = decrypt_data(unpacked_ct, password, unpacked_salt, unpacked_nonce)
        
        assert decrypted == original_data
    
    def test_full_workflow_large_file(self):
        """Full workflow with large file."""
        original_data = b"x" * (5 * 1024 * 1024)  # 5MB
        password = "test"
        
        salt, nonce, ciphertext = encrypt_data(original_data, password)
        packed = pack_encrypted_data(salt, nonce, ciphertext)
        unpacked_salt, unpacked_nonce, unpacked_ct = unpack_encrypted_data(packed)
        decrypted = decrypt_data(unpacked_ct, password, unpacked_salt, unpacked_nonce)
        
        assert decrypted == original_data
        assert len(decrypted) == len(original_data)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
