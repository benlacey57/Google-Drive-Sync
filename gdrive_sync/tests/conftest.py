"""Shared test fixtures and configuration."""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock
from datetime import datetime

from gdrive_sync.domain.models import PerformanceMetrics, SyncState, DriveFileInfo
from gdrive_sync.config.models import (
    DownloadConfig,
    UploadConfig,
    SyncConfig,
    ApplicationConfig
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_credentials():
    """Mock Google credentials."""
    mock_creds = Mock()
    mock_creds.valid = True
    mock_creds.expired = False
    mock_creds.refresh_token = "mock_refresh_token"
    return mock_creds


@pytest.fixture
def mock_drive_service():
    """Mock Google Drive service."""
    service = MagicMock()
    
    # Mock files().list()
    files_list = MagicMock()
    files_list.execute.return_value = {
        'files': [
            {
                'id': 'file1',
                'name': 'test_file.txt',
                'mimeType': 'text/plain',
                'size': '1024',
                'modifiedTime': '2024-01-01T00:00:00Z',
                'parents': ['parent1']
            }
        ],
        'nextPageToken': None
    }
    service.files.return_value.list.return_value = files_list
    
    # Mock files().get()
    files_get = MagicMock()
    files_get.execute.return_value = {
        'id': 'folder1',
        'name': 'test_folder',
        'parents': ['root']
    }
    service.files.return_value.get.return_value = files_get
    
    # Mock files().create()
    files_create = MagicMock()
    files_create.execute.return_value = {'id': 'new_file_id'}
    service.files.return_value.create.return_value = files_create
    
    return service


@pytest.fixture
def sample_download_config(temp_dir):
    """Sample download configuration."""
    return DownloadConfig(
        paths=['/test/path'],
        destination=str(temp_dir / 'downloads'),
        resume=True,
        exclude_patterns=['*.tmp', '*.log'],
        max_file_size_mb=100,
        convert_google_docs=True,
        use_compression=True
    )


@pytest.fixture
def sample_upload_config(temp_dir):
    """Sample upload configuration."""
    return UploadConfig(
        source=str(temp_dir / 'source'),
        destination_path='/test/upload',
        resume=True,
        exclude_patterns=['*.tmp'],
        max_file_size_mb=50,
        use_compression=True
    )


@pytest.fixture
def sample_sync_config(temp_dir):
    """Sample sync configuration."""
    return SyncConfig(
        paths=['/test/sync'],
        destination=str(temp_dir / 'sync'),
        bidirectional=True,
        delete_missing=False,
        delete_missing_remote=False,
        resume=True,
        exclude_patterns=['*.cache'],
        max_file_size_mb=0,
        use_compression=True,
        convert_google_docs=True
    )


@pytest.fixture
def sample_metrics():
    """Sample performance metrics."""
    import time
    return PerformanceMetrics(
        operation='download',
        start_time=time.time(),
        total_files=10,
        successful_files=8,
        failed_files=2,
        excluded_files=1,
        total_bytes_original=1024000,
        total_bytes_transferred=900000,
        compressed_files=3,
        bytes_saved_compression=124000
    )


@pytest.fixture
def sample_drive_file():
    """Sample drive file metadata."""
    return {
        'id': 'file123',
        'name': 'test_document.txt',
        'mimeType': 'text/plain',
        'size': '2048',
        'modifiedTime': '2024-01-15T10:30:00Z',
        'parents': ['parent123'],
        'md5Checksum': 'abc123def456'
    }


@pytest.fixture
def sample_config_file(temp_dir):
    """Create a sample configuration file."""
    config_dir = temp_dir / 'config'
    config_dir.mkdir()
    
    config_data = {
        'paths': ['/test/path'],
        'destination': str(temp_dir / 'dest'),
        'resume': True,
        'exclude_patterns': ['*.tmp'],
        'max_file_size_mb': 0,
        'convert_google_docs': True,
        'use_compression': True
    }
    
    config_file = config_dir / 'download.json'
    with open(config_file, 'w') as f:
        json.dump(config_data, f)
    
    return config_file


@pytest.fixture
def sample_exclusions_file(temp_dir):
    """Create a sample exclusions file."""
    exclusions_file = temp_dir / 'exclusions.conf'
    with open(exclusions_file, 'w') as f:
        f.write("# Test exclusions\n")
        f.write("*.tmp\n")
        f.write("*.log\n")
        f.write(".DS_Store\n")
    return exclusions_file


@pytest.fixture
def mock_progress():
    """Mock Rich progress bar."""
    progress = MagicMock()
    progress.add_task.return_value = 1
    progress.update.return_value = None
    progress.remove_task.return_value = None
    return progress


@pytest.fixture
def sample_test_files(temp_dir):
    """Create sample test files."""
    files_dir = temp_dir / 'files'
    files_dir.mkdir()
    
    # Create various test files
    (files_dir / 'document.txt').write_text('Test content')
    (files_dir / 'large_file.txt').write_text('x' * 2000000)  # 2MB
    (files_dir / 'temp.tmp').write_text('Temporary')
    
    # Create subdirectory
    subdir = files_dir / 'subdir'
    subdir.mkdir()
    (subdir / 'nested.txt').write_text('Nested content')
    
    return files_dir
