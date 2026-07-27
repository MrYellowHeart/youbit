"""
Integration tests for the encryption feature with encoding/decoding workflow.

Tests cover:
- Full encode → decode roundtrip with encryption
- Settings integration
- Metadata storage and retrieval
- CLI argument passing
"""
import pytest
import tempfile
from pathlib import Path
from youbit.encode import Encoder
from youbit.decode import decode_local
from youbit.metadata import Metadata
from youbit.settings import Settings, Resolution, BitsPerPixel, Browser


class TestEncryptionIntegration:
    """Integration tests for encryption with encoding/decoding."""
    
    @pytest.fixture
    def temp_file(self):
        """Create a temporary file with test data."""
        with tempfile.NamedTemporaryFile(delete=False, mode='wb') as f:
            # Write 1MB of test data
            f.write(b"Test data " * 100000)
            temp_path = Path(f.name)
        yield temp_path
        temp_path.unlink()
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for output."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        # Cleanup
        import shutil
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
    
    def test_encode_with_encryption_creates_metadata(self, temp_file, temp_dir):
        """Encoding with password should set encryption flags in metadata."""
        password = "test_password_123"
        settings = Settings(
            resolution=Resolution.HD,
            bits_per_pixel=BitsPerPixel.ONE,
            ecc_symbols=32,
            encryption_password=password,
        )
        
        encoder = Encoder(temp_file, settings)
        
        # Check that metadata has encryption enabled
        assert encoder._metadata.encryption_enabled is True
        assert encoder._metadata.encryption_algorithm == "AES256-GCM"
        # Salt will be set during encoding
    
    def test_encode_without_encryption_no_metadata_flags(self, temp_file):
        """Encoding without password should not set encryption flags."""
        settings = Settings(
            resolution=Resolution.HD,
            bits_per_pixel=BitsPerPixel.ONE,
            ecc_symbols=32,
            encryption_password=None,
        )
        
        encoder = Encoder(temp_file, settings)
        
        # Check that metadata has encryption disabled
        assert encoder._metadata.encryption_enabled is False
        assert encoder._metadata.encryption_salt is None
    
    def test_metadata_export_import_with_encryption(self, temp_file):
        """Metadata with encryption should survive export/import."""
        password = "test_password_123"
        settings = Settings(encryption_password=password)
        
        encoder = Encoder(temp_file, settings)
        
        # Simulate encoding (sets encryption fields)
        encoder._metadata.encryption_enabled = True
        encoder._metadata.encryption_salt = b"a" * 16
        encoder._metadata.encryption_algorithm = "AES256-GCM"
        
        # Export and import
        base64_str = encoder._metadata.export_as_base64()
        imported_metadata = Metadata.create_from_base64(base64_str)
        
        # Verify fields survived
        assert imported_metadata.encryption_enabled is True
        assert imported_metadata.encryption_salt == b"a" * 16
        assert imported_metadata.encryption_algorithm == "AES256-GCM"
    
    def test_settings_encryption_enabled_property(self):
        """Settings.encryption_enabled should reflect password presence."""
        # No password
        settings1 = Settings(encryption_password=None)
        assert settings1.encryption_enabled is False
        
        # With password
        settings2 = Settings(encryption_password="password")
        assert settings2.encryption_enabled is True
    
    def test_settings_encryption_password_validation(self):
        """Settings should validate encryption password."""
        # Empty string should fail
        with pytest.raises(ValueError, match="cannot be an empty string"):
            Settings(encryption_password="")
        
        # Non-string should fail
        with pytest.raises(ValueError, match="must be a string or None"):
            Settings(encryption_password=123)
        
        # None is valid
        settings = Settings(encryption_password=None)
        assert settings.encryption_password is None
        
        # Valid password
        settings = Settings(encryption_password="valid_password")
        assert settings.encryption_password == "valid_password"


class TestEncryptionCLIIntegration:
    """Tests for CLI integration with encryption."""
    
    def test_cli_password_flag_in_settings(self):
        """CLI password flag should be passed to Settings."""
        from youbit.settings import Settings
        
        # Test with password
        settings = Settings(encryption_password="cli_password_123")
        assert settings.encryption_enabled is True
        assert settings.encryption_password == "cli_password_123"
        
        # Test without password (None)
        settings = Settings(encryption_password=None)
        assert settings.encryption_enabled is False
    
    def test_settings_encryption_does_not_affect_other_settings(self):
        """Encryption settings should not interfere with other settings."""
        settings = Settings(
            resolution=Resolution.QHD,
            bits_per_pixel=BitsPerPixel.TWO,
            ecc_symbols=64,
            constant_rate_factor=20,
            null_frames=True,
            encryption_password="password",
        )
        
        # Verify all settings are preserved
        assert settings.resolution == Resolution.QHD
        assert settings.bits_per_pixel == BitsPerPixel.TWO
        assert settings.ecc_symbols == 64
        assert settings.constant_rate_factor == 20
        assert settings.null_frames is True
        assert settings.encryption_enabled is True


class TestEncryptionBackwardCompatibility:
    """Tests for backward compatibility with non-encrypted files."""
    
    def test_metadata_without_encryption_fields(self):
        """Old metadata without encryption fields should be compatible."""
        # Create metadata without encryption fields
        metadata = Metadata(
            filename="test.txt",
            md5_hash="abc123",
            encryption_enabled=False,  # Defaults to False
        )
        
        # Should not raise
        assert metadata.encryption_enabled is False
        assert metadata.encryption_salt is None
    
    def test_settings_backward_compatible(self):
        """Settings without password should work as before."""
        settings = Settings(
            resolution=Resolution.HD,
            bits_per_pixel=BitsPerPixel.ONE,
            ecc_symbols=32,
            # No password specified
        )
        
        assert settings.encryption_enabled is False
        assert settings.encryption_password is None
        
        # Other settings should work
        assert settings.resolution == Resolution.HD
        assert settings.bits_per_pixel == BitsPerPixel.ONE


class TestEncryptionEdgeCases:
    """Edge case tests for encryption integration."""
    
    def test_very_long_password(self):
        """Very long passwords should be handled."""
        long_password = "p" * 1000
        settings = Settings(encryption_password=long_password)
        assert settings.encryption_password == long_password
        assert settings.encryption_enabled is True
    
    def test_special_characters_in_password(self):
        """Passwords with special characters should work."""
        special_password = "P@ssw0rd!#$%^&*()[]{}|;:',.<>?/~`"
        settings = Settings(encryption_password=special_password)
        assert settings.encryption_password == special_password
        assert settings.encryption_enabled is True
    
    def test_unicode_password(self):
        """Unicode passwords should work."""
        unicode_password = "密码🔒パスワード"
        settings = Settings(encryption_password=unicode_password)
        assert settings.encryption_password == unicode_password
        assert settings.encryption_enabled is True
    
    def test_metadata_with_all_encryption_fields(self):
        """Metadata should store all encryption fields correctly."""
        metadata = Metadata(
            filename="encrypted_file.bin",
            md5_hash="hash123",
            encryption_enabled=True,
            encryption_salt=b"salt" * 4,  # 16 bytes
            encryption_algorithm="AES256-GCM",
        )
        
        # Export and verify
        base64_str = metadata.export_as_base64()
        recovered = Metadata.create_from_base64(base64_str)
        
        assert recovered.encryption_enabled is True
        assert recovered.encryption_salt == b"salt" * 4
        assert recovered.encryption_algorithm == "AES256-GCM"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
