"""Google Drive file operations handler."""

from pathlib import Path
from typing import Dict, Any, List, Optional
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from rich.console import Console
from rich.progress import Progress

from gdrive_sync.utils.constants import EXPORT_FORMATS

console = Console()


class DriveFileHandler:
    """Handles Google Drive file operations."""

    def __init__(self, service, convert_google_docs: bool = True):
        """
        Initialize file handler.
        
        Args:
            service: Google Drive API service
            convert_google_docs: Whether to convert Google Docs to ODF
        """
        self.service = service
        self.convert_google_docs = convert_google_docs

    def list_files_in_folder(
        self,
        folder_id: str,
        recursive: bool = True
    ) -> List[Dict[str, Any]]:
        """
        List all files in a folder, optionally recursive.
        
        Args:
            folder_id: ID of the folder to list
            recursive: Whether to recurse into subfolders
            
        Returns:
            List of file metadata dictionaries
        """
        all_files = []
        page_token = None

        query = f"'{folder_id}' in parents and trashed=false"

        try:
            while True:
                results = self.service.files().list(
                    q=query,
                    spaces='drive',
                    fields='nextPageToken, files(id, name, mimeType, size, modifiedTime, md5Checksum, parents)',
                    pageToken=page_token,
                    pageSize=1000
                ).execute()

                files = results.get('files', [])
                all_files.extend(files)

                page_token = results.get('nextPageToken')
                if not page_token:
                    break

            # Recursively get files from subfolders
            if recursive:
                folders = [
                    f for f in all_files 
                    if f['mimeType'] == 'application/vnd.google-apps.folder'
                ]
                for folder in folders:
                    all_files.extend(
                        self.list_files_in_folder(folder['id'], recursive=True)
                    )

            return all_files

        except HttpError as error:
            console.print(f"[red]Error listing files: {error}[/red]")
            return []

    def download_file(
        self,
        file_id: str,
        file_metadata: Dict[str, Any],
        destination: Path,
        progress: Progress,
        task_id: int
    ) -> bool:
        """
        Download a file from Google Drive.
        
        Args:
            file_id: ID of the file to download
            file_metadata: File metadata from Drive API
            destination: Local destination path
            progress: Rich progress bar
            task_id: Progress task ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            mime_type = file_metadata['mimeType']

            # Handle Google Workspace files
            if mime_type.startswith('application/vnd.google-apps'):
                if not self.convert_google_docs:
                    console.print(
                        f"[yellow]Skipping Google Workspace file: "
                        f"{file_metadata['name']}[/yellow]"
                    )
                    return False

                if mime_type in EXPORT_FORMATS:
                    return self._export_google_file(
                        file_id, file_metadata, destination, progress, task_id
                    )
                else:
                    console.print(
                        f"[yellow]Unsupported Google Workspace type: "
                        f"{mime_type}[/yellow]"
                    )
                    return False

            # Regular file download
            request = self.service.files().get_media(fileId=file_id)
            destination.parent.mkdir(parents=True, exist_ok=True)

            with open(destination, 'wb') as fh:
                downloader = MediaIoBaseDownload(fh, request, chunksize=1024*1024)
                done = False

                while not done:
                    status, done = downloader.next_chunk()
                    if status:
                        progress.update(
                            task_id,
                            completed=int(status.progress() * 100)
                        )

            progress.update(task_id, completed=100)
            return True

        except HttpError as error:
            console.print(
                f"[red]Error downloading {file_metadata['name']}: {error}[/red]"
            )
            return False
        except Exception as error:
            console.print(
                f"[red]Unexpected error downloading {file_metadata['name']}: "
                f"{error}[/red]"
            )
            return False

    def _export_google_file(
        self,
        file_id: str,
        file_metadata: Dict[str, Any],
        destination: Path,
        progress: Progress,
        task_id: int
    ) -> bool:
        """Export a Google Workspace file to Open Document Format."""
        try:
            mime_type = file_metadata['mimeType']
            export_config = EXPORT_FORMATS[mime_type]

            # Update destination with correct extension
            destination = destination.with_suffix(export_config['extension'])
            destination.parent.mkdir(parents=True, exist_ok=True)

            request = self.service.files().export_media(
                fileId=file_id,
                mimeType=export_config['format']
            )

            with open(destination, 'wb') as fh:
                downloader = MediaIoBaseDownload(fh, request, chunksize=1024*1024)
                done = False

                while not done:
                    status, done = downloader.next_chunk()
                    if status:
                        progress.update(
                            task_id,
                            completed=int(status.progress() * 100)
                        )

            progress.update(task_id, completed=100)
            return True

        except HttpError as error:
            console.print(
                f"[red]Error exporting {file_metadata['name']}: {error}[/red]"
            )
            return False

    def upload_file(
        self,
        file_path: Path,
        parent_folder_id: str,
        progress: Progress,
        task_id: int
    ) -> Optional[str]:
        """
        Upload a file to Google Drive.
        
        Args:
            file_path: Local file path
            parent_folder_id: ID of parent folder in Drive
            progress: Rich progress bar
            task_id: Progress task ID
            
        Returns:
            File ID if successful, None otherwise
        """
        try:
            file_metadata = {
                'name': file_path.name,
                'parents': [parent_folder_id]
            }

            media = MediaFileUpload(
                str(file_path),
                resumable=True,
                chunksize=1024*1024
            )

            request = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            )

            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    progress.update(
                        task_id,
                        completed=int(status.progress() * 100)
                    )

            progress.update(task_id, completed=100)
            return response.get('id')

        except HttpError as error:
            console.print(f"[red]Error uploading {file_path.name}: {error}[/red]")
            return None

    def create_folder(
        self,
        folder_name: str,
        parent_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Create a folder in Google Drive.
        
        Args:
            folder_name: Name of the folder to create
            parent_id: ID of parent folder (None for root)
            
        Returns:
            Folder ID if successful, None otherwise
        """
        try:
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }

            if parent_id:
                file_metadata['parents'] = [parent_id]

            folder = self.service.files().create(
                body=file_metadata,
                fields='id'
            ).execute()

            return folder.get('id')

        except HttpError as error:
            console.print(f"[red]Error creating folder {folder_name}: {error}[/red]")
            return None

    def delete_file(self, file_id: str) -> bool:
        """
        Delete a file from Google Drive.
        
        Args:
            file_id: ID of file to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.service.files().delete(fileId=file_id).execute()
            return True
        except HttpError as error:
            console.print(f"[red]Error deleting file: {error}[/red]")
            return False
