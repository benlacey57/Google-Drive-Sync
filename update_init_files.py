#!/usr/bin/env python3
"""
Dynamic __init__.py Generator and Updater

Scans Python files in packages, extracts public classes/functions,
and generates/updates __init__.py files with appropriate exports.

Usage:
    python update_init_files.py                 # Update all files
    python update_init_files.py --check         # Check without updating
    python update_init_files.py --dry-run       # Preview changes
    python update_init_files.py --verbose       # Detailed output
"""

import ast
import argparse
import sys
from pathlib import Path
from typing import List, Set, Dict, Tuple, Optional
from dataclasses import dataclass, field
from collections import defaultdict

# Colours for output
class Colours:
    GREEN = '\033[0;32m'
    BLUE = '\033[0;34m'
    YELLOW = '\033[1;33m'
    RED = '\033[0;31m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'  # No Colour


@dataclass
class ModuleInfo:
    """Information about a Python module."""
    name: str
    path: Path
    classes: Set[str] = field(default_factory=set)
    functions: Set[str] = field(default_factory=set)
    constants: Set[str] = field(default_factory=set)
    submodules: Set[str] = field(default_factory=set)
    docstring: Optional[str] = None


@dataclass
class PackageInfo:
    """Information about a Python package."""
    name: str
    path: Path
    modules: List[ModuleInfo] = field(default_factory=list)
    subpackages: List[str] = field(default_factory=list)
    docstring: Optional[str] = None


class PythonAnalyzer:
    """Analyzes Python files to extract exports."""

    @staticmethod
    def is_public(name: str) -> bool:
        """Check if a name is public (doesn't start with _)."""
        return not name.startswith('_')

    @staticmethod
    def extract_module_docstring(tree: ast.AST) -> Optional[str]:
        """Extract module docstring from AST."""
        if isinstance(tree, ast.Module) and tree.body:
            first = tree.body[0]
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
                if isinstance(first.value.value, str):
                    return first.value.value.strip()
        return None

    def analyze_file(self, file_path: Path) -> ModuleInfo:
        """Analyze a Python file and extract public exports."""
        try:
            content = file_path.read_text(encoding='utf-8')
            tree = ast.parse(content, filename=str(file_path))
        except SyntaxError as e:
            print(f"{Colours.RED}[ERROR]{Colours.NC} Syntax error in {file_path}: {e}")
            return ModuleInfo(name=file_path.stem, path=file_path)
        except Exception as e:
            print(f"{Colours.RED}[ERROR]{Colours.NC} Error parsing {file_path}: {e}")
            return ModuleInfo(name=file_path.stem, path=file_path)

        module_info = ModuleInfo(
            name=file_path.stem,
            path=file_path,
            docstring=self.extract_module_docstring(tree)
        )

        for node in ast.walk(tree):
            # Extract classes
            if isinstance(node, ast.ClassDef):
                if self.is_public(node.name):
                    module_info.classes.add(node.name)

            # Extract functions (top-level only)
            elif isinstance(node, ast.FunctionDef):
                if self.is_public(node.name):
                    # Check if it's a top-level function
                    for parent in ast.walk(tree):
                        if isinstance(parent, ast.Module):
                            if node in parent.body:
                                module_info.functions.add(node.name)
                                break

            # Extract constants (uppercase variables)
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        if target.id.isupper() and self.is_public(target.id):
                            module_info.constants.add(target.id)

        return module_info

    def analyze_package(self, package_path: Path) -> PackageInfo:
        """Analyze a package directory."""
        package_info = PackageInfo(
            name=package_path.name,
            path=package_path
        )

        # Check for existing __init__.py docstring
        init_file = package_path / "__init__.py"
        if init_file.exists():
            try:
                content = init_file.read_text(encoding='utf-8')
                tree = ast.parse(content)
                package_info.docstring = self.extract_module_docstring(tree)
            except:
                pass

        # Find all Python files in the package
        for py_file in sorted(package_path.glob("*.py")):
            if py_file.name == "__init__.py":
                continue
            if py_file.name.startswith("test_"):
                continue

            module_info = self.analyze_file(py_file)
            package_info.modules.append(module_info)

        # Find subpackages
        for item in sorted(package_path.iterdir()):
            if item.is_dir() and not item.name.startswith(('.', '_', 'test')):
                if (item / "__init__.py").exists() or any(item.glob("*.py")):
                    package_info.subpackages.append(item.name)

        return package_info


class InitFileGenerator:
    """Generates __init__.py file content."""

    def __init__(self, project_name: str = "gdrive_sync", version: str = "1.0.0"):
        self.project_name = project_name
        self.version = version

    def generate_main_init(self, package_info: PackageInfo) -> str:
        """Generate main package __init__.py."""
        lines = [
            f'"""Google Drive Synchronisation Tool."""\n',
            f'__version__ = "{self.version}"',
            '__author__ = "Your Name"',
            '__email__ = "your.email@example.com"',
            '',
        ]

        # Add subpackages to __all__
        if package_info.subpackages:
            lines.append('__all__ = [')
            for subpkg in sorted(package_info.subpackages):
                lines.append(f'    "{subpkg}",')
            lines.append(']')
            lines.append('')

        return '\n'.join(lines)

    def generate_package_init(self, package_info: PackageInfo) -> str:
        """Generate package __init__.py."""
        lines = []

        # Add docstring
        if package_info.docstring:
            lines.append(f'"""{package_info.docstring}"""')
        else:
            # Generate default docstring
            pkg_name = package_info.name.replace('_', ' ').title()
            lines.append(f'"""{pkg_name}.')
            lines.append('')
            lines.append('This module contains components for the Google Drive Sync Tool.')
            lines.append('"""')
        lines.append('')

        # Collect all exports
        all_exports = []
        imports = []

        # Add imports from modules
        for module in sorted(package_info.modules, key=lambda m: m.name):
            module_exports = sorted(
                module.classes | module.functions | module.constants
            )

            if module_exports:
                # Create import statement
                module_path = f"{self.project_name}.{self._get_relative_path(package_info.path)}"
                if module_path.endswith('.'):
                    module_path = module_path[:-1]

                imports.append(
                    f"from {module_path}.{module.name} import ("
                )

                for export in module_exports:
                    imports.append(f"    {export},")
                    all_exports.append(export)

                imports.append(")")
                imports.append("")

        # Add imports
        if imports:
            lines.extend(imports)

        # Add subpackages to __all__ if no other exports
        if not all_exports and package_info.subpackages:
            all_exports = sorted(package_info.subpackages)

        # Add __all__
        if all_exports:
            lines.append("__all__ = [")
            for export in sorted(set(all_exports)):
                lines.append(f'    "{export}",')
            lines.append("]")
            lines.append("")

        return '\n'.join(lines)

    def generate_test_init(self, package_info: PackageInfo) -> str:
        """Generate test package __init__.py."""
        pkg_name = package_info.name.replace('test_', '').replace('_', ' ').title()

        lines = [
            f'"""Tests for {pkg_name}."""',
            '',
        ]

        return '\n'.join(lines)

    def _get_relative_path(self, path: Path) -> str:
        """Get relative path from project root."""
        try:
            # Find project root (where main.py is)
            current = path
            while current.parent != current:
                if (current / "main.py").exists():
                    break
                current = current.parent

            rel_path = path.relative_to(current)
            return str(rel_path).replace('/', '.')
        except:
            return path.name


class InitFileUpdater:
    """Updates __init__.py files in the project."""

    def __init__(self, root_path: Path, dry_run: bool = False, verbose: bool = False):
        self.root_path = root_path
        self.dry_run = dry_run
        self.verbose = verbose
        self.analyzer = PythonAnalyzer()
        self.generator = InitFileGenerator()
        self.stats = {
            'created': 0,
            'updated': 0,
            'unchanged': 0,
            'errors': 0,
        }

    def should_skip_directory(self, path: Path) -> bool:
        """Check if directory should be skipped."""
        skip_dirs = {
            'venv', 'env', '.venv', '.env',
            '__pycache__', '.pytest_cache',
            '.git', '.tox', '.nox',
            'build', 'dist', '.eggs',
            'node_modules',
        }

        return any(part in skip_dirs for part in path.parts)

    def find_packages(self) -> List[Path]:
        """Find all Python packages in the project."""
        packages = []

        for path in self.root_path.rglob("*"):
            if not path.is_dir():
                continue

            if self.should_skip_directory(path):
                continue

            # Check if it's a package (has Python files)
            if any(path.glob("*.py")):
                packages.append(path)

        return sorted(packages)

    def update_init_file(self, package_path: Path) -> None:
        """Update or create __init__.py for a package."""
        init_file = package_path / "__init__.py"

        # Analyze package
        package_info = self.analyzer.analyze_package(package_path)

        # Generate content
        if package_path.name == self.root_path.name:
            # Main package
            content = self.generator.generate_main_init(package_info)
        elif 'test' in package_path.name or 'tests' in str(package_path):
            # Test package
            content = self.generator.generate_test_init(package_info)
        else:
            # Regular package
            content = self.generator.generate_package_init(package_info)

        # Check if needs update
        if init_file.exists():
            try:
                existing_content = init_file.read_text(encoding='utf-8')
                if existing_content.strip() == content.strip():
                    self.stats['unchanged'] += 1
                    if self.verbose:
                        print(f"{Colours.BLUE}[SKIP]{Colours.NC} {init_file} (unchanged)")
                    return
            except Exception as e:
                print(f"{Colours.RED}[ERROR]{Colours.NC} Reading {init_file}: {e}")
                self.stats['errors'] += 1
                return

        # Write file
        if self.dry_run:
            print(f"{Colours.CYAN}[DRY-RUN]{Colours.NC} Would update: {init_file}")
            if self.verbose:
                print(f"\n{'-'*60}")
                print(content)
                print(f"{'-'*60}\n")
        else:
            try:
                init_file.write_text(content, encoding='utf-8')
                if init_file.exists() and init_file.stat().st_size > 0:
                    self.stats['updated'] += 1
                    print(f"{Colours.GREEN}[UPDATE]{Colours.NC} {init_file}")
                else:
                    self.stats['created'] += 1
                    print(f"{Colours.GREEN}[CREATE]{Colours.NC} {init_file}")
            except Exception as e:
                print(f"{Colours.RED}[ERROR]{Colours.NC} Writing {init_file}: {e}")
                self.stats['errors'] += 1

    def update_all(self) -> bool:
        """Update all __init__.py files in the project."""
        print(f"Scanning for Python packages in: {self.root_path}")
        print()

        packages = self.find_packages()

        if not packages:
            print(f"{Colours.YELLOW}[WARN]{Colours.NC} No Python packages found")
            return True

        for package_path in packages:
            self.update_init_file(package_path)

        # Print summary
        print()
        print("="*60)
        print("Summary:")
        print(f"  Created:   {self.stats['created']}")
        print(f"  Updated:   {self.stats['updated']}")
        print(f"  Unchanged: {self.stats['unchanged']}")
        print(f"  Errors:    {self.stats['errors']}")
        print(f"  Total:     {sum(self.stats.values())}")
        print("="*60)

        return self.stats['errors'] == 0

    def check_only(self) -> bool:
        """Check if any __init__.py files need updating."""
        print(f"Checking __init__.py files in: {self.root_path}")
        print()

        packages = self.find_packages()
        needs_update = []

        for package_path in packages:
            init_file = package_path / "__init__.py"
            package_info = self.analyzer.analyze_package(package_path)

            # Generate expected content
            if package_path.name == self.root_path.name:
                expected_content = self.generator.generate_main_init(package_info)
            elif 'test' in package_path.name or 'tests' in str(package_path):
                expected_content = self.generator.generate_test_init(package_info)
            else:
                expected_content = self.generator.generate_package_init(package_info)

            # Check if differs
            if not init_file.exists():
                needs_update.append((init_file, "missing"))
                print(f"{Colours.RED}[MISSING]{Colours.NC} {init_file}")
            else:
                try:
                    existing_content = init_file.read_text(encoding='utf-8')
                    if existing_content.strip() != expected_content.strip():
                        needs_update.append((init_file, "outdated"))
                        print(f"{Colours.YELLOW}[OUTDATED]{Colours.NC} {init_file}")
                    else:
                        print(f"{Colours.GREEN}[OK]{Colours.NC} {init_file}")
                except Exception as e:
                    needs_update.append((init_file, "error"))
                    print(f"{Colours.RED}[ERROR]{Colours.NC} {init_file}: {e}")

        # Print summary
        print()
        print("="*60)
        if needs_update:
            print(f"{Colours.RED}Check failed:{Colours.NC} {len(needs_update)} file(s) need updating")
            for file, reason in needs_update:
                print(f"  - {file} ({reason})")
            print()
            print("Run without --check to update files")
            return False
        else:
            print(f"{Colours.GREEN}✓ All __init__.py files are up to date{Colours.NC}")
            return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Update __init__.py files dynamically",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Update all __init__.py files
  %(prog)s --check            # Check without updating
  %(prog)s --dry-run          # Preview changes
  %(prog)s --verbose          # Show detailed output
  %(prog)s --path gdrive_sync # Specify root path
        """
    )

    parser.add_argument(
        '--check',
        action='store_true',
        help='Check if files need updating (exit 1 if updates needed)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be updated without making changes'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed output'
    )
    parser.add_argument(
        '--path',
        type=Path,
        default=Path('gdrive_sync'),
        help='Root path to scan (default: gdrive_sync)'
    )

    args = parser.parse_args()

    # Validate path
    if not args.path.exists():
        print(f"{Colours.RED}[ERROR]{Colours.NC} Path not found: {args.path}")
        return 1

    if not args.path.is_dir():
        print(f"{Colours.RED}[ERROR]{Colours.NC} Not a directory: {args.path}")
        return 1

    # Create updater
    updater = InitFileUpdater(
        root_path=args.path,
        dry_run=args.dry_run,
        verbose=args.verbose
    )

    # Run
    if args.check:
        success = updater.check_only()
        return 0 if success else 1
    else:
        success = updater.update_all()
        return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
