# YouBit Password-Based Encryption

This document describes the password-based encryption feature added to YouBit.

## Overview

YouBit now supports optional password-based encryption for files before they are encoded into video. This allows you to protect sensitive data with a password while storing it in a YouTube video.

**Encryption is disabled by default.** You must explicitly provide a password to enable it.

## How It Works

### Encryption Process (Encoding)

1. **File Compression**: Your original file is compressed with gzip
2. **Encryption** (if password provided):
   - A random salt is generated (16 bytes)
   - Your password is derived into a 256-bit encryption key using PBKDF2 with SHA-256 (100,000 iterations)
   - The compressed data is encrypted using AES-256-GCM (authenticated encryption)
   - The salt and nonce are packed with the ciphertext
3. **Error Correction**: Optional Reed-Solomon error correction is applied
4. **Video Encoding**: The data is encoded into a video using LSB steganography
5. **Metadata Storage**: Encryption information is stored in the metadata (included in video description)

### Decryption Process (Decoding)

1. **Video Decoding**: The video is decoded to recover the data
2. **Error Correction**: Optional Reed-Solomon error correction is applied
3. **Decryption** (if file is encrypted):
   - You are prompted for the password
   - The password is derived into the decryption key using the stored salt
   - The ciphertext is decrypted using AES-256-GCM (authentication is verified)
4. **Decompression**: The data is decompressed with gzip to recover the original file

## Usage

### Encoding with Encryption

```bash
# Encode a file locally with password protection
youbit encode myfile.pdf output_dir --password "my_secure_password"

# Upload to YouTube with password protection
youbit upload myfile.pdf firefox --password "my_secure_password"
```

### Encoding without Encryption (Default)

```bash
# Encode without any password (no encryption)
youbit encode myfile.pdf output_dir

# Upload without encryption
youbit upload myfile.pdf firefox
```

### Decoding with Encryption

When you decode a file that was encrypted, you will be prompted for the password:

```bash
youbit decode video.mp4 output_dir <metadata_base64_string>
# You will be prompted: "Enter decryption password: "
# Enter your password (input is hidden)
```

If you enter the wrong password, decryption will fail with a clear error message.

## Security Considerations

### Strengths

- **AES-256-GCM**: Industry-standard authenticated encryption
  - 256-bit key (unbreakable with current technology)
  - Authenticated encryption (detects tampering)
  - Random nonce for each encryption (prevents patterns)

- **PBKDF2 Key Derivation**: Password is strengthened
  - 100,000 iterations of SHA-256 (slow to crack)
  - Random salt (prevents rainbow table attacks)
  - Each file has its own salt

- **Authentication Tag**: Ensures data integrity
  - Decryption fails if file is corrupted or tampered with
  - Password verification happens during decryption

### Important Warnings ⚠️

1. **Password Strength**: Use a strong password (12+ characters, mix of upper/lower/numbers/symbols)
   - Weak passwords can be brute-forced
   - Use a password manager to generate random passwords

2. **Password Storage**: 
   - Do NOT store passwords in plain text
   - Do NOT include passwords in commit messages or code
   - Share passwords through secure channels only

3. **Metadata**: 
   - The encryption algorithm and salt ARE visible in metadata (this is normal)
   - The password is NEVER stored anywhere
   - Without the password, the encrypted data cannot be recovered

4. **Loss of Password**:
   - If you lose your password, the encrypted file is unrecoverable
   - There is no "forgot password" recovery
   - Keep backups of important passwords

5. **Video Platform**:
   - YouTube may compress/re-encode the video
   - Error correction (ECC) symbols protect against this
   - Always test decoding after uploading

## Technical Details

### Cryptographic Parameters

| Parameter | Value | Notes |
|-----------|-------|-------|
| Encryption Algorithm | AES-256-GCM | NIST-approved authenticated encryption |
| Key Size | 256 bits | Unbreakable with current technology |
| Key Derivation | PBKDF2-SHA256 | 100,000 iterations |
| Salt Length | 16 bytes | Random per file |
| Nonce Length | 12 bytes | Random per encryption |
| Authentication Tag | 16 bytes | Included in ciphertext |

### Data Format

The encrypted file is stored with this binary format:

```
[2 bytes: salt length] [salt] [2 bytes: nonce length] [nonce] [ciphertext + auth tag]
```

This allows the decoder to extract the salt and nonce needed for decryption.

### File Size

Encryption adds minimal overhead:
- Salt: 16 bytes
- Nonce: 12 bytes
- Authentication tag: 16 bytes
- **Total overhead: ~44 bytes per file**

## Testing

### Unit Tests

Comprehensive unit tests are included in `tests/test_encryption.py`:

```bash
# Run encryption tests
pytest tests/test_encryption.py -v
```

Tests cover:
- ✅ Salt generation and randomness
- ✅ Key derivation determinism
- ✅ Encryption/decryption roundtrips
- ✅ Large file handling (10MB+)
- ✅ Wrong password detection
- ✅ Data tampering detection
- ✅ Packing/unpacking of encrypted data
- ✅ End-to-end workflow

### Manual Testing

```bash
# 1. Create a test file
echo "Secret message" > secret.txt

# 2. Encode with password
youbit encode secret.txt test_output --password "test_password_123"

# 3. Try to decode
youbit decode YOUBIT-secret.txt.mp4 decoded_output <metadata_from_readme>
# Enter password: test_password_123
# File should be recovered!

# 4. Verify the file
diff secret.txt decoded_output/secret.txt
# Should show no differences
```

## Troubleshooting

### "Decryption failed. Check that you entered the correct password."

**Causes:**
- Wrong password entered
- File is corrupted
- File was tampered with
- Metadata doesn't match the video

**Solutions:**
- Double-check your password
- Try re-downloading the video
- Verify the metadata string is correct
- Ensure no characters were modified when copying metadata

### "Encryption salt not found in metadata"

**Causes:**
- Metadata is corrupted
- File wasn't encrypted during encoding

**Solutions:**
- Get the metadata from the original video description
- If decoding a file that wasn't encrypted, don't provide a password

### Performance Issues

- Encryption adds ~5-10% to encoding time
- Decryption adds ~5-10% to decoding time
- PBKDF2 key derivation takes ~100ms per file (intentional, for security)

## Backward Compatibility

- **Non-encrypted files**: Work exactly as before
- **Old metadata**: Still compatible (encryption fields are optional)
- **Without --password flag**: Encryption is disabled (no performance impact)

## Future Improvements

Possible future enhancements:
- [ ] Support for different encryption algorithms
- [ ] Key file support (instead of password)
- [ ] Passphrase-based encryption with custom PBKDF2 iterations
- [ ] Encrypted metadata option
- [ ] Two-factor authentication support

## References

- [AES-256-GCM](https://en.wikipedia.org/wiki/Galois/Counter_Mode)
- [PBKDF2](https://en.wikipedia.org/wiki/PBKDF2)
- [cryptography.io](https://cryptography.io/) - Python cryptography library used
