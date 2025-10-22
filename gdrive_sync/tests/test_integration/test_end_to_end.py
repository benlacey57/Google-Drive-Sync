"""Integration tests for end-to-end workflows."""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from gdrive_sync.config.models import DownloadConfig, UploadConfig
from gdrive_sync.services.sync_service import SyncService
from gdrive_sync.services.exclusion_service import ExclusionService
from gdrive_sync.infrastructure.drive.file_handler import DriveFileHandler
from gdrive_sync.infrastructure.drive.path_resolver import PathResolver
from gdrive_sync.infrastructure.logging.metrics_logger import MetricsLogger


class TestEndToEnd:
    """End-to-end integration tests."""

    @pytest.fixture
    def setup_services(self, temp_dir, mock_drive_service):
        """Set up all required services."""
        file_handler = DriveFileHandler(mock_drive_service)
        path_resolver = PathResolver(mock_drive_service)
        exclusion_service = ExclusionService()
        metrics_logger = MetricsLogger(temp_dir / 'data')
        
        sync_service = SyncService(
            file_handler,
            path_resolver,
            exclusion_service,
            metrics_logger,
            use_compression=False  # Disable for simpler testing
        )
        
        return {
            'sync_service': sync_service,
            'file_handler': file_handler,
            'path_resolver': path_resolver,
            'exclusion_service': exclusion_service,
            'metrics_logger': metrics_logger
        }

    @patch('gdrive_sync.services.sync_service.StorageChecker')
    def test_download_workflow(
        self,
        mock_storage_checker,
        setup_services,
        temp_dir
    ):
        """Test complete download workflow."""
        services = setup_services
        
        # Mock storage check
        mock_storage_checker.check_sufficient_space.return_value = (
            True,
            "Sufficient space"
        )
        
        # Mock file list
        with patch.object(
            services['file_handler'],
            'list_files_in_folder',
            return_value=[
                {
                    'id': 'file1',
                    'name': 'test.txt',
                    'mimeType': 'text/plain',
                    'size': '1024',
                    'modifiedTime': '2024-01-01T00:00:00Z'
                }
            ]
        ):
            # Mock path resolution
            with patch.object(
                services['path_resolver'],
                'resolve_path',
                return_value='folder_id'
            ):
                # Mock download
                with patch.object(
                    services['file_handler'],
                    'download_file',
                    return_value=True
                ):
                    # Create test file that download would create
                    dest = temp_dir / 'downloads'
                    dest.mkdir()
                    (dest / 'test.txt').write_text('content')
                    
                    config = DownloadConfig(
                        paths=['/test'],
                        destination=str(dest),
                        use_compression=False
                    )
                    
                    metrics = services['sync_service'].download(config)
        
        assert metrics.total_files >= 0
        assert metrics.operation == 'download'

    def test_upload_workflow(
        self,
        setup_services,
        sample_test_files,
        temp_dir
    ):
        """Test complete upload workflow."""
        services = setup_services
        
        # Mock path resolution and folder creation
        with patch.object(
            services['path_resolver'],
            'resolve_path',
            return_value='folder_id'
        ):
            with patch.object(
                services['file_handler'],
                'upload_file',
                return_value='uploaded_file_id'
            ):
                with patch.object(
                    services['file_handler'],
                    'create_folder',
                    return_value='new_folder_id'
                ):
                    config = UploadConfig(
                        source=str(sample_test_files),
                        destination_path='/test/upload',
                        use_compression=False
                    )
                    
                    metrics = services['sync_service'].upload(config)
        
        assert metrics.operation == 'upload'
        assert metrics.total_files > 0

    def test_exclusion_filtering(
        self,
        setup_services,
        sample_test_files
    ):
        """Test that exclusion patterns are applied."""
        services = setup_services
        
        # Add exclusion
        services['exclusion_service'].add_exclusion('*.tmp')
        
        # Check files are excluded
        for file_path in sample_test_files.rglob('*'):
            if file_path.is_file():
                is_excluded = services['exclusion_service'].should_exclude(
                    file_path,
                    sample_test_files
                )
                
                if file_path.suffix == '.tmp':
                    assert is_excluded is True
                elif file_path.suffix == '.txt':
                    assert is_excluded is False

    def test_metrics_persistence(
        self,
        setup_services,
        sample_metrics,
        temp_dir
    ):
        """Test that metrics are saved correctly."""
        services = setup_services
        
        # Save metrics
        sample_metrics.finish()
        services['metrics_logger'].save_metrics(sample_metrics)
        
        # Check metrics file was created
        metrics_files = list(
            (temp_dir / 'data' / 'metrics').glob('metrics_*.json')
        )
        assert len(metrics_files) > 0
        
        # Load and verify
        with open(metrics_files[0], 'r') as f:
            data = json.load(f)
        
        assert data['operation'] == 'download'
        assert data['total_files'] == 10

    def test_configuration_roundtrip(
        self,
        temp_dir
    ):
        """Test saving and loading configuration."""
        from gdrive_sync.config.loader import ConfigLoader
        
        config_dir = temp_dir / 'config'
        config_dir.mkdir()
        
        loader = ConfigLoader(config_dir)
        
        # Create and save config
        original = DownloadConfig(
            paths=['/photos', '/documents'],
            destination=str(temp_dir / 'dest'),
            max_file_size_mb=50
        )
        
        loader.save_download_config(original, 'test')
        
        # Load config
        loaded = loader.load_download_config('test')
        
        assert loaded is not None
        assert loaded.paths == original.paths
        assert loaded.destination == original.destination
        assert loaded.max_file_size_mb == original.max_file_size_mb
