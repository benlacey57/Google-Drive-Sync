"""Configuration loading and management."""

from pathlib import Path
from typing import Optional
from rich.console import Console

from .models import DownloadConfig, UploadConfig, SyncConfig, ApplicationConfig

console = Console()


class ConfigLoader:
    """Loads and manages configuration files."""

    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize configuration loader.
        
        Args:
            config_dir: Directory containing configuration files
        """
        self.config_dir = config_dir or Path.cwd() / 'config'
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def load_download_config(self, name: str = "download") -> Optional[DownloadConfig]:
        """Load download configuration."""
        config_path = self.config_dir / f"{name}.json"
        if not config_path.exists():
            console.print(f"[yellow]Config file not found: {config_path}[/yellow]")
            return None

        try:
            config = DownloadConfig.from_file(config_path)
            valid, message = config.validate()
            if not valid:
                console.print(f"[red]Invalid configuration: {message}[/red]")
                return None
            return config
        except Exception as e:
            console.print(f"[red]Error loading config: {e}[/red]")
            return None

    def load_upload_config(self, name: str = "upload") -> Optional[UploadConfig]:
        """Load upload configuration."""
        config_path = self.config_dir / f"{name}.json"
        if not config_path.exists():
            console.print(f"[yellow]Config file not found: {config_path}[/yellow]")
            return None

        try:
            config = UploadConfig.from_file(config_path)
            valid, message = config.validate()
            if not valid:
                console.print(f"[red]Invalid configuration: {message}[/red]")
                return None
            return config
        except Exception as e:
            console.print(f"[red]Error loading config: {e}[/red]")
            return None

    def load_sync_config(self, name: str = "sync") -> Optional[SyncConfig]:
        """Load sync configuration."""
        config_path = self.config_dir / f"{name}.json"
        if not config_path.exists():
            console.print(f"[yellow]Config file not found: {config_path}[/yellow]")
            return None

        try:
            config = SyncConfig.from_file(config_path)
            valid, message = config.validate()
            if not valid:
                console.print(f"[red]Invalid configuration: {message}[/red]")
                return None
            return config
        except Exception as e:
            console.print(f"[red]Error loading config: {e}[/red]")
            return None

    def load_app_config(self) -> ApplicationConfig:
        """Load application configuration."""
        config_path = self.config_dir / "app.json"
        return ApplicationConfig.from_file(config_path)

    def save_download_config(self, config: DownloadConfig, name: str = "download"):
        """Save download configuration."""
        config_path = self.config_dir / f"{name}.json"
        config.save(config_path)
        console.print(f"[green]Configuration saved to {config_path}[/green]")

    def save_upload_config(self, config: UploadConfig, name: str = "upload"):
        """Save upload configuration."""
        config_path = self.config_dir / f"{name}.json"
        config.save(config_path)
        console.print(f"[green]Configuration saved to {config_path}[/green]")

    def save_sync_config(self, config: SyncConfig, name: str = "sync"):
        """Save sync configuration."""
        config_path = self.config_dir / f"{name}.json"
        config.save(config_path)
        console.print(f"[green]Configuration saved to {config_path}[/green]")

    def list_configs(self) -> dict[str, list[str]]:
        """List all available configurations."""
        configs = {
            'download': [],
            'upload': [],
            'sync': []
        }

        for file in self.config_dir.glob('*.json'):
            name = file.stem
            if name == 'app':
                continue
            
            # Try to determine type by loading
            try:
                with open(file, 'r') as f:
                    import json
                    data = json.load(f)
                
                if 'paths' in data and 'destination' in data:
                    if 'bidirectional' in data:
                        configs['sync'].append(name)
                    else:
                        configs['download'].append(name)
                elif 'source' in data and 'destination_path' in data:
                    configs['upload'].append(name)
            except:
                pass

        return configs
