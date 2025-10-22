"""Interactive menu interface."""

from pathlib import Path
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.tree import Tree
from rich.panel import Panel

from gdrive_sync.config.models import DownloadConfig, UploadConfig, SyncConfig
from gdrive_sync.infrastructure.storage.space_checker import StorageChecker

console = Console()


class InteractiveMenu:
    """Interactive menu system."""

    def __init__(
        self,
        auth_service,
        file_handler,
        path_resolver,
        sync_service,
        analysis_service,
        exclusion_service,
        metrics_logger,
        config_loader
    ):
        """
        Initialize interactive menu.
        
        Args:
            auth_service: Authentication service
            file_handler: File handler
            path_resolver: Path resolver
            sync_service: Sync service
            analysis_service: Analysis service
            exclusion_service: Exclusion service
            metrics_logger: Metrics logger
            config_loader: Configuration loader
        """
        self.auth_service = auth_service
        self.file_handler = file_handler
        self.path_resolver = path_resolver
        self.sync_service = sync_service
        self.analysis_service = analysis_service
        self.exclusion_service = exclusion_service
        self.metrics_logger = metrics_logger
        self.config_loader = config_loader

    def show_main_menu(self):
        """Display main menu and handle user selection."""
        while True:
            console.clear()
            console.print(Panel.fit(
                "[bold cyan]Google Drive Synchronisation Tool[/bold cyan]\n"
                "[dim]Manage your Google Drive files with ease[/dim]",
                border_style="cyan"
            ))

            console.print("\n[bold]Available Operations:[/bold]")
            console.print("  1. Download from Google Drive")
            console.print("  2. Upload to Google Drive")
            console.print("  3. Synchronise folders")
            console.print("  4. Analyse Drive storage")
            console.print("  5. Browse Drive folders")
            console.print("  6. View statistics")
            console.print("  7. Manage exclusion patterns")
            console.print("  8. Configuration management")
            console.print("  9. View logs")
            console.print("  0. Exit\n")

            choice = Prompt.ask(
                "[bold cyan]Select an option[/bold cyan]",
                choices=["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"],
                default="0"
            )

            if choice == "0":
                console.print("\n[green]Goodbye![/green]")
                break
            elif choice == "1":
                self._download_menu()
            elif choice == "2":
                self._upload_menu()
            elif choice == "3":
                self._sync_menu()
            elif choice == "4":
                self._analyse_menu()
            elif choice == "5":
                self._browse_menu()
            elif choice == "6":
                self._statistics_menu()
            elif choice == "7":
                self._exclusions_menu()
            elif choice == "8":
                self._config_management_menu()
            elif choice == "9":
                self._logs_menu()

    def _download_menu(self):
        """Download menu."""
        console.clear()
        console.print("[bold cyan]Download from Google Drive[/bold cyan]\n")

        # Select paths
        paths = self._select_drive_paths()
        if not paths:
            console.print("[yellow]No paths selected[/yellow]")
            Prompt.ask("\nPress Enter to continue")
            return

        # Get destination
        destination = Prompt.ask(
            "\n[cyan]Enter local destination path[/cyan]",
            default=str(Path.home() / "Downloads" / "GDrive")
        )

        destination_path = Path(destination)

        # Check disk space
        console.print("\n[cyan]Checking disk space...[/cyan]")
        StorageChecker.display_disk_info(destination_path)

        if not Confirm.ask("\nProceed with download?", default=True):
            return

        # Create configuration
        config = DownloadConfig(
            paths=paths,
            destination=destination,
            exclude_patterns=self.exclusion_service.get_exclusions_list()
        )

        # Advanced options
        if Confirm.ask("\nConfigure advanced options?", default=False):
            config.convert_google_docs = Confirm.ask(
                "Convert Google Docs to ODF?",
                default=True
            )
            config.use_compression = Confirm.ask(
                "Use compression?",
                default=True
            )

            max_size_mb = Prompt.ask(
                "Maximum file size in MB (0 for no limit)",
                default="0"
            )
            config.max_file_size_mb = int(max_size_mb)

        # Save config option
        if Confirm.ask("\nSave this configuration for future use?", default=False):
            name = Prompt.ask("Configuration name", default="download")
            self.config_loader.save_download_config(config, name)

        # Execute download
        console.print(f"\n[green]Starting download...[/green]\n")
        try:
            metrics = self.sync_service.download(config)
            self._display_operation_summary(metrics)
        except Exception as e:
            console.print(f"[red]Error during download: {e}[/red]")

        Prompt.ask("\nPress Enter to continue")

    def _upload_menu(self):
        """Upload menu."""
        console.clear()
        console.print("[bold cyan]Upload to Google Drive[/bold cyan]\n")

        # Get source
        source = Prompt.ask("[cyan]Enter local folder path to upload[/cyan]")
        source_path = Path(source)

        if not source_path.exists() or not source_path.is_dir():
            console.print("[red]Invalid folder path[/red]")
            Prompt.ask("\nPress Enter to continue")
            return

        # Select destination
        destination_path = self._input_drive_path("Enter destination path in Drive")
        if not destination_path:
            return

        # Create configuration
        config = UploadConfig(
            source=source,
            destination_path=destination_path,
            exclude_patterns=self.exclusion_service.get_exclusions_list()
        )

        # Advanced options
        if Confirm.ask("\nConfigure advanced options?", default=False):
            config.use_compression = Confirm.ask(
                "Use compression during transfer?",
                default=True
            )

            max_size_mb = Prompt.ask(
                "Maximum file size in MB (0 for no limit)",
                default="0"
            )
            config.max_file_size_mb = int(max_size_mb)

        # Save config option
        if Confirm.ask("\nSave this configuration for future use?", default=False):
            name = Prompt.ask("Configuration name", default="upload")
            self.config_loader.save_upload_config(config, name)

        # Execute upload
        console.print(f"\n[green]Starting upload...[/green]\n")
        try:
            metrics = self.sync_service.upload(config)
            self._display_operation_summary(metrics)
        except Exception as e:
            console.print(f"[red]Error during upload: {e}[/red]")

        Prompt.ask("\nPress Enter to continue")

    def _sync_menu(self):
        """Synchronisation menu."""
        console.clear()
        console.print("[bold cyan]Synchronise Folders[/bold cyan]\n")

        # Select paths
        paths = self._select_drive_paths()
        if not paths:
            console.print("[yellow]No paths selected[/yellow]")
            Prompt.ask("\nPress Enter to continue")
            return

        # Get destination
        destination = Prompt.ask(
            "\n[cyan]Enter local folder path[/cyan]",
            default=str(Path.home() / "Documents" / "GDrive")
        )

        # Create configuration
        config = SyncConfig(
            paths=paths,
            destination=destination,
            exclude_patterns=self.exclusion_service.get_exclusions_list()
        )

        # Sync options
        config.bidirectional = Confirm.ask(
            "\nUse bidirectional sync? (uploads local changes too)",
            default=True
        )

        if Confirm.ask("\nConfigure advanced options?", default=False):
            config.delete_missing = Confirm.ask(
                "[yellow]Delete local files not in Drive?[/yellow]",
                default=False
            )

            if config.bidirectional:
                config.delete_missing_remote = Confirm.ask(
                    "[yellow]Delete Drive files not local?[/yellow]",
                    default=False
                )

            config.convert_google_docs = Confirm.ask(
                "Convert Google Docs to ODF?",
                default=True
            )

            max_size_mb = Prompt.ask(
                "Maximum file size in MB (0 for no limit)",
                default="0"
            )
            config.max_file_size_mb = int(max_size_mb)

        # Save config option
        if Confirm.ask("\nSave this configuration for future use?", default=False):
            name = Prompt.ask("Configuration name", default="sync")
            self.config_loader.save_sync_config(config, name)

        # Execute sync
        console.print(f"\n[green]Starting synchronisation...[/green]\n")
        try:
            metrics = self.sync_service.sync(config)
            self._display_operation_summary(metrics)
        except Exception as e:
            console.print(f"[red]Error during sync: {e}[/red]")

        Prompt.ask("\nPress Enter to continue")

    def _analyse_menu(self):
        """Analysis menu."""
        console.clear()
        console.print("[bold cyan]Analyse Drive Storage[/bold cyan]\n")

        path = self._input_drive_path("Enter path to analyse", default="/")
        if not path:
            return

        console.print(f"\n[cyan]Analysing {path}...[/cyan]\n")

        try:
            stats = self.analysis_service.analyse_drive(path)

            if stats:
                self.analysis_service.display_analysis(stats)

                if Confirm.ask("\nExport analysis to JSON?", default=False):
                    export_path = Prompt.ask(
                        "Export file path",
                        default=f"analysis_{path.replace('/', '_')}.json"
                    )
                    self.analysis_service.export_analysis(stats, Path(export_path))

        except Exception as e:
            console.print(f"[red]Error during analysis: {e}[/red]")

        Prompt.ask("\nPress Enter to continue")

    def _browse_menu(self):
        """Browse Drive folders."""
        console.clear()
        console.print("[bold cyan]Browse Google Drive[/bold cyan]\n")

        current_path = "/"

        while True:
            console.clear()
            console.print(f"[bold cyan]Current Path: {current_path}[/bold cyan]\n")

            folders = self.path_resolver.list_folders(current_path)

            if folders:
                tree = Tree(f"[bold cyan]📁 {current_path}[/bold cyan]")
                for i, (name, path) in enumerate(folders, 1):
                    tree.add(f"[green]{i}.[/green] 📁 {name}")

                console.print(tree)
                console.print()

                console.print("[dim]Options: [number] to enter, 'b' to go back, 'q' to quit[/dim]")
                choice = Prompt.ask("\nSelect")

                if choice.lower() == 'q':
                    break
                elif choice.lower() == 'b':
                    if current_path != '/':
                        current_path = str(Path(current_path).parent)
                        if current_path == '.':
                            current_path = '/'
                else:
                    try:
                        idx = int(choice) - 1
                        if 0 <= idx < len(folders):
                            current_path = folders[idx][1]
                    except ValueError:
                        pass
            else:
                console.print("[yellow]No folders found[/yellow]")
                Prompt.ask("\nPress Enter to continue")
                break

    def _statistics_menu(self):
        """Statistics menu."""
        console.clear()
        days = Prompt.ask(
            "[cyan]Show statistics for how many days?[/cyan]",
            default="7"
        )

        try:
            days = int(days)
            self.metrics_logger.display_statistics(days)
        except ValueError:
            console.print("[red]Invalid number of days[/red]")

        Prompt.ask("\nPress Enter to continue")

    def _exclusions_menu(self):
        """Exclusion patterns menu."""
        while True:
            console.clear()
            console.print("[bold cyan]Exclusion Pattern Management[/bold cyan]\n")

            exclusions = self.exclusion_service.get_exclusions_list()

            if exclusions:
                table = Table(show_header=True, header_style="bold magenta")
                table.add_column("#", style="cyan", width=4)
                table.add_column("Pattern", style="green")

                for i, pattern in enumerate(exclusions, 1):
                    table.add_row(str(i), pattern)

                console.print(table)
            else:
                console.print("[yellow]No exclusion patterns configured[/yellow]")

            console.print("\n[bold]Options:[/bold]")
            console.print("  1. Add exclusion pattern")
            console.print("  2. Remove exclusion pattern")
            console.print("  3. Reset to defaults")
            console.print("  0. Back to main menu\n")

            choice = Prompt.ask(
                "[cyan]Select an option[/cyan]",
                choices=["0", "1", "2", "3"],
                default="0"
            )

            if choice == "0":
                break
            elif choice == "1":
                pattern = Prompt.ask(
                    "[cyan]Enter exclusion pattern (e.g., *.tmp, node_modules)[/cyan]"
                )
                self.exclusion_service.add_exclusion(pattern)
                self.exclusion_service.save_exclusions()
                console.print(f"[green]Added pattern: {pattern}[/green]")
                Prompt.ask("\nPress Enter to continue")
            elif choice == "2":
                if not exclusions:
                    console.print("[yellow]No patterns to remove[/yellow]")
                    Prompt.ask("\nPress Enter to continue")
                    continue
                pattern = Prompt.ask(
                    "[cyan]Enter pattern to remove[/cyan]",
                    choices=exclusions
                )
                self.exclusion_service.remove_exclusion(pattern)
                self.exclusion_service.save_exclusions()
                console.print(f"[green]Removed pattern: {pattern}[/green]")
                Prompt.ask("\nPress Enter to continue")
            elif choice == "3":
                if Confirm.ask("[yellow]Reset to default patterns?[/yellow]"):
                    self.exclusion_service.reset_to_defaults()
                    self.exclusion_service.save_exclusions()
                    console.print("[green]Reset to defaults[/green]")
                Prompt.ask("\nPress Enter to continue")

    def _config_management_menu(self):
        """Configuration management menu."""
        console.clear()
        console.print("[bold cyan]Configuration Management[/bold cyan]\n")

        configs = self.config_loader.list_configs()

        # Display available configs
        console.print("[bold]Available Configurations:[/bold]\n")

        for config_type, names in configs.items():
            if names:
                console.print(f"[cyan]{config_type.title()}:[/cyan]")
                for name in names:
                    console.print(f"  • {name}")
                console.print()

        console.print("\n[bold]Options:[/bold]")
        console.print("  1. Run existing configuration")
        console.print("  2. Create new configuration")
        console.print("  0. Back to main menu\n")

        choice = Prompt.ask(
            "[cyan]Select an option[/cyan]",
            choices=["0", "1", "2"],
            default="0"
        )

        if choice == "1":
            config_type = Prompt.ask(
                "Configuration type",
                choices=["download", "upload", "sync"]
            )

            if not configs[config_type]:
                console.print(f"[yellow]No {config_type} configurations found[/yellow]")
                Prompt.ask("\nPress Enter to continue")
                return

            name = Prompt.ask(
                "Configuration name",
                choices=configs[config_type]
            )

            # Load and execute
            console.print(f"\n[green]Loading {config_type} configuration: {name}[/green]\n")

            if config_type == "download":
                config = self.config_loader.load_download_config(name)
                if config:
                    metrics = self.sync_service.download(config)
                    self._display_operation_summary(metrics)
            elif config_type == "upload":
                config = self.config_loader.load_upload_config(name)
                if config:
                    metrics = self.sync_service.upload(config)
                    self._display_operation_summary(metrics)
            elif config_type == "sync":
                config = self.config_loader.load_sync_config(name)
                if config:
                    metrics = self.sync_service.sync(config)
                    self._display_operation_summary(metrics)

            Prompt.ask("\nPress Enter to continue")

    def _logs_menu(self):
        """View logs menu."""
        console.clear()
        console.print("[bold cyan]Recent Log Files[/bold cyan]\n")

        log_files = sorted(
            self.metrics_logger.logs_path.glob('*.log'),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )[:10]

        if log_files:
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("File", style="cyan")
            table.add_column("Modified", style="green")
            table.add_column("Size", style="yellow")

            for log_file in log_files:
                from datetime import datetime
                mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                size = log_file.stat().st_size

                table.add_row(
                    log_file.name,
                    mtime.strftime("%Y-%m-%d %H:%M:%S"),
                    f"{size:,} bytes"
                )

            console.print(table)
        else:
            console.print("[yellow]No log files found[/yellow]")

        Prompt.ask("\nPress Enter to continue")

    def _select_drive_paths(self) -> list[str]:
        """
        Select Drive paths interactively.
        
        Returns:
            List of selected paths
        """
        console.print("[cyan]Enter Drive paths (one per line, empty line to finish):[/cyan]")
        console.print("[dim]Examples: /photos, /documents/2024, /[/dim]\n")

        paths = []
        while True:
            path = Prompt.ask(
                f"Path {len(paths) + 1} (or press Enter to finish)",
                default=""
            )

            if not path:
                break

            # Normalize path
            if not path.startswith('/'):
                path = '/' + path

            paths.append(path)

        return paths

    def _input_drive_path(self, prompt: str, default: str = "/") -> str:
        """
        Input a single Drive path.
        
        Args:
            prompt: Prompt message
            default: Default value
            
        Returns:
            Entered path
        """
        path = Prompt.ask(f"[cyan]{prompt}[/cyan]", default=default)

        # Normalize path
        if not path.startswith('/'):
            path = '/' + path

        return path

    def _display_operation_summary(self, metrics):
        """Display operation summary."""
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

        console.print(summary_table)
        console.print("="*60 + "\n")
