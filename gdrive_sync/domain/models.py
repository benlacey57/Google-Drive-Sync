"""Domain models."""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import json


@dataclass
class SyncState:
    """Represents the state of a synchronisation operation."""
    operation: str
    paths: List[str]
    local_path: str
    last_sync: str
    completed_files: List[str] = field(default_factory=list)
    failed_files: Dict[str, str] = field(default_factory=dict)
    total_files: int = 0
    total_size: int = 0

    def save(self, state_file: Path):
        """Save the current state to a file."""
        state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(state_file, 'w') as f:
            json.dump(asdict(self), f, indent=2)

    @classmethod
    def load(cls, state_file: Path) -> Optional['SyncState']:
        """Load state from a file."""
        if not state_file.exists():
            return None
        try:
            with open(state_file, 'r') as f:
                data = json.load(f)
            return cls(**data)
        except (json.JSONDecodeError, TypeError):
            return None


@dataclass
class PerformanceMetrics:
    """Tracks performance metrics for operations."""
    operation: str
    start_time: float
    end_time: float = 0.0
    total_files: int = 0
    successful_files: int = 0
    failed_files: int = 0
    total_bytes_original: int = 0
    total_bytes_transferred: int = 0
    compressed_files: int = 0
    bytes_saved_compression: int = 0
    excluded_files: int = 0
    errors: List[Dict[str, str]] = field(default_factory=list)

    def finish(self):
        """Mark the operation as finished."""
        import time
        self.end_time = time.time()

    def duration(self) -> float:
        """Calculate operation duration in seconds."""
        import time
        end = self.end_time if self.end_time > 0 else time.time()
        return end - self.start_time

    def average_speed(self) -> float:
        """Calculate average transfer speed in bytes per second."""
        duration = self.duration()
        if duration > 0:
            return self.total_bytes_transferred / duration
        return 0.0

    def compression_ratio(self) -> float:
        """Calculate compression ratio percentage."""
        if self.total_bytes_original > 0:
            return (1 - (self.total_bytes_transferred / self.total_bytes_original)) * 100
        return 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            'operation': self.operation,
            'start_time': datetime.fromtimestamp(self.start_time).isoformat(),
            'end_time': datetime.fromtimestamp(self.end_time).isoformat() if self.end_time > 0 else None,
            'duration_seconds': self.duration(),
            'total_files': self.total_files,
            'successful_files': self.successful_files,
            'failed_files': self.failed_files,
            'excluded_files': self.excluded_files,
            'total_bytes_original': self.total_bytes_original,
            'total_bytes_transferred': self.total_bytes_transferred,
            'compressed_files': self.compressed_files,
            'bytes_saved_compression': self.bytes_saved_compression,
            'average_speed_mbps': self.average_speed() / (1024 * 1024),
            'compression_ratio_percent': self.compression_ratio(),
            'errors': self.errors
        }


@dataclass
class DriveFileInfo:
    """Information about a Drive file."""
    id: str
    name: str
    mime_type: str
    size: int
    modified_time: str
    path: str
    parents: List[str] = field(default_factory=list)
    md5_checksum: Optional[str] = None

    @classmethod
    def from_api_response(cls, file_data: Dict[str, Any], path: str) -> 'DriveFileInfo':
        """Create from Google Drive API response."""
        return cls(
            id=file_data['id'],
            name=file_data['name'],
            mime_type=file_data.get('mimeType', ''),
            size=int(file_data.get('size', 0)),
            modified_time=file_data.get('modifiedTime', ''),
            path=path,
            parents=file_data.get('parents', []),
            md5_checksum=file_data.get('md5Checksum')
        )
