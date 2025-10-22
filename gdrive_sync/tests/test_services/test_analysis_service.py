"""Tests for analysis service."""

import pytest
from unittest.mock import Mock, MagicMock, patch

from gdrive_sync.services.analysis_service import AnalysisService
from gdrive_sync.domain.enums import FileCategory


class TestAnalysisService:
    """Tests for AnalysisService."""

    @pytest.fixture
    def analysis_service(self, mock_drive_service):
        """Create analysis service with mocks."""
        from gdrive_sync.infrastructure.drive.path_resolver import PathResolver
        path_resolver = PathResolver(mock_drive_service)
        return AnalysisService(mock_drive_service, path_resolver)

    def test_categorise_file_type_images(self, analysis_service):
        """Test categorizing image files."""
        category = analysis_service._categorise_file_type('image/png', '.png')
        assert category == FileCategory.IMAGES
        
        category = analysis_service._categorise_file_type('image/jpeg', '.jpg')
        assert category == FileCategory.IMAGES

    def test_categorise_file_type_videos(self, analysis_service):
        """Test categorizing video files."""
        category = analysis_service._categorise_file_type('video/mp4', '.mp4')
        assert category == FileCategory.VIDEOS

    def test_categorise_file_type_documents(self, analysis_service):
        """Test categorizing document files."""
        category = analysis_service._categorise_file_type(
            'application/msword',
            '.doc'
        )
        assert category == FileCategory.DOCUMENTS
        
        category = analysis_service._categorise_file_type('', '.docx')
        assert category == FileCategory.DOCUMENTS

    def test_categorise_file_type_spreadsheets(self, analysis_service):
        """Test categorizing spreadsheet files."""
        category = analysis_service._categorise_file_type('', '.xlsx')
        assert category == FileCategory.SPREADSHEETS
        
        category = analysis_service._categorise_file_type('', '.csv')
        assert category == FileCategory.SPREADSHEETS

    def test_categorise_file_type_google_docs(self, analysis_service):
        """Test categorizing Google Docs."""
        category = analysis_service._categorise_file_type(
            'application/vnd.google-apps.document',
            ''
        )
        assert category == FileCategory.GOOGLE_DOCS

    def test_categorise_file_type_archives(self, analysis_service):
        """Test categorizing archive files."""
        category = analysis_service._categorise_file_type('', '.zip')
        assert category == FileCategory.ARCHIVES
        
        category = analysis_service._categorise_file_type('', '.tar')
        assert category == FileCategory.ARCHIVES

    def test_categorise_file_type_other(self, analysis_service):
        """Test categorizing unknown file types."""
        category = analysis_service._categorise_file_type('', '.xyz')
        assert category == FileCategory.OTHER

    @patch.object(AnalysisService, '_get_all_files_recursive')
    def test_analyse_drive_basic(
        self,
        mock_get_files,
        analysis_service
    ):
        """Test basic drive analysis."""
        # Mock file list
        mock_get_files.return_value = [
            {
                'file': {
                    'id': '1',
                    'name': 'document.txt',
                    'mimeType': 'text/plain',
                    'size': '1024'
                },
                'folder_path': '/test'
            },
            {
                'file': {
                    'id': '2',
                    'name': 'image.jpg',
                    'mimeType': 'image/jpeg',
                    'size': '2048'
                },
                'folder_path': '/test'
            }
        ]
        
        with patch.object(
            analysis_service.path_resolver,
            'resolve_path',
            return_value='folder_id'
        ):
            stats = analysis_service.analyse_drive('/test')
        
        assert stats['total_files'] == 2
        assert stats['total_size'] == 3072
        assert '.txt' in stats['by_extension']
        assert '.jpg' in stats['by_extension']

    @patch.object(AnalysisService, '_get_all_files_recursive')
    def test_analyse_drive_google_docs(
        self,
        mock_get_files,
        analysis_service
    ):
        """Test analysis with Google Docs."""
        mock_get_files.return_value = [
            {
                'file': {
                    'id': '1',
                    'name': 'doc',
                    'mimeType': 'application/vnd.google-apps.document',
                    'size': '0'
                },
                'folder_path': '/test'
            }
        ]
        
        with patch.object(
            analysis_service.path_resolver,
            'resolve_path',
            return_value='folder_id'
        ):
            stats = analysis_service.analyse_drive('/test')
        
        assert stats['google_docs']['count'] == 1
        assert 'document' in stats['google_docs']['types']

    def test_export_analysis(self, analysis_service, temp_dir):
        """Test exporting analysis to JSON."""
        stats = {
            'path': '/test',
            'total_files': 5,
            'total_size': 10000,
            'by_extension': {'.txt': {'count': 3, 'size': 5000}},
            'by_folder': {'/test': {'count': 5, 'size': 10000}},
            'google_docs': {'count': 0, 'types': {}},
            'largest_files': [],
            'file_type_distribution': {'Text': 3}
        }
        
        output_file = temp_dir / 'analysis.json'
        analysis_service.export_analysis(stats, output_file)
        
        assert output_file.exists()
        
        import json
        with open(output_file, 'r') as f:
            exported = json.load(f)
        
        assert exported['path'] == '/test'
        assert exported['total_files'] == 5
        assert 'generated_at' in exported
