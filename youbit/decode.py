from pathlib import Path
from typing import Union
import shutil
import gzip

from youbit.tempdir import TempDir
from youbit.metadata import Metadata
from youbit.ecc.ecc import remove_ecc
from youbit.detransform import pixels_to_bytes
from youbit.download import Downloader
from youbit.video import VideoDecoder
from youbit.encryption import (
    decrypt_data,
    unpack_encrypted_data,
)


def download_and_decode(url: str, output_dir: Path) -> Path:
    output_dir = Path(output_dir)
    if not output_dir.exists() or not output_dir.is_dir():
        raise ValueError(f"'{output_dir}' is not a valid directory.")

    tempdir = TempDir()
    downloader = Downloader(url)

    download_path = tempdir.path / "downloaded"
    downloader.download(download_path)

    output_path = decode_local(download_path, output_dir, downloader.youbit_metadata)
    tempdir.close()
    return output_path


def decode_local(
    input_file: Union[Path, str], output_dir: Union[Path, str], metadata: Metadata
) -> Path:
    input_file, output_dir = Path(input_file), Path(output_dir)
    if not input_file.exists() or not input_file.is_file():
        raise ValueError(f"'{input_file}' is not a valid file location.")
    if not output_dir.exists() or not output_dir.is_dir():
        raise ValueError(f"'{output_dir}' is not a valid directory.")

    tempdir = TempDir()
    still_zipped_path = tempdir.path / "bin.gz"
    settings = metadata.settings

    video_decoder = VideoDecoder(input_file, metadata.settings)
    with open(still_zipped_path, "wb") as file:
        chunk_size = 255_000_000  # Must be factor of 255 and 8.
        while True:
            pixeldata_arr = video_decoder.extract_pixeldata(chunk_size)
            if not pixeldata_arr.size:
                break
            bytes_arr = pixels_to_bytes(pixeldata_arr, settings.bits_per_pixel)
            if settings.ecc_symbols:
                bytes_arr = remove_ecc(bytes_arr.tobytes(), settings.ecc_symbols)
            file.write(bytes_arr)
    video_decoder.close()

    # Handle decryption if needed
    if metadata.encryption_enabled:
        encrypted_path = still_zipped_path
        still_zipped_path = tempdir.path / "decrypted.bin"
        _decrypt_file(encrypted_path, still_zipped_path, metadata)

    output_path = _create_valid_path(output_dir, metadata)
    _unzip_file(still_zipped_path, output_path)
    tempdir.close()
    return output_path


def _decrypt_file(
    encrypted_path: Path, output_path: Path, metadata: Metadata
) -> None:
    """Decrypt a file that was encrypted during encoding.
    
    Args:
        encrypted_path: Path to encrypted file (contains packed salt + nonce + ciphertext)
        output_path: Path to write decrypted data
        metadata: Metadata containing encryption salt and settings
        
    Raises:
        ValueError: If decryption fails or password is incorrect
    """
    if not metadata.encryption_enabled:
        raise ValueError("File metadata indicates encryption is not enabled")
    
    if not metadata.encryption_salt:
        raise ValueError("Encryption salt not found in metadata")
    
    # Read encrypted data
    with open(encrypted_path, "rb") as f:
        packed_data = f.read()
    
    # Unpack to get salt, nonce, and ciphertext
    salt, nonce, ciphertext = unpack_encrypted_data(packed_data)
    
    # Prompt for password
    password = _prompt_for_password()
    
    # Decrypt
    try:
        plaintext = decrypt_data(ciphertext, password, salt, nonce)
    except ValueError as e:
        raise ValueError(
            f"Decryption failed. Check that you entered the correct password. Details: {str(e)}"
        )
    
    # Write decrypted data
    with open(output_path, "wb") as f:
        f.write(plaintext)


def _prompt_for_password() -> str:
    """Prompt user for decryption password (securely, without echoing).
    
    Returns:
        str: Password entered by user
    """
    import getpass
    
    password = getpass.getpass("Enter decryption password: ")
    return password


def _unzip_file(input_file: Path, output_path: Path) -> None:
    with gzip.open(input_file, "rb") as f_in, open(output_path, "wb") as f_out:
        shutil.copyfileobj(f_in, f_out)


def _create_valid_path(directory: Path, metadata: Metadata) -> Path:
    """Given a directory, returns a usable filepath within it."""
    original_filename = Path(metadata.filename)
    output = directory / original_filename
    i = 0
    while output.exists():
        i += 1
        output = Path(
            output.parent
            / (original_filename.stem + f"({i})" + original_filename.suffix)
        )
    return output
