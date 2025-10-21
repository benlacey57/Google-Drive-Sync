"""Configuration models."""

from dataclasses import dataclass, field, asdict
from typing import List, Optional
from pathlib import Path
import json


@dataclass
class OperationConfig:
    """Base configuration for all operations."""
    exclude_patterns: List[str] = field(default_factory=list)
    max_file_size_mb: int = 0  # 0 = no limit
    use_compression: bool = True
    resume: bool = True

    def get_max_file_size_bytes(self) -> Optional[int]:
        """Get max file size in bytes."""
        if self.max_file_size_mb > 0:
            return self.max_file_size_mb * 1024 * 1024
        return None


@dataclass
class DownloadConfig(OperationConfig):
    """Configuration for download operations."""
    paths: List[str] = field(default_factory=list)
    destination: str = ""
    convert_google_docs: bool = True

    @classmethod
    def from_file(cls, config_path: Path) -> 'DownloadConfig':
        """Load configuration from JSON file."""
        with open(config_path, 'r') as f:
            data = json.load(f)
        return cls(**data)

    def save(self, config_path: Path):
        """Save configuration to JSON file."""
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, 'w') as f:
            json.dump(asdict(self), f, indent=2)

    def validate(self) -> tuple[bool, str]:
        """Validate configuration."""
        if not self.paths:
            return False, "No paths specified"
        if not self.destination:
            return False, "No destination specified"
        return True, ""


@dataclass
class UploadConfig(OperationConfig):
    """Configuration for upload operations."""
    source: str = ""
    destination_path: str = ""

    @classmethod
    def from_file(cls, config_path: Path) -> 'UploadConfig':
        """Load configuration from JSON file."""
        with open(config_path, 'r') as f:
            data = json.load(f)
        return cls(**data)

    def save(self, config_path: Path):
        """Save configuration to JSON file."""
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, 'w') as f:
            json.dump(asdict(self), f, indent=2)

    def validate(self) -> tuple[bool, str]:
        """Validate configuration."""
        if not self.source:
            return False, "No source specified"
        if not Path(self.source).exists():
            return False, f"Source path does not exist: {self.source}"
        if not self.destination_path:
            return False, "No destination path specified"
        return True, ""


@dataclass
class SyncConfig(OperationConfig):
    """Configuration for sync operations."""
    paths: List[str] = field(default_factory=list)
    destination: str = ""
    bidirectional: bool = True
    delete_missing: bool = False
    delete_missing_remote: bool = False
    convert_google_docs: bool = True

    @classmethod
    def from_file(cls, config_path: Path) -> 'SyncConfig':
        """Load configuration from JSON file."""
        with open(config_path, 'r') as f:
            data = json.load(f)
        return cls(**data)

    def save(self, config_path: Path):
        """Save configuration to JSON file."""
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, 'w') as f:
            json.dump(asdict(self), f, indent=2)

    def validate(self) -> tuple[bool, str]:
        """Validate configuration."""
        if not self.paths:
            return False, "No paths specified"
        if not self.destination:
            return False, "No destination specified"
        return True, ""


@dataclass
class ApplicationConfig:
    """Main application configuration."""
    credentials_path: str = "credentials.json"
    token_path: str = "token.json"
    data_dir: str = str(Path.home() / '.gdrive_sync')
    default_exclude_file: str = ".gdriveignore"

    @classmethod
    def from_file(cls, config_path: Path) -> 'ApplicationConfig':
        """Load configuration from JSON file."""
        if not config_path.exists():
            return cls()
        with open(config_path, 'r') as f:
            data = json.load(f)
        return cls(**data)

    def save(self, config_path: Path):
        """Save configuration to JSON file."""
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, 'w') as f:
            json.dump(asdict(self), f, indent=2)
