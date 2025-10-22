"""Tests for domain models."""

import pytest
import time
import json
from pathlib import Path

from gdrive_sync.domain.models import (
    PerformanceMetrics,
    SyncState,
    DriveFileInfo
)


class TestPerformanceMetrics:
    """Tests for PerformanceMetrics model."""

    def test_initialization(self):
        """Test metrics initialization."""
        start = time.time()
        metrics = PerformanceMetrics(
            operation='download',
            start_time=start
        )
        
        assert metrics.operation == 'download'
        assert metrics.start_time == start
        assert metrics.total_files == 0
        assert metrics.successful_files == 0
        assert metrics.errors == []

    def test_duration_calculation(self):
        """Test duration calculation."""
        start = time.time()
        metrics = PerformanceMetrics(
            operation='upload',
            start_time=start
        )
        
        time.sleep(0.1)
        metrics.finish()
        
        duration = metrics.duration()
        assert duration >= 0.1
        assert duration < 1.0

    def test_average_speed(self):
        """Test average speed calculation."""
        start = time.time()
        metrics = PerformanceMetrics(
            operation='download',
            start_time=start,
            total_bytes_transferred=1024000
        )
        
        time.sleep(0.1)
        metrics.finish()
        
        speed = metrics.average_speed()
        assert speed > 0
        assert speed < 1024000 / 0.1 * 2  # Reasonable upper bound

    def test_compression_ratio(self):
        """Test compression ratio calculation."""
        metrics = PerformanceMetrics(
            operation='download',
            start_time=time.time(),
            total_bytes_original=1000000,
            total_bytes_transferred=700000
        )
        
        ratio = metrics.compression_ratio()
        assert ratio == 30.0

    def test_compression_ratio_no_data(self):
        """Test compression ratio with no data."""
        metrics = PerformanceMetrics(
            operation='download',
            start_time=time.time()
        )
        
        ratio = metrics.compression_ratio()
        assert ratio == 0.0

    def test_to_dict(self, sample_metrics):
        """Test conversion to dictionary."""
        sample_metrics.finish()
        data = sample_metrics.to_dict()
        
        assert isinstance(data, dict)
        assert data['operation'] == 'download'
        assert data['total_files'] == 10
        assert data['successful_files'] == 8
        assert 'start_time' in data
        assert 'end_time' in data


class TestSyncState:
    """Tests for SyncState model."""

    def test_initialization(self):
        """Test state initialization."""
        state = SyncState(
            operation='download',
            paths=['/test/path'],
            local_path='/local/path',
            last_sync='2024-01-01T00:00:00',
            completed_files=['file1', 'file2'],
            total_files=10,
            total_size=1024000
        )
        
        assert state.operation == 'download'
        assert len(state.completed_files) == 2
        assert state.total_files == 10

    def test_save_and_load(self, temp_dir):
        """Test saving and loading state."""
        state_file = temp_dir / 'state.json'
        
        state = SyncState(
            operation='upload',
            paths=['/path1', '/path2'],
            local_path=str(temp_dir),
            last_sync='2024-01-01T00:00:00',
            completed_files=['file1'],
            total_files=5,
            total_size=5000
        )
        
        # Save state
        state.save(state_file)
        assert state_file.exists()
        
        # Load state
        loaded_state = SyncState.load(state_file)
        assert loaded_state is not None
        assert loaded_state.operation == 'upload'
        assert loaded_state.paths == ['/path1', '/path2']
        assert loaded_state.completed_files == ['file1']

    def test_load_nonexistent_file(self, temp_dir):
        """Test loading non-existent state file."""
        state_file = temp_dir / 'nonexistent.json'
        state = SyncState.load(state_file)
        assert state is None

    def test_load_invalid_json(self, temp_dir):
        """Test loading invalid JSON."""
        state_file = temp_dir / 'invalid.json'
        state_file.write_text('invalid json {')
        
        state = SyncState.load(state_file)
        assert state is None


class TestDriveFileInfo:
    """Tests for DriveFileInfo model."""

    def test_initialization(self):
        """Test file info initialization."""
        file_info = DriveFileInfo(
            id='file123',
            name='test.txt',
            mime_type='text/plain',
            size=1024,
            modified_time='2024-01-01T00:00:00Z',
            path='/test',
            parents=['parent1'],
            md5_checksum='abc123'
        )
        
        assert file_info.id == 'file123'
        assert file_info.name == 'test.txt'
        assert file_info.size == 1024

    def test_from_api_response(self, sample_drive_file):
        """Test creation from API response."""
        file_info = DriveFileInfo.from_api_response(
            sample_drive_file,
            '/test/path'
        )
        
        assert file_info.id == 'file123'
        assert file_info.name == 'test_document.txt'
        assert file_info.mime_type == 'text/plain'
        assert file_info.size == 2048
        assert file_info.path == '/test/path'
