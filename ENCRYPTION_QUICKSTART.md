# Encryption Quick Start Guide

Get started with YouBit's password-based encryption in 5 minutes!

## Installation

Make sure you have YouBit installed:

```bash
pip install youbit
```

## Basic Usage

### 1. Encode a File with Password

```bash
youbit encode myfile.txt output_folder --password "MySecurePassword123!"
```

**What happens:**
- Your file is compressed (gzip)
- Compressed data is encrypted with your password (AES-256)
- Encrypted data is encoded into a video file
- Video is saved in `output_folder`

### 2. Upload to YouTube with Encryption

```bash
youbit upload myfile.txt firefox --password "MySecurePassword123!"
```

**What happens:**
- Same as above, but uploads directly to YouTube
- Metadata with decryption info is included in video description
- Video is private by default (you set permissions on YouTube)

### 3. Decode a File with Password

```bash
youbit decode video.mp4 output_folder <metadata_string>
```

**What happens:**
- You'll be prompted: `Enter decryption password:`
- Enter your password (input is hidden)
- File is decrypted and saved to `output_folder`

## Common Examples

### Protecting a PDF

```bash
# Encode with password
youbit encode document.pdf ./encoded_videos --password "SecureDoc2024!"

# Later, decode it
youbit decode YOUBIT-document.pdf.mp4 ./decoded --password "SecureDoc2024!"
```

### Encrypting Sensitive Data

```bash
# Use a strong password
youbit encode data.csv ./videos --password "C0mpl3x!P@ssw0rd#2024"

# Share the video and tell recipient the password (via secure channel)
```

### Batch Encoding

```bash
# Encode multiple files
for file in *.txt; do
    youbit encode "$file" ./videos --password "CommonPassword"
done
```

## Password Tips

### ✅ Good Passwords
- `MyP@ssw0rd!2024#Secure` - Long, mixed characters
- `correct-horse-battery-staple` - Memorable but long
- `#8mK$vL2!xN9pQ@` - Random characters

### ❌ Weak Passwords
- `password` - Too common
- `123456` - Numbers only
- `qwerty` - Keyboard pattern
- Your name or birthday

### Best Practices
1. Use **12+ characters** (longer is better)
2. Mix **uppercase, lowercase, numbers, symbols**
3. Avoid **dictionary words** and **personal info**
4. Use a **password manager** (1Password, Bitwarden, etc.)
5. Never share passwords in emails or chat

## Storage Format

When you encode with a password:

```
Your File (e.g., document.pdf)
    ↓
Gzip Compression
    ↓
AES-256 Encryption (with your password)
    ↓
Error Correction (Reed-Solomon)
    ↓
Video Encoding (LSB Steganography)
    ↓
Output: YOUBIT-document.pdf.mp4 or YouTube Video
```

The password is **never stored**. Only the encrypted data and a salt (for key derivation) are stored.

## Decoding Process

```
YouTube Video or Video File
    ↓
Video Decoding
    ↓
Error Correction Removal
    ↓
[Enter Password]
    ↓
AES-256 Decryption (validates password)
    ↓
Gzip Decompression
    ↓
Output: Your original file
```

If you enter the wrong password, decryption fails immediately.

## Troubleshooting

### "Decryption failed. Check that you entered the correct password."

**Solutions:**
1. Make sure you're using the **exact same password**
2. Check for **CAPS LOCK**
3. Verify you have the **correct video/metadata**
4. Try re-downloading the video from YouTube

### "Encryption password cannot be an empty string"

**Solutions:**
1. Provide a password: `--password "your_password"`
2. Or remove the flag entirely to skip encryption

### "File saved at..." but I can't decrypt it later

**Prevention:**
1. **Save your password** somewhere safe
2. **Write down the password** (or use a password manager)
3. **Test decryption** immediately after encoding
4. **Back up** the original file

## Advanced Usage

### Using Environment Variables

```bash
# Set password in environment
export YOUBIT_PASSWORD="MyPassword123!"

# Use in scripts
youbit encode myfile.txt output --password "$YOUBIT_PASSWORD"
```

### Programmatic Usage (Python)

```python
from youbit import Encoder
from youbit.settings import Settings

# Create settings with password
settings = Settings(encryption_password="MyPassword123!")

# Encode with encryption
encoder = Encoder("myfile.txt", settings)
output_path = encoder.encode_local("output_dir")

print(f"Encoded to: {output_path}")
```

### Decoding Programmatically

```python
from youbit import decode_local, Metadata

# Load metadata (usually from video description)
metadata = Metadata.create_from_base64(metadata_string)

# Decode (will prompt for password if encrypted)
output_path = decode_local("video.mp4", "output_dir", metadata)

print(f"Decoded to: {output_path}")
```

## Security Guarantees

✅ **What's Protected:**
- File content is encrypted with AES-256-GCM
- No one can see your data without the password
- Password is never stored or transmitted
- Tampering is detected automatically

⚠️ **What's Not Protected:**
- Weak passwords can be guessed
- YouTube could theoretically see the video
- Your computer could be compromised
- Loss of password means lost data

## Video Quality

Encoding to video causes some quality loss:
- **Default: 1920x1080 resolution**
- **Adjustable with `--res` flag** (HD, QHD, UHD)
- **Error correction recovers most data** (default: 32 ECC symbols)

For important data:
```bash
youbit encode myfile.txt output --password "pwd" --res UHD --ecc 64
```

## Sharing Encrypted Videos

1. **Upload to YouTube** (private or unlisted)
2. **Share video link** via any channel
3. **Share password** via **secure channel only**:
   - ✅ In-person conversation
   - ✅ Encrypted message (Signal, WhatsApp)
   - ❌ Email (not secure)
   - ❌ Unencrypted chat

## Limitations & Considerations

- **File size**: Encoded size ≈ 3-5× original size (due to video encoding)
- **Time**: Encoding takes ~5-15 minutes depending on file size
- **Password memory**: You must remember your password
- **Video platform**: YouTube compression might affect decoding (ECC helps)

## Next Steps

1. **Read the full guide**: `ENCRYPTION.md` for detailed info
2. **Run tests**: `pytest tests/test_encryption.py` to verify it works
3. **Try encoding**: Encode a test file and decode it
4. **Share securely**: Share encrypted videos with confidence

## Support

- **Issues**: Report bugs on GitHub
- **Questions**: Check `ENCRYPTION.md` FAQ section
- **Suggestions**: Open a GitHub discussion

## Examples Repository

Check the `examples/` directory for more use cases:
- `encode_with_password.py` - Python example
- `batch_encrypt.sh` - Batch encoding script
- `share_securely.md` - Secure sharing guide

---

**Remember**: Your password is the only thing protecting your data. Keep it safe! 🔒
