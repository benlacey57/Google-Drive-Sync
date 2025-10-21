"""Metrics and logging management."""

import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from collections import defaultdict
from typing import Dict, Any, List
from datetime import datetime
import time

from rich.console import Console
from rich.table import Table

from gdrive_sync.domain.models import PerformanceMetrics

console = Console()


class MetricsLogger:
    """Manages logging and metrics storage."""

    def __init__(self, base_path: Path):
        """
        Initialize metrics logger.
        
        Args:
            base_path: Base directory for logs and metrics
        """
        self.base_path = base_path
        self.logs_path = base_path / 'logs'
        self.metrics_path = base_path / 'metrics'
        self.state_path = base_path / 'state'

        # Create directories
        self.logs_path.mkdir(parents=True, exist_ok=True)
        self.metrics_path.mkdir(parents=True, exist_ok=True)
        self.state_path.mkdir(parents=True, exist_ok=True)

        self._setup_logging()

    def _setup_logging(self):
        """Configure logging with rotation."""
        log_file = self.logs_path / 'gdrive_sync.log'

        # Create logger
        self.logger = logging.getLogger('GDriveSync')
        self.logger.setLevel(logging.DEBUG)
        
        # Clear existing handlers
        self.logger.handlers.clear()

        # Rotating file handler (10MB per file, keep 5 files)
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)

        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def log_operation(self, level: str, message: str, **kwargs):
        """
        Log an operation with optional metadata.
        
        Args:
            level: Log level (debug, info, warning, error, critical)
            message: Log message
            **kwargs: Additional metadata
        """
        log_method = getattr(self.logger, level.lower())
        log_method(message, extra=kwargs)

    def save_metrics(self, metrics: PerformanceMetrics):
        """
        Save performance metrics to JSON file.
        
        Args:
            metrics: Performance metrics to save
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        metrics_file = self.metrics_path / f'metrics_{timestamp}.json'

        with open(metrics_file, 'w') as f:
            json.dump(metrics.to_dict(), f, indent=2)

        self.logger.info(f"Metrics saved to {metrics_file}")

    def save_operation_log(self, operation: str, details: Dict[str, Any]):
        """
        Save detailed operation log as JSON.
        
        Args:
            operation: Operation type
            details: Operation details
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = self.logs_path / f'{operation}_{timestamp}.json'

        details['timestamp'] = datetime.now().isoformat()
        details['operation'] = operation

        with open(log_file, 'w') as f:
            json.dump(details, f, indent=2)

    def get_statistics(self, days: int = 7) -> Dict[str, Any]:
        """
        Get statistics from recent metrics files.
        
        Args:
            days: Number of days to look back
            
        Returns:
            Dictionary of statistics
        """
        stats = {
            'total_operations': 0,
            'operations_by_type': defaultdict(int),
            'total_files_processed': 0,
            'total_bytes_transferred': 0,
            'total_bytes_saved': 0,
            'average_speed_mbps': 0.0,
            'success_rate': 0.0,
            'recent_errors': []
        }

        cutoff_time = time.time() - (days * 24 * 3600)
        metrics_files = sorted(self.metrics_path.glob('metrics_*.json'))

        speeds = []
        total_successful = 0
        total_files = 0

        for metrics_file in metrics_files:
            # Check if file is recent enough
            if metrics_file.stat().st_mtime < cutoff_time:
                continue

            try:
                with open(metrics_file, 'r') as f:
                    data = json.load(f)

                stats['total_operations'] += 1
                stats['operations_by_type'][data['operation']] += 1
                stats['total_files_processed'] += data['total_files']
                stats['total_bytes_transferred'] += data['total_bytes_transferred']
                stats['total_bytes_saved'] += data['bytes_saved_compression']

                if data.get('average_speed_mbps', 0) > 0:
                    speeds.append(data['average_speed_mbps'])

                total_successful += data['successful_files']
                total_files += data['total_files']

                # Collect recent errors
                for error in data.get('errors', [])[:5]:
                    stats['recent_errors'].append(error)

            except (json.JSONDecodeError, KeyError) as e:
                self.logger.warning(f"Error reading metrics file {metrics_file}: {e}")

        if speeds:
            stats['average_speed_mbps'] = sum(speeds) / len(speeds)

        if total_files > 0:
            stats['success_rate'] = (total_successful / total_files) * 100

        return stats

    def display_statistics(self, days: int = 7):
        """
        Display statistics in rich tables.
        
        Args:
            days: Number of days to look back
        """
        stats = self.get_statistics(days)

        console.print(f"\n[bold cyan]Statistics (Last {days} days)[/bold cyan]\n")

        # Summary table
        summary_table = Table(show_header=True, header_style="bold magenta")
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Value", style="green")

        summary_table.add_row("Total Operations", str(stats['total_operations']))
        summary_table.add_row("Files Processed", f"{stats['total_files_processed']:,}")
        summary_table.add_row(
            "Data Transferred",
            f"{stats['total_bytes_transferred'] / (1024**3):.2f} GB"
        )
        summary_table.add_row(
            "Saved by Compression",
            f"{stats['total_bytes_saved'] / (1024**2):.2f} MB"
        )
        summary_table.add_row(
            "Average Speed",
            f"{stats['average_speed_mbps']:.2f} MB/s"
        )
        summary_table.add_row(
            "Success Rate",
            f"{stats['success_rate']:.1f}%"
        )

        console.print(summary_table)

        # Operations by type
        if stats['operations_by_type']:
            console.print("\n[bold cyan]Operations by Type[/bold cyan]\n")
            ops_table = Table(show_header=True, header_style="bold magenta")
            ops_table.add_column("Operation", style="cyan")
            ops_table.add_column("Count", style="green")

            for op, count in stats['operations_by_type'].items():
                ops_table.add_row(op.title(), str(count))

            console.print(ops_table)

        # Recent errors
        if stats['recent_errors']:
            console.print("\n[bold yellow]Recent Errors[/bold yellow]\n")
            for i, error in enumerate(stats['recent_errors'][:10], 1):
                console.print(
                    f"{i}. {error.get('file', 'Unknown')}: "
                    f"{error.get('error', 'Unknown error')}"
                  )
