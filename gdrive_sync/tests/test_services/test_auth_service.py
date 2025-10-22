"""Tests for authentication service."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from gdrive_sync.services.auth_service import AuthenticationService


class TestAuthenticationService:
    """Tests for AuthenticationService."""

    @pytest.fixture
    def auth_service(self, temp_dir):
        """Create auth service with temp paths."""
        creds_path = temp_dir / 'credentials.json'
        token_path = temp_dir / 'token.json'
        return AuthenticationService(creds_path, token_path)

    def test_initialization(self, auth_service, temp_dir):
        """Test service initialization."""
        assert auth_service.credentials_path == temp_dir / 'credentials.json'
        assert auth_service.token_path == temp_dir / 'token.json'
        assert auth_service.credentials is None
        assert auth_service.service is None

    @patch('gdrive_sync.services.auth_service.Credentials')
    @patch('gdrive_sync.services.auth_service.build')
    def test_authenticate_with_valid_token(
        self,
        mock_build,
        mock_creds_class,
        auth_service,
        mock_credentials,
        temp_dir
    ):
        """Test authentication with valid token."""
        # Create token file
        token_file = temp_dir / 'token.json'
        token_file.write_text('{"token": "mock"}')
        
        # Mock credentials
        mock_creds_class.from_authorized_user_file.return_value = mock_credentials
        mock_build.return_value = Mock()
        
        auth_service.authenticate()
        
        assert auth_service.credentials is not None
        assert auth_service.service is not None
        mock_creds_class.from_authorized_user_file.assert_called_once()

    @patch('gdrive_sync.services.auth_service.InstalledAppFlow')
    @patch('gdrive_sync.services.auth_service.build')
    def test_authenticate_new_user(
        self,
        mock_build,
        mock_flow_class,
        auth_service,
        mock_credentials,
        temp_dir
    ):
        """Test authentication for new user."""
        # Create credentials file
        creds_file = temp_dir / 'credentials.json'
        creds_file.write_text('{"installed": {}}')
        
        # Mock flow
        mock_flow = Mock()
        mock_flow.run_local_server.return_value = mock_credentials
        mock_flow_class.from_client_secrets_file.return_value = mock_flow
        mock_build.return_value = Mock()
        
        auth_service.authenticate()
        
        assert auth_service.credentials is not None
        mock_flow.run_local_server.assert_called_once()

    def test_authenticate_missing_credentials(self, auth_service):
        """Test authentication with missing credentials file."""
        with pytest.raises(SystemExit):
            auth_service.authenticate()

    def test_get_service_not_authenticated(self, auth_service):
        """Test getting service when not authenticated."""
        with pytest.raises(ValueError, match='Not authenticated'):
            auth_service.get_service()

    @patch('gdrive_sync.services.auth_service.build')
    def test_get_service_authenticated(
        self,
        mock_build,
        auth_service,
        mock_credentials
    ):
        """Test getting service when authenticated."""
        mock_service = Mock()
        mock_build.return_value = mock_service
        
        auth_service.credentials = mock_credentials
        auth_service.service = mock_service
        
        service = auth_service.get_service()
        assert service == mock_service

    def test_is_authenticated(self, auth_service):
        """Test checking authentication status."""
        assert auth_service.is_authenticated() is False
        
        auth_service.service = Mock()
        assert auth_service.is_authenticated() is True
