"""Google Drive path resolution."""

from typing import Optional, List, Tuple
from googleapiclient.errors import HttpError
from rich.console import Console

console = Console()


class PathResolver:
    """Resolves Google Drive paths to folder IDs."""

    def __init__(self, service):
        """
        Initialize path resolver.
        
        Args:
            service: Google Drive API service
        """
        self.service = service
        self._cache = {}  # Cache path to ID mappings

    def resolve_path(self, path: str, create_if_missing: bool = False) -> Optional[str]:
        """
        Resolve a Google Drive path to a folder ID.
        
        Args:
            path: Path like '/photos/2024' or 'documents/work'
            create_if_missing: Create folders if they don't exist
            
        Returns:
            Folder ID or None if not found/created
        """
        # Normalise path
        path = path.strip()
        if not path or path == '/':
            return 'root'

        # Remove leading/trailing slashes
        path = path.strip('/')
        
        # Check cache
        if path in self._cache:
            return self._cache[path]

        # Split path into components
        components = path.split('/')
        current_id = 'root'

        for component in components:
            folder_id = self._find_folder(component, current_id)
            
            if not folder_id:
                if create_if_missing:
                    folder_id = self._create_folder(component, current_id)
                    if not folder_id:
                        return None
                else:
                    console.print(f"[yellow]Folder not found: {component} in path {path}[/yellow]")
                    return None
            
            current_id = folder_id

        # Cache the result
        self._cache[path] = current_id
        return current_id

    def _find_folder(self, name: str, parent_id: str) -> Optional[str]:
        """Find a folder by name within a parent."""
        try:
            # Escape single quotes in the name
            escaped_name = name.replace("'", "\\'")
            query = (
                f"name='{escaped_name}' and "
                f"'{parent_id}' in parents and "
                f"mimeType='application/vnd.google-apps.folder' and "
                f"trashed=false"
            )
            
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)',
                pageSize=1
            ).execute()

            files = results.get('files', [])
            if files:
                return files[0]['id']
            return None

        except HttpError as error:
            console.print(f"[red]Error finding folder {name}: {error}[/red]")
            return None

    def _create_folder(self, name: str, parent_id: str) -> Optional[str]:
        """Create a folder in the specified parent."""
        try:
            file_metadata = {
                'name': name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [parent_id]
            }

            folder = self.service.files().create(
                body=file_metadata,
                fields='id'
            ).execute()

            folder_id = folder.get('id')
            console.print(f"[green]Created folder: {name}[/green]")
            return folder_id

        except HttpError as error:
            console.print(f"[red]Error creating folder {name}: {error}[/red]")
            return None

    def get_path_from_id(self, folder_id: str) -> str:
        """Get the full path for a folder ID."""
        if folder_id == 'root':
            return '/'

        path_components = []
        current_id = folder_id

        try:
            while current_id != 'root':
                file = self.service.files().get(
                    fileId=current_id,
                    fields='name, parents'
                ).execute()

                path_components.insert(0, file['name'])
                
                parents = file.get('parents', [])
                if not parents:
                    break
                current_id = parents[0]

            return '/' + '/'.join(path_components)

        except HttpError as error:
            console.print(f"[red]Error resolving path: {error}[/red]")
            return f"/{folder_id}"

    def list_folders(self, parent_path: str = '/') -> List[Tuple[str, str]]:
        """
        List all folders in a given path.
        
        Returns:
            List of tuples (folder_name, full_path)
        """
        parent_id = self.resolve_path(parent_path)
        if not parent_id:
            return []

        try:
            query = (
                f"'{parent_id}' in parents and "
                f"mimeType='application/vnd.google-apps.folder' and "
                f"trashed=false"
            )
            
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)',
                pageSize=1000,
                orderBy='name'
            ).execute()

            folders = results.get('files', [])
            parent_path_clean = parent_path.rstrip('/')
            
            return [
                (folder['name'], f"{parent_path_clean}/{folder['name']}")
                for folder in folders
            ]

        except HttpError as error:
            console.print(f"[red]Error listing folders: {error}[/red]")
            return []

    def clear_cache(self):
        """Clear the path resolution cache."""
        self._cache.clear()
