"""Authentication service for Google Drive API."""

from pathlib import Path
from typing import Optional
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from rich.console import Console

from gdrive_sync.utils.constants import SCOPES

console = Console()


class AuthenticationService:
    """Manages Google Drive authentication."""

    def __init__(self, credentials_path: Path, token_path: Path):
        """
        Initialize authentication service.
        
        Args:
            credentials_path: Path to credentials.json
            token_path: Path to token.json
        """
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.credentials: Optional[Credentials] = None
        self.service = None

    def authenticate(self):
        """
        Authenticate with Google Drive API.
        Creates and stores service instance.
        
        Raises:
            SystemExit: If credentials file not found
        """
        if self.token_path.exists():
            self.credentials = Credentials.from_authorized_user_file(
                str(self.token_path), SCOPES
            )

        if not self.credentials or not self.credentials.valid:
            if (self.credentials and 
                self.credentials.expired and 
                self.credentials.refresh_token):
                try:
                    self.credentials.refresh(Request())
                except Exception as e:
                    console.print(f"[yellow]Token refresh failed: {e}[/yellow]")
                    self.credentials = None

            if not self.credentials:
                if not self.credentials_path.exists():
                    console.print(
                        "[red]Error: credentials.json not found![/red]\n"
                        "Please download OAuth 2.0 credentials from Google Cloud Console.\n"
                        f"Expected location: {self.credentials_path}"
                    )
                    raise SystemExit(1)

                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.credentials_path), SCOPES
                )
                self.credentials = flow.run_local_server(port=0)

            # Save credentials for future use
            self.token_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.token_path, 'w') as token:
                token.write(self.credentials.to_json())

        # Build service
        self.service = build('drive', 'v3', credentials=self.credentials)
        console.print("[green]✓ Successfully authenticated with Google Drive[/green]")

    def get_service(self):
        """
        Get the Google Drive service instance.
        
        Returns:
            Google Drive API service
            
        Raises:
            ValueError: If not authenticated
        """
        if not self.service:
            raise ValueError("Not authenticated. Call authenticate() first.")
        return self.service

    def is_authenticated(self) -> bool:
        """
        Check if currently authenticated.
        
        Returns:
            True if authenticated
        """
        return self.service is not None
