"""File compression handling."""

import gzip
import shutil
from pathlib import Path
from typing import Tuple
from rich.console import Console

from gdrive_sync.utils.constants import COMPRESSION_THRESHOLD, COMPRESSIBLE_EXTENSIONS

console = Console()


class CompressionHandler:
    """Handles file compression and decompression."""

    @staticmethod
    def should_compress(file_path: Path, mime_type: str = None) -> bool:
        """
        Determine if a file should be compressed.
        
        Args:
            file_path: Path to the file
            mime_type: MIME type of the file
            
        Returns:
            True if file should be compressed
        """
        # Check file size
        if file_path.stat().st_size < COMPRESSION_THRESHOLD:
            return False

        # Check if already compressed
        if file_path.suffix.lower() in {'.gz', '.zip', '.bz2', '.7z', '.rar', '.tar'}:
            return False

        # Check if file type is compressible
        if file_path.suffix.lower() in COMPRESSIBLE_EXTENSIONS:
            return True

        # Check MIME type for text-based files
        if mime_type and mime_type.startswith('text/'):
            return True

        return False

    @staticmethod
    def compress_file(source: Path, destination: Path) -> Tuple[bool, int, int]:
        """
        Compress a file using gzip.
        
        Args:
            source: Source file path
            destination: Destination file path
            
        Returns:
            Tuple of (success, original_size, compressed_size)
        """
        try:
            original_size = source.stat().st_size

            with open(source, 'rb') as f_in:
                with gzip.open(destination, 'wb', compresslevel=6) as f_out:
                    shutil.copyfileobj(f_in, f_out)

            compressed_size = destination.stat().st_size
            return True, original_size, compressed_size

        except Exception as e:
            console.print(f"[red]Compression error: {e}[/red]")
            return False, 0, 0

    @staticmethod
    def decompress_file(source: Path, destination: Path) -> Tuple[bool, int]:
        """
        Decompress a gzip file.
        
        Args:
            source: Source compressed file
            destination: Destination decompressed file
            
        Returns:
            Tuple of (success, decompressed_size)
        """
        try:
            with gzip.open(source, 'rb') as f_in:
                with open(destination, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)

            decompressed_size = destination.stat().st_size
            return True, decompressed_size

        except Exception as e:
            console.print(f"[red]Decompression error: {e}[/red]")
            return False, 0
