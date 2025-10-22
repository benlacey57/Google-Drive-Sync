"""Tests for compression handler."""

import pytest
from pathlib import Path

from gdrive_sync.infrastructure.storage.compression import CompressionHandler


class TestCompressionHandler:
    """Tests for CompressionHandler."""

    def test_should_compress_small_file(self, temp_dir):
        """Test that small files are not compressed."""
        small_file = temp_dir / 'small.txt'
        small_file.write_text('x' * 100)  # 100 bytes
        
        assert not CompressionHandler.should_compress(small_file)

    def test_should_compress_large_text_file(self, temp_dir):
        """Test that large text files are compressed."""
        large_file = temp_dir / 'large.txt'
        large_file.write_text('x' * 2000000)  # 2MB
        
        assert CompressionHandler.should_compress(large_file)

    def test_should_not_compress_already_compressed(self, temp_dir):
        """Test that already compressed files are skipped."""
        gz_file = temp_dir / 'file.gz'
        gz_file.write_text('x' * 2000000)
        
        assert not CompressionHandler.should_compress(gz_file)

    def test_should_compress_by_extension(self, temp_dir):
        """Test compression based on file extension."""
        # Compressible extensions
        json_file = temp_dir / 'data.json'
        json_file.write_text('x' * 2000000)
        assert CompressionHandler.should_compress(json_file)
        
        csv_file = temp_dir / 'data.csv'
        csv_file.write_text('x' * 2000000)
        assert CompressionHandler.should_compress(csv_file)
        
        # Non-compressible
        zip_file = temp_dir / 'archive.zip'
        zip_file.write_text('x' * 2000000)
        assert not CompressionHandler.should_compress(zip_file)

    def test_compress_and_decompress_file(self, temp_dir):
        """Test compressing and decompressing a file."""
        # Create source file
        source = temp_dir / 'source.txt'
        content = 'Test content ' * 100
        source.write_text(content)
        
        # Compress
        compressed = temp_dir / 'compressed.gz'
        success, orig_size, comp_size = CompressionHandler.compress_file(
            source, compressed
        )
        
        assert success is True
        assert orig_size > 0
        assert comp_size > 0
        assert comp_size < orig_size  # Compressed should be smaller
        assert compressed.exists()
        
        # Decompress
        decompressed = temp_dir / 'decompressed.txt'
        success, decomp_size = CompressionHandler.decompress_file(
            compressed, decompressed
        )
        
        assert success is True
        assert decomp_size == orig_size
        assert decompressed.read_text() == content

    def test_compress_nonexistent_file(self, temp_dir):
        """Test compressing non-existent file."""
        source = temp_dir / 'nonexistent.txt'
        dest = temp_dir / 'compressed.gz'
        
        success, orig_size, comp_size = CompressionHandler.compress_file(
            source, dest
        )
        
        assert success is False
        assert orig_size == 0
        assert comp_size == 0

    def test_decompress_invalid_file(self, temp_dir):
        """Test decompressing invalid gzip file."""
        invalid = temp_dir / 'invalid.gz'
        invalid.write_text('not a gzip file')
        
        dest = temp_dir / 'output.txt'
        success, size = CompressionHandler.decompress_file(invalid, dest)
        
        assert success is False
        assert size == 0
