"""Tests for exclusion service."""

import pytest
from pathlib import Path

from gdrive_sync.services.exclusion_service import ExclusionService


class TestExclusionService:
    """Tests for ExclusionService."""

    def test_initialization_with_defaults(self):
        """Test initialization with default exclusions."""
        service = ExclusionService()
        
        exclusions = service.get_exclusions_list()
        assert len(exclusions) > 0
        assert '.DS_Store' in exclusions
        assert '*.pyc' in exclusions

    def test_initialization_with_config_file(self, sample_exclusions_file):
        """Test initialization with config file."""
        service = ExclusionService(sample_exclusions_file)
        
        exclusions = service.get_exclusions_list()
        assert '*.tmp' in exclusions
        assert '*.log' in exclusions

    def test_add_exclusion(self):
        """Test adding exclusion pattern."""
        service = ExclusionService()
        initial_count = len(service.exclusions)
        
        service.add_exclusion('*.custom')
        assert len(service.exclusions) == initial_count + 1
        assert '*.custom' in service.exclusions

    def test_remove_exclusion(self):
        """Test removing exclusion pattern."""
        service = ExclusionService()
        service.add_exclusion('*.custom')
        
        service.remove_exclusion('*.custom')
        assert '*.custom' not in service.exclusions

    def test_add_multiple_exclusions(self):
        """Test adding multiple exclusions."""
        service = ExclusionService()
        patterns = ['*.tmp', '*.log', '*.bak']
        
        service.add_exclusions(patterns)
        for pattern in patterns:
            assert pattern in service.exclusions

    def test_should_exclude_filename(self):
        """Test exclusion by filename."""
        service = ExclusionService()
        service.add_exclusion('*.tmp')
        
        assert service.should_exclude(Path('file.tmp')) is True
        assert service.should_exclude(Path('file.txt')) is False

    def test_should_exclude_exact_name(self):
        """Test exclusion by exact name."""
        service = ExclusionService()
        service.add_exclusion('.DS_Store')
        
        assert service.should_exclude(Path('.DS_Store')) is True
        assert service.should_exclude(Path('other.txt')) is False

    def test_should_exclude_with_base_path(self, temp_dir):
        """Test exclusion with base path."""
        service = ExclusionService()
        service.add_exclusion('node_modules')
        
        file_path = temp_dir / 'project' / 'node_modules' / 'package'
        base_path = temp_dir / 'project'
        
        assert service.should_exclude(file_path, base_path) is True

    def test_should_exclude_relative_path(self, temp_dir):
        """Test exclusion by relative path."""
        service = ExclusionService()
        service.add_exclusion('temp/*')
        
        file_path = temp_dir / 'temp' / 'file.txt'
        
        assert service.should_exclude(file_path, temp_dir) is True

    def test_wildcard_matching(self):
        """Test wildcard pattern matching."""
        service = ExclusionService()
        service.add_exclusion('test_*.py')
        
        assert service.should_exclude(Path('test_file.py')) is True
        assert service.should_exclude(Path('test_something.py')) is True
        assert service.should_exclude(Path('other.py')) is False

    def test_question_mark_wildcard(self):
        """Test single character wildcard."""
        service = ExclusionService()
        service.add_exclusion('file?.txt')
        
        assert service.should_exclude(Path('file1.txt')) is True
        assert service.should_exclude(Path('file2.txt')) is True
        assert service.should_exclude(Path('file10.txt')) is False

    def test_save_exclusions(self, temp_dir):
        """Test saving exclusions to file."""
        config_file = temp_dir / 'exclusions.conf'
        service = ExclusionService(config_file)
        
        service.add_exclusion('*.custom')
        service.save_exclusions()
        
        assert config_file.exists()
        content = config_file.read_text()
        assert '*.custom' in content

    def test_reset_to_defaults(self):
        """Test resetting to default exclusions."""
        service = ExclusionService()
        service.add_exclusion('*.custom')
        
        service.reset_to_defaults()
        assert '*.custom' not in service.exclusions
        assert '.DS_Store' in service.exclusions

    def test_get_exclusions_list_sorted(self):
        """Test that exclusions list is sorted."""
        service = ExclusionService()
        service.add_exclusion('zzz')
        service.add_exclusion('aaa')
        
        exclusions = service.get_exclusions_list()
        assert exclusions == sorted(exclusions)
