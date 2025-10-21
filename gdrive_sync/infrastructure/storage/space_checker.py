"""Disk space checking utilities."""

import shutil
from pathlib import Path
from typing import Tuple
from rich.console import Console
from rich.table import Table

console = Console()


class StorageChecker:
    """Checks available disk space before operations."""

    @staticmethod
    def check_available_space(path: Path) -> Tuple[int, int, int]:
        """
        Check available disk space at path.
        
        Args:
            path: Path to check
            
        Returns:
            Tuple of (total, used, free) in bytes
        """
        # Ensure path exists
        path.mkdir(parents=True, exist_ok=True)
        
        stat = shutil.disk_usage(path)
        return stat.total, stat.used, stat.free

    @staticmethod
    def format_bytes(bytes_val: int) -> str:
        """
        Format bytes into human-readable format.
        
        Args:
            bytes_val: Number of bytes
            
        Returns:
            Formatted string
        """
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_val < 1024.0:
                return f"{bytes_val:.2f} {unit}"
            bytes_val /= 1024.0
        return f"{bytes_val:.2f} PB"

    @staticmethod
    def check_sufficient_space(
        path: Path,
        required_bytes: int,
        safety_margin: float = 0.1
    ) -> Tuple[bool, str]:
        """
        Check if there's sufficient space for an operation.
        
        Args:
            path: Path to check
            required_bytes: Required space in bytes
            safety_margin: Safety margin as percentage (0.1 = 10%)
            
        Returns:
            Tuple of (sufficient, message)
        """
        total, used, free = StorageChecker.check_available_space(path)
        
        # Add safety margin
        required_with_margin = int(required_bytes * (1 + safety_margin))
        
        if free < required_with_margin:
            return False, (
                f"Insufficient disk space!\n"
                f"Required: {StorageChecker.format_bytes(required_with_margin)}\n"
                f"Available: {StorageChecker.format_bytes(free)}\n"
                f"Shortage: {StorageChecker.format_bytes(required_with_margin - free)}"
            )
        
        return True, (
            f"Sufficient space available\n"
            f"Required: {StorageChecker.format_bytes(required_with_margin)}\n"
            f"Available: {StorageChecker.format_bytes(free)}"
        )

    @staticmethod
    def display_disk_info(path: Path):
        """
        Display disk information in a table.
        
        Args:
            path: Path to display info for
        """
        total, used, free = StorageChecker.check_available_space(path)
        
        table = Table(show_header=False, box=None)
        table.add_column("Metric", style="cyan", width=20)
        table.add_column("Value", style="green")
        
        table.add_row("Path", str(path))
        table.add_row("Total Space", StorageChecker.format_bytes(total))
        table.add_row("Used Space", StorageChecker.format_bytes(used))
        table.add_row("Free Space", StorageChecker.format_bytes(free))
        table.add_row("Usage", f"{(used/total)*100:.1f}%")
        
        console.print("\n")
        console.print(table)
        console.print("\n")
