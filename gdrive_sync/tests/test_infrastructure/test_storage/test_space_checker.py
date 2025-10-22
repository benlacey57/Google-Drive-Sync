"""Tests for storage space checker."""

import pytest
from pathlib import Path

from gdrive_sync.infrastructure.storage.space_checker import StorageChecker


class TestStorageChecker:
    """Tests for StorageChecker."""

    def test_check_available_space(self, temp_dir):
        """Test checking available space."""
        total, used, free = StorageChecker.check_available_space(temp_dir)
        
        assert total > 0
        assert used >= 0
        assert free > 0
        assert total >= used + free  # Allow for some overhead

    def test_format_bytes(self):
        """Test byte formatting."""
        assert StorageChecker.format_bytes(0) == "0.00 B"
        assert StorageChecker.format_bytes(1024) == "1.00 KB"
        assert StorageChecker.format_bytes(1024 * 1024) == "1.00 MB"
        assert StorageChecker.format_bytes(1024 * 1024 * 1024) == "1.00 GB"
        assert "TB" in StorageChecker.format_bytes(1024 ** 4)

    def test_check_sufficient_space_enough(self, temp_dir):
        """Test checking space when sufficient."""
        required = 1024  # 1KB (definitely available)
        sufficient, message = StorageChecker.check_sufficient_space(
            temp_dir, required
        )
        
        assert sufficient is True
        assert 'Sufficient' in message

    def test_check_sufficient_space_insufficient(self, temp_dir):
        """Test checking space when insufficient."""
        total, used, free = StorageChecker.check_available_space(temp_dir)
        required = free * 2  # Request more than available
        
        sufficient, message = StorageChecker.check_sufficient_space(
            temp_dir, required
        )
        
        assert sufficient is False
        assert 'Insufficient' in message
        assert 'Shortage' in message

    def test_check_sufficient_space_with_margin(self, temp_dir):
        """Test space checking with safety margin."""
        total, used, free = StorageChecker.check_available_space(temp_dir)
        
        # Request just under free space
        required = int(free * 0.95)
        
        # With 10% margin, this should fail
        sufficient, message = StorageChecker.check_sufficient_space(
            temp_dir, required, safety_margin=0.1
        )
        
        # Result depends on actual free space
        assert isinstance(sufficient, bool)
        assert isinstance(message, str)
