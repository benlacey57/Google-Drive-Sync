"""Tests for file metadata operations."""

import pytest
from pathlib import Path
from datetime import datetime, timezone

from gdrive_sync.infrastructure.storage.metadata import FileMetadata


class TestFileMetadata:
    """Tests for FileMetadata."""

    def test_calculate_hash(self, temp_dir):
        """Test MD5 hash calculation."""
        test_file = temp_dir / 'test.txt'
        test_file.write_text('Test content for hashing')
        
        hash1 = FileMetadata.calculate_hash(test_file)
        assert isinstance(hash1, str)
        assert len(hash1) == 32  # MD5 hash length
        
        # Same content should produce same hash
        hash2 = FileMetadata.calculate_hash(test_file)
        assert hash1 == hash2
        
        # Different content should produce different hash
        test_file.write_text('Different content')
        hash3 = FileMetadata.calculate_hash(test_file)
        assert hash1 != hash3

    def test_calculate_hash_large_file(self, temp_dir):
        """Test hash calculation for large file."""
        large_file = temp_dir / 'large.bin'
        # Create 5MB file
        large_file.write_bytes(b'x' * (5 * 1024 * 1024))
        
        hash_result = FileMetadata.calculate_hash(large_file)
        assert isinstance(hash_result, str)
        assert len(hash_result) == 32

    def test_needs_update_file_not_exists(self, temp_dir):
        """Test needs_update when local file doesn't exist."""
        local_file = temp_dir / 'nonexistent.txt'
        drive_file = {
            'modifiedTime': '2024-01-01T00:00:00Z'
        }
        
        assert FileMetadata.needs_update(local_file, drive_file) is True

    def test_needs_update_drive_newer(self, temp_dir):
        """Test needs_update when Drive file is newer."""
        local_file = temp_dir / 'old.txt'
        local_file.write_text('content')
        
        # Set file to be old
        import os
        import time
        old_time = time.time() - 86400  # 1 day ago
        os.utime(local_file, (old_time, old_time))
        
        drive_file = {
            'modifiedTime': datetime.now(timezone.utc).isoformat()
        }
        
        assert FileMetadata.needs_update(local_file, drive_file) is True

    def test_needs_update_local_newer(self, temp_dir):
        """Test needs_update when local file is newer."""
        local_file = temp_dir / 'new.txt'
        local_file.write_text('content')
        
        drive_file = {
            'modifiedTime': '2020-01-01T00:00:00Z'
        }
        
        assert FileMetadata.needs_update(local_file, drive_file) is False

    def test_is_newer(self):
        """Test is_newer comparison."""
        time1 = datetime(2024, 1, 1, 12, 0, 0)
        time2 = datetime(2024, 1, 1, 11, 0, 0)
        
        assert FileMetadata.is_newer(time1, time2) is True
        assert FileMetadata.is_newer(time2, time1) is False
        assert FileMetadata.is_newer(time1, time1) is False
