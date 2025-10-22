"""Tests for Drive path resolver."""

import pytest
from unittest.mock import Mock, MagicMock, patch

from gdrive_sync.infrastructure.drive.path_resolver import PathResolver


class TestPathResolver:
    """Tests for PathResolver."""

    @pytest.fixture
    def path_resolver(self, mock_drive_service):
        """Create path resolver with mock service."""
        return PathResolver(mock_drive_service)

    def test_resolve_root_path(self, path_resolver):
        """Test resolving root path."""
        folder_id = path_resolver.resolve_path('/')
        assert folder_id == 'root'
        
        folder_id = path_resolver.resolve_path('')
        assert folder_id == 'root'

    def test_resolve_path_cached(self, path_resolver):
        """Test path resolution uses cache."""
        # Mock the find method
        with patch.object(path_resolver, '_find_folder', return_value='folder123'):
            # First call
            folder_id1 = path_resolver.resolve_path('/test/path')
            
            # Second call should use cache
            folder_id2 = path_resolver.resolve_path('/test/path')
            
            assert folder_id1 == folder_id2
            # _find_folder should only be called twice (once for 'test', once for 'path')
            assert path_resolver._find_folder.call_count == 2

    def test_resolve_path_not_found(self, path_resolver):
        """Test resolving non-existent path."""
        with patch.object(path_resolver, '_find_folder', return_value=None):
            folder_id = path_resolver.resolve_path('/nonexistent')
            assert folder_id is None

    def test_resolve_path_create_missing(self, path_resolver):
        """Test creating missing folders."""
        with patch.object(path_resolver, '_find_folder', return_value=None):
            with patch.object(path_resolver, '_create_folder', return_value='new_folder_id'):
                folder_id = path_resolver.resolve_path(
                    '/new/path',
                    create_if_missing=True
                )
                assert folder_id == 'new_folder_id'

    def test_normalize_path(self, path_resolver):
        """Test path normalization."""
        with patch.object(path_resolver, '_find_folder', return_value='folder123'):
            # All these should resolve the same way
            id1 = path_resolver.resolve_path('/test/')
            path_resolver.clear_cache()
            id2 = path_resolver.resolve_path('test')
            path_resolver.clear_cache()
            id3 = path_resolver.resolve_path('/test')
            
            assert id1 == id2 == id3

    def test_get_path_from_id_root(self, path_resolver):
        """Test getting path from root ID."""
        path = path_resolver.get_path_from_id('root')
        assert path == '/'

    def test_get_path_from_id(self, path_resolver):
        """Test getting path from folder ID."""
        # Mock the API response
        path_resolver.service.files().get().execute.side_effect = [
            {
                'name': 'folder2',
                'parents': ['parent1']
            },
            {
                'name': 'folder1',
                'parents': ['root']
            }
        ]
        
        path = path_resolver.get_path_from_id('folder2_id')
        assert path == '/folder1/folder2'

    def test_list_folders(self, path_resolver):
        """Test listing folders in a path."""
        # Mock the service response
        path_resolver.service.files().list().execute.return_value = {
            'files': [
                {'id': '1', 'name': 'folder1'},
                {'id': '2', 'name': 'folder2'}
            ]
        }
        
        with patch.object(path_resolver, 'resolve_path', return_value='parent_id'):
            folders = path_resolver.list_folders('/test')
            
            assert len(folders) == 2
            assert folders[0] == ('folder1', '/test/folder1')
            assert folders[1] == ('folder2', '/test/folder2')

    def test_clear_cache(self, path_resolver):
        """Test clearing the cache."""
        path_resolver._cache = {'/test': 'folder123'}
        assert len(path_resolver._cache) > 0
        
        path_resolver.clear_cache()
        assert len(path_resolver._cache) == 0
