"""File metadata operations."""

import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, Any


class FileMetadata:
    """Handles file metadata operations."""

    @staticmethod
    def calculate_hash(file_path: Path, chunk_size: int = 8192) -> str:
        """
        Calculate MD5 hash of a file.
        
        Args:
            file_path: Path to file
            chunk_size: Size of chunks to read
            
        Returns:
            MD5 hash as hex string
        """
        md5 = hashlib.md5()
        with open(file_path, 'rb') as f:
            while chunk := f.read(chunk_size):
                md5.update(chunk)
        return md5.hexdigest()

    @staticmethod
    def needs_update(local_path: Path, drive_file: Dict[str, Any]) -> bool:
        """
        Determine if local file needs updating.
        
        Args:
            local_path: Path to local file
            drive_file: Drive file metadata
            
        Returns:
            True if file needs update
        """
        if not local_path.exists():
            return True

        # Compare modification times
        local_mtime = datetime.fromtimestamp(local_path.stat().st_mtime)
        drive_mtime = datetime.fromisoformat(
            drive_file['modifiedTime'].replace('Z', '+00:00')
        )

        return drive_mtime > local_mtime

    @staticmethod
    def is_newer(file1_mtime: datetime, file2_mtime: datetime) -> bool:
        """
        Check if file1 is newer than file2.
        
        Args:
            file1_mtime: Modification time of first file
            file2_mtime: Modification time of second file
            
        Returns:
            True if file1 is newer
        """
        return file1_mtime > file2_mtime
