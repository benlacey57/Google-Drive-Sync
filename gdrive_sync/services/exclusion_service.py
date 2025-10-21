"""Exclusion pattern management service."""

import fnmatch
from pathlib import Path
from typing import Set, List, Optional
from rich.console import Console

from gdrive_sync.utils.constants import DEFAULT_EXCLUSIONS

console = Console()


class ExclusionService:
    """Manages file and folder exclusion patterns."""

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize exclusion service.
        
        Args:
            config_path: Path to exclusion configuration file
        """
        self.exclusions: Set[str] = set(DEFAULT_EXCLUSIONS)
        self.config_path = config_path
        if self.config_path:
            self._load_exclusions()

    def _load_exclusions(self):
        """Load exclusions from configuration file."""
        if not self.config_path or not self.config_path.exists():
            return

        try:
            with open(self.config_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        self.exclusions.add(line)
        except Exception as e:
            console.print(
                f"[yellow]Warning: Could not load exclusions from "
                f"{self.config_path}: {e}[/yellow]"
            )

    def save_exclusions(self):
        """Save current exclusions to configuration file."""
        if not self.config_path:
            return

        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w') as f:
                f.write("# Google Drive Sync Exclusion Patterns\n")
                f.write("# One pattern per line. Supports wildcards (* and ?)\n")
                f.write("# Lines starting with # are comments\n\n")
                for pattern in sorted(self.exclusions):
                    f.write(f"{pattern}\n")
        except Exception as e:
            console.print(f"[red]Error saving exclusions: {e}[/red]")

    def add_exclusion(self, pattern: str):
        """
        Add an exclusion pattern.
        
        Args:
            pattern: Exclusion pattern to add
        """
        self.exclusions.add(pattern)

    def remove_exclusion(self, pattern: str):
        """
        Remove an exclusion pattern.
        
        Args:
            pattern: Exclusion pattern to remove
        """
        self.exclusions.discard(pattern)

    def add_exclusions(self, patterns: List[str]):
        """
        Add multiple exclusion patterns.
        
        Args:
            patterns: List of exclusion patterns
        """
        for pattern in patterns:
            self.exclusions.add(pattern)

    def should_exclude(self, path: Path, base_path: Optional[Path] = None) -> bool:
        """
        Check if a path should be excluded based on patterns.
        
        Args:
            path: Path to check
            base_path: Base path for relative pattern matching
            
        Returns:
            True if path should be excluded
        """
        # Check the filename
        if self._matches_pattern(path.name):
            return True

        # Check relative path components if base_path provided
        if base_path:
            try:
                relative = path.relative_to(base_path)
                # Check each component of the path
                for part in relative.parts:
                    if self._matches_pattern(part):
                        return True
                # Check the full relative path
                if self._matches_pattern(str(relative)):
                    return True
            except ValueError:
                pass

        return False

    def _matches_pattern(self, name: str) -> bool:
        """
        Check if a name matches any exclusion pattern.
        
        Args:
            name: Name to check
            
        Returns:
            True if name matches any pattern
        """
        for pattern in self.exclusions:
            if fnmatch.fnmatch(name, pattern):
                return True
        return False

    def get_exclusions_list(self) -> List[str]:
        """
        Get sorted list of exclusion patterns.
        
        Returns:
            Sorted list of patterns
        """
        return sorted(self.exclusions)

    def reset_to_defaults(self):
        """Reset exclusions to default patterns."""
        self.exclusions = set(DEFAULT_EXCLUSIONS)
