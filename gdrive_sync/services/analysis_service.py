"""Drive storage analysis service."""

from pathlib import Path
from typing import Dict, Any, List
from collections import defaultdict
from googleapiclient.errors import HttpError
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
import json
from datetime import datetime

from gdrive_sync.domain.enums import FileCategory
from gdrive_sync.infrastructure.drive.path_resolver import PathResolver

console = Console()


class AnalysisService:
    """Analyses Google Drive storage and provides statistics."""

    def __init__(self, service, path_resolver: PathResolver):
        """
        Initialize analysis service.
        
        Args:
            service: Google Drive API service
            path_resolver: Path resolver instance
        """
        self.service = service
        self.path_resolver = path_resolver

    def analyse_drive(self, path: str = '/') -> Dict[str, Any]:
        """
        Analyse Drive contents and generate statistics.
        
        Args:
            path: Drive path to analyse
            
        Returns:
            Dictionary of statistics
        """
        folder_id = self.path_resolver.resolve_path(path)
        if not folder_id:
            return {}

        console.print(f"[cyan]Analysing {path}...[/cyan]")

        stats = {
            'path': path,
            'total_files': 0,
            'total_size': 0,
            'by_extension': defaultdict(lambda: {'count': 0, 'size': 0}),
            'by_folder': defaultdict(lambda: {'count': 0, 'size': 0}),
            'google_docs': {'count': 0, 'types': defaultdict(int)},
            'largest_files': [],
            'file_type_distribution': defaultdict(int)
        }

        # Get all files recursively
        all_files = self._get_all_files_recursive(folder_id, path)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task(
                f"[cyan]Analysing {len(all_files)} files...",
                total=len(all_files)
            )

            for file_info in all_files:
                file_data = file_info['file']
                folder_path = file_info['folder_path']
                
                # Basic stats
                stats['total_files'] += 1
                
                mime_type = file_data.get('mimeType', '')
                file_size = int(file_data.get('size', 0))
                file_name = file_data['name']

                # Handle Google Workspace files
                if mime_type.startswith('application/vnd.google-apps'):
                    stats['google_docs']['count'] += 1
                    doc_type = mime_type.split('.')[-1]
                    stats['google_docs']['types'][doc_type] += 1
                else:
                    stats['total_size'] += file_size

                # Extension analysis
                ext = Path(file_name).suffix.lower() or 'no_extension'
                stats['by_extension'][ext]['count'] += 1
                stats['by_extension'][ext]['size'] += file_size

                # Folder analysis
                stats['by_folder'][folder_path]['count'] += 1
                stats['by_folder'][folder_path]['size'] += file_size

                # File type categorisation
                file_type = self._categorise_file_type(mime_type, ext)
                stats['file_type_distribution'][file_type.value] += 1

                # Track largest files
                if file_size > 0:
                    stats['largest_files'].append({
                        'name': file_name,
                        'size': file_size,
                        'path': folder_path,
                        'mime_type': mime_type
                    })

                progress.advance(task)

        # Sort largest files
        stats['largest_files'].sort(key=lambda x: x['size'], reverse=True)
        stats['largest_files'] = stats['largest_files'][:20]

        return stats

    def _get_all_files_recursive(
        self,
        folder_id: str,
        folder_path: str
    ) -> List[Dict[str, Any]]:
        """
        Recursively get all files in a folder.
        
        Args:
            folder_id: ID of folder to scan
            folder_path: Path of the folder
            
        Returns:
            List of file information dictionaries
        """
        all_files = []
        page_token = None

        try:
            while True:
                query = f"'{folder_id}' in parents and trashed=false"
                
                results = self.service.files().list(
                    q=query,
                    spaces='drive',
                    fields='nextPageToken, files(id, name, mimeType, size, parents)',
                    pageToken=page_token,
                    pageSize=1000
                ).execute()

                files = results.get('files', [])
                
                for file_data in files:
                    if file_data['mimeType'] == 'application/vnd.google-apps.folder':
                        # Recurse into subfolder
                        subfolder_path = f"{folder_path.rstrip('/')}/{file_data['name']}"
                        all_files.extend(
                            self._get_all_files_recursive(file_data['id'], subfolder_path)
                        )
                    else:
                        all_files.append({
                            'file': file_data,
                            'folder_path': folder_path
                        })

                page_token = results.get('nextPageToken')
                if not page_token:
                    break

        except HttpError as error:
            console.print(f"[red]Error scanning folder: {error}[/red]")

        return all_files

    def _categorise_file_type(self, mime_type: str, extension: str) -> FileCategory:
        """
        Categorise file into broad types.
        
        Args:
            mime_type: MIME type of file
            extension: File extension
            
        Returns:
            FileCategory enum
        """
        if mime_type.startswith('image/'):
            return FileCategory.IMAGES
        elif mime_type.startswith('video/'):
            return FileCategory.VIDEOS
        elif mime_type.startswith('audio/'):
            return FileCategory.AUDIO
        elif mime_type.startswith('text/') or extension in {'.txt', '.md', '.log'}:
            return FileCategory.TEXT
        elif extension in {'.pdf'}:
            return FileCategory.PDFS
        elif extension in {'.doc', '.docx', '.odt'}:
            return FileCategory.DOCUMENTS
        elif extension in {'.xls', '.xlsx', '.ods', '.csv'}:
            return FileCategory.SPREADSHEETS
        elif extension in {'.ppt', '.pptx', '.odp'}:
            return FileCategory.PRESENTATIONS
        elif extension in {'.zip', '.tar', '.gz', '.7z', '.rar'}:
            return FileCategory.ARCHIVES
        elif mime_type.startswith('application/vnd.google-apps'):
            return FileCategory.GOOGLE_DOCS
        else:
            return FileCategory.OTHER

    def display_analysis(self, stats: Dict[str, Any]):
        """
        Display analysis results in rich tables.
        
        Args:
            stats: Statistics dictionary from analyse_drive()
        """
        console.print(f"\n[bold cyan]Storage Analysis for {stats['path']}[/bold cyan]\n")

        # Summary
        summary_table = Table(show_header=False, box=None)
        summary_table.add_column("Metric", style="cyan", width=30)
        summary_table.add_column("Value", style="green")

        summary_table.add_row("Total Files", f"{stats['total_files']:,}")
        summary_table.add_row(
            "Total Size",
            f"{stats['total_size'] / (1024**3):.2f} GB"
        )
        summary_table.add_row(
            "Google Workspace Files",
            f"{stats['google_docs']['count']:,}"
        )
        
        if stats['total_files'] > stats['google_docs']['count']:
            avg_size = stats['total_size'] / (
                stats['total_files'] - stats['google_docs']['count']
            )
            summary_table.add_row(
                "Average File Size",
                f"{avg_size / (1024**2):.2f} MB"
            )

        console.print(summary_table)
        console.print()

        # File type distribution
        console.print("[bold cyan]File Type Distribution[/bold cyan]\n")
        type_table = Table(show_header=True, header_style="bold magenta")
        type_table.add_column("Type", style="cyan")
        type_table.add_column("Count", style="green", justify="right")
        type_table.add_column("Percentage", style="yellow", justify="right")

        sorted_types = sorted(
            stats['file_type_distribution'].items(),
            key=lambda x: x[1],
            reverse=True
        )

        for file_type, count in sorted_types:
            percentage = (count / stats['total_files']) * 100
            type_table.add_row(
                file_type,
                f"{count:,}",
                f"{percentage:.1f}%"
            )

        console.print(type_table)
        console.print()

        # Top extensions
        console.print("[bold cyan]Top Extensions by Size[/bold cyan]\n")
        ext_table = Table(show_header=True, header_style="bold magenta")
        ext_table.add_column("Extension", style="cyan")
        ext_table.add_column("Files", style="green", justify="right")
        ext_table.add_column("Total Size", style="yellow", justify="right")

        sorted_exts = sorted(
            stats['by_extension'].items(),
            key=lambda x: x[1]['size'],
            reverse=True
        )[:15]

        for ext, data in sorted_exts:
            ext_table.add_row(
                ext,
                f"{data['count']:,}",
                f"{data['size'] / (1024**2):.2f} MB"
            )

        console.print(ext_table)
        console.print()

        # Top folders
        console.print("[bold cyan]Top Folders by Size[/bold cyan]\n")
        folder_table = Table(show_header=True, header_style="bold magenta")
        folder_table.add_column("Folder", style="cyan", width=50)
        folder_table.add_column("Files", style="green", justify="right")
        folder_table.add_column("Total Size", style="yellow", justify="right")

        sorted_folders = sorted(
            stats['by_folder'].items(),
            key=lambda x: x[1]['size'],
            reverse=True
        )[:15]

        for folder, data in sorted_folders:
            folder_table.add_row(
                folder,
                f"{data['count']:,}",
                f"{data['size'] / (1024**2):.2f} MB"
            )

        console.print(folder_table)
        console.print()

        # Largest files
        if stats['largest_files']:
            console.print("[bold cyan]Largest Files[/bold cyan]\n")
            large_table = Table(show_header=True, header_style="bold magenta")
            large_table.add_column("File", style="cyan", width=40)
            large_table.add_column("Size", style="green", justify="right")
            large_table.add_column("Path", style="yellow", width=40)

            for file_info in stats['largest_files'][:10]:
                large_table.add_row(
                    file_info['name'],
                    f"{file_info['size'] / (1024**2):.2f} MB",
                    file_info['path']
                )

            console.print(large_table)
            console.print()

    def export_analysis(self, stats: Dict[str, Any], output_path: Path):
        """
        Export analysis to JSON file.
        
        Args:
            stats: Statistics dictionary
            output_path: Path to save JSON file
        """
        # Convert defaultdicts to regular dicts for JSON serialisation
        export_data = {
            'path': stats['path'],
            'total_files': stats['total_files'],
            'total_size': stats['total_size'],
            'by_extension': dict(stats['by_extension']),
            'by_folder': dict(stats['by_folder']),
            'google_docs': {
                'count': stats['google_docs']['count'],
                'types': dict(stats['google_docs']['types'])
            },
            'largest_files': stats['largest_files'],
            'file_type_distribution': dict(stats['file_type_distribution']),
            'generated_at': datetime.now().isoformat()
        }

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2)

        console.print(f"[green]Analysis exported to {output_path}[/green]")
