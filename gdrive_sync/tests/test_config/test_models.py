"""Tests for configuration models."""

import pytest
from pathlib import Path

from gdrive_sync.config.models import (
    DownloadConfig,
    UploadConfig,
    SyncConfig,
    ApplicationConfig,
    OperationConfig
)


class TestOperationConfig:
    """Tests for OperationConfig base class."""

    def test_get_max_file_size_bytes(self):
        """Test max file size conversion."""
        config = OperationConfig(max_file_size_mb=100)
        assert config.get_max_file_size_bytes() == 100 * 1024 * 1024

    def test_get_max_file_size_bytes_zero(self):
        """Test max file size with zero (no limit)."""
        config = OperationConfig(max_file_size_mb=0)
        assert config.get_max_file_size_bytes() is None


class TestDownloadConfig:
    """Tests for DownloadConfig."""

    def test_initialization(self):
        """Test download config initialization."""
        config = DownloadConfig(
            paths=['/path1', '/path2'],
            destination='/local/path',
            convert_google_docs=True
        )
        
        assert len(config.paths) == 2
        assert config.destination == '/local/path'
        assert config.convert_google_docs is True
        assert config.resume is True

    def test_validate_valid_config(self):
        """Test validation of valid configuration."""
        config = DownloadConfig(
            paths=['/test'],
            destination='/dest'
        )
        
        valid, message = config.validate()
        assert valid is True
        assert message == ""

    def test_validate_missing_paths(self):
        """Test validation with missing paths."""
        config = DownloadConfig(
            paths=[],
            destination='/dest'
        )
        
        valid, message = config.validate()
        assert valid is False
        assert 'paths' in message.lower()

    def test_validate_missing_destination(self):
        """Test validation with missing destination."""
        config = DownloadConfig(
            paths=['/test'],
            destination=''
        )
        
        valid, message = config.validate()
        assert valid is False
        assert 'destination' in message.lower()

    def test_save_and_load(self, temp_dir):
        """Test saving and loading configuration."""
        config_file = temp_dir / 'download.json'
        
        config = DownloadConfig(
            paths=['/photos'],
            destination='/local/photos',
            exclude_patterns=['*.tmp'],
            max_file_size_mb=50
        )
        
        # Save
        config.save(config_file)
        assert config_file.exists()
        
        # Load
        loaded = DownloadConfig.from_file(config_file)
        assert loaded.paths == ['/photos']
        assert loaded.destination == '/local/photos'
        assert loaded.max_file_size_mb == 50


class TestUploadConfig:
    """Tests for UploadConfig."""

    def test_initialization(self):
        """Test upload config initialization."""
        config = UploadConfig(
            source='/local/path',
            destination_path='/drive/path'
        )
        
        assert config.source == '/local/path'
        assert config.destination_path == '/drive/path'

    def test_validate_valid_config(self, temp_dir):
        """Test validation of valid configuration."""
        source_dir = temp_dir / 'source'
        source_dir.mkdir()
        
        config = UploadConfig(
            source=str(source_dir),
            destination_path='/drive'
        )
        
        valid, message = config.validate()
        assert valid is True

    def test_validate_missing_source(self):
        """Test validation with missing source."""
        config = UploadConfig(
            source='',
            destination_path='/drive'
        )
        
        valid, message = config.validate()
        assert valid is False
        assert 'source' in message.lower()

    def test_validate_nonexistent_source(self):
        """Test validation with non-existent source."""
        config = UploadConfig(
            source='/nonexistent/path',
            destination_path='/drive'
        )
        
        valid, message = config.validate()
        assert valid is False
        assert 'not exist' in message.lower()


class TestSyncConfig:
    """Tests for SyncConfig."""

    def test_initialization(self):
        """Test sync config initialization."""
        config = SyncConfig(
            paths=['/sync/path'],
            destination='/local/sync',
            bidirectional=True,
            delete_missing=False
        )
        
        assert config.bidirectional is True
        assert config.delete_missing is False
        assert config.delete_missing_remote is False

    def test_validate_valid_config(self):
        """Test validation of valid configuration."""
        config = SyncConfig(
            paths=['/sync'],
            destination='/local'
        )
        
        valid, message = config.validate()
        assert valid is True

    def test_save_and_load(self, temp_dir):
        """Test saving and loading sync configuration."""
        config_file = temp_dir / 'sync.json'
        
        config = SyncConfig(
            paths=['/work'],
            destination='/local/work',
            bidirectional=True,
            delete_missing=True,
            max_file_size_mb=200
        )
        
        config.save(config_file)
        loaded = SyncConfig.from_file(config_file)
        
        assert loaded.paths == ['/work']
        assert loaded.bidirectional is True
        assert loaded.delete_missing is True


class TestApplicationConfig:
    """Tests for ApplicationConfig."""

    def test_initialization(self):
        """Test app config initialization."""
        config = ApplicationConfig()
        
        assert config.credentials_path == 'credentials.json'
        assert config.token_path == 'token.json'
        assert '.gdrive_sync' in config.data_dir

    def test_custom_paths(self):
        """Test custom paths."""
        config = ApplicationConfig(
            credentials_path='/custom/creds.json',
            token_path='/custom/token.json',
            data_dir='/custom/data'
        )
        
        assert config.credentials_path == '/custom/creds.json'
        assert config.data_dir == '/custom/data'

    def test_save_and_load(self, temp_dir):
        """Test saving and loading app configuration."""
        config_file = temp_dir / 'app.json'
        
        config = ApplicationConfig(
            data_dir=str(temp_dir / 'data')
        )
        
        config.save(config_file)
        loaded = ApplicationConfig.from_file(config_file)
        
        assert loaded.data_dir == str(temp_dir / 'data')

    def test_load_nonexistent_returns_default(self, temp_dir):
        """Test loading non-existent file returns defaults."""
        config_file = temp_dir / 'nonexistent.json'
        config = ApplicationConfig.from_file(config_file)
        
        assert isinstance(config, ApplicationConfig)
        assert config.credentials_path == 'credentials.json'
