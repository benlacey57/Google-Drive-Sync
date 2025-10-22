"""Command-line interface handler."""

import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

from gdrive_sync.config.loader import ConfigLoader
from gdrive_sync.config.models import ApplicationConfig
from gdrive_sync.services.auth_service import AuthenticationService
from gdrive_sync.services.sync_service import SyncService
from gdrive_sync.services.exclusion_service import ExclusionService
from gdrive_sync.services.analysis_service import AnalysisService
from gdrive_sync.infrastructure.drive.file_handler import DriveFileHandler
from gdrive_sync.infrastructure.drive.path_resolver import PathResolver
from gdrive_sync.infrastructure.logging.metrics_logger import MetricsLogger
from gdrive_sync.application.menu import InteractiveMenu

console = Console()


class CLI:
    """Command-line interface handler."""

    def __init__(self):
        """Initialize CLI."""
        self.config_loader = ConfigLoader()
        self.app_config = self.config_loader.load_app_config()
        
        # Setup paths
        self.data_dir = Path(self.app_config.data_dir)
        self.credentials_path = Path(self.app_config.credentials_path)
        self.token_path = Path(self.app_config.token_path)
        
        # Initialize services
        self.auth_service = None
        self.file_handler = None
        self.path_resolver = None
        self.exclusion_service = None
        self.metrics_logger = None
        self.sync_service = None
        self.analysis_service = None

    def run(self):
        """Run the CLI application."""
        # Parse command line arguments
        args = self._parse_args()

        # Display banner
        if not args.quiet:
            self._display_banner()

        # Initialize services
        self._initialize_services()

        # Route to appropriate handler
        if args.config:
            self._handle_config_command(args)
        elif args.analyse:
            self._handle_analyse_command(args)
        elif args.stats:
            self._handle_stats_command(args)
        else:
            # Interactive mode
            self._run_interactive_mode()

    def _parse_args(self):
        """Parse command-line arguments."""
        import argparse

        parser = argparse.ArgumentParser(
            description='Google Drive Synchronisation Tool',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Interactive mode
  %(prog)s

  # Run with configuration file
  %(prog)s --config download --name my_photos

  # Analyse Drive storage
  %(prog)s --analyse /photos

  # View statistics
  %(prog)s --stats --days 30

Configuration Files:
  Place JSON configuration files in the 'config' directory:
  - download.json, upload.json, sync.json
  - Use --config to specify which config to run
            """
        )

        parser.add_argument(
            '--config',
            type=str,
            choices=['download', 'upload', 'sync'],
            help='Run operation using configuration file'
        )

        parser.add_argument(
            '--name',
            type=str,
            default=None,
            help='Name of configuration file (without .json extension)'
        )

        parser.add_argument(
            '--analyse',
            type=str,
            metavar='PATH',
            help='Analyse Drive storage at path (e.g., /photos)'
        )

        parser.add_argument(
            '--export-analysis',
            type=str,
            metavar='FILE',
            help='Export analysis to JSON file'
        )

        parser.add_argument(
            '--stats',
            action='store_true',
            help='Display statistics from previous operations'
        )

        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Number of days for statistics (default: 7)'
        )

        parser.add_argument(
            '--list-configs',
            action='store_true',
            help='List available configuration files'
        )

        parser.add_argument(
            '--quiet',
            action='store_true',
            help='Suppress banner and non-essential output'
        )

        parser.add_argument(
            '--config-dir',
            type=str,
            default='config',
            help='Configuration directory (default: config)'
        )

        return parser.parse_args()

    def _display_banner(self):
        """Display application banner."""
        banner = """
[bold cyan]╔═══════════════════════════════════════════════════╗[/bold cyan]
[bold cyan]║   Google Drive Synchronisation Tool              ║[/bold cyan]
[bold cyan]║   Manage your Drive with ease                     ║[/bold cyan]
[bold cyan]╚═══════════════════════════════════════════════════╝[/bold cyan]
        """
        console.print(banner)

    def _initialize_services(self):
        """Initialize all required services."""
        try:
            # Authentication
            self.auth_service = AuthenticationService(
                self.credentials_path,
                self.token_path
            )
            self.auth_service.authenticate()
            service = self.auth_service.get_service()

            # Infrastructure
            self.file_handler = DriveFileHandler(service)
            self.path_resolver = PathResolver(service)

            # Exclusion service
            exclusion_file = self.data_dir / 'exclusions.conf'
            self.exclusion_service = ExclusionService(exclusion_file)

            # Metrics logger
            self.metrics_logger = MetricsLogger(self.data_dir)

            # Core services
            self.sync_service = SyncService(
                self.file_handler,
                self.path_resolver,
                self.exclusion_service,
                self.metrics_logger
            )

            self.analysis_service = AnalysisService(
                service,
                self.path_resolver
            )

        except Exception as e:
            console.print(f"[red]Failed to initialize services: {e}[/red]")
            sys.exit(1)

    def _handle_config_command(self, args):
        """Handle configuration-based commands."""
        config_name = args.name or args.config

        if args.config == 'download':
            config = self.config_loader.load_download_config(config_name)
            if not config:
                sys.exit(1)

            console.print(
                f"[cyan]Running download operation with config: {config_name}[/cyan]\n"
            )
            metrics = self.sync_service.download(config)
            self._display_metrics_summary(metrics)

        elif args.config == 'upload':
            config = self.config_loader.load_upload_config(config_name)
            if not config:
                sys.exit(1)

            console.print(
                f"[cyan]Running upload operation with config: {config_name}[/cyan]\n"
            )
            metrics = self.sync_service.upload(config)
            self._display_metrics_summary(metrics)

        elif args.config == 'sync':
            config = self.config_loader.load_sync_config(config_name)
            if not config:
                sys.exit(1)

            console.print(
                f"[cyan]Running sync operation with config: {config_name}[/cyan]\n"
            )
            metrics = self.sync_service.sync(config)
            self._display_metrics_summary(metrics)

    def _handle_analyse_command(self, args):
        """Handle analysis command."""
        path = args.analyse or '/'

        console.print(f"[cyan]Analysing Drive path: {path}[/cyan]\n")

        stats = self.analysis_service.analyse_drive(path)

        if stats:
            self.analysis_service.display_analysis(stats)

            if args.export_analysis:
                export_path = Path(args.export_analysis)
                self.analysis_service.export_analysis(stats, export_path)

    def _handle_stats_command(self, args):
        """Handle statistics command."""
        console.print(
            f"[cyan]Loading statistics for last {args.days} days...[/cyan]\n"
        )
        self.metrics_logger.display_statistics(args.days)

    def _run_interactive_mode(self):
        """Run interactive menu mode."""
        menu = InteractiveMenu(
            self.auth_service,
            self.file_handler,
            self.path_resolver,
            self.sync_service,
            self.analysis_service,
            self.exclusion_service,
            self.metrics_logger,
            self.config_loader
        )
        menu.show_main_menu()

    def _display_metrics_summary(self, metrics):
        """Display operation metrics summary."""
        from rich.table import Table

        console.print("\n" + "="*60)
        console.print("[bold green]Operation Complete![/bold green]\n")

        summary_table = Table(show_header=False, box=None)
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Value", style="green")

        summary_table.add_row("Operation", metrics.operation.title())
        summary_table.add_row("Duration", f"{metrics.duration():.2f} seconds")
        summary_table.add_row("Total Files", str(metrics.total_files))
        summary_table.add_row("Successful", str(metrics.successful_files))
        summary_table.add_row("Failed", str(metrics.failed_files))
        summary_table.add_row("Excluded", str(metrics.excluded_files))
        summary_table.add_row(
            "Data Transferred",
            f"{metrics.total_bytes_transferred / (1024**2):.2f} MB"
        )
        summary_table.add_row(
            "Average Speed",
            f"{metrics.average_speed() / (1024**2):.2f} MB/s"
        )

        if metrics.compressed_files > 0:
            summary_table.add_row("Compressed Files", str(metrics.compressed_files))
            summary_table.add_row(
                "Space Saved",
                f"{metrics.bytes_saved_compression / (1024**2):.2f} MB"
            )
            summary_table.add_row(
                "Compression Ratio",
                f"{metrics.compression_ratio():.1f}%"
            )

        console.print(summary_table)
        console.print("="*60 + "\n")

        # Show errors if any
        if metrics.errors:
            console.print("[bold yellow]Errors occurred:[/bold yellow]")
            for i, error in enumerate(metrics.errors[:5], 1):
                console.print(
                    f"  {i}. {error.get('file', 'Unknown')}: "
                    f"{error.get('error', 'Unknown error')}"
                )
            if len(metrics.errors) > 5:
                console.print(f"  ... and {len(metrics.errors) - 5} more errors")
