#!/bin/bash

# Script to create __init__.py files throughout the project
# This ensures all Python packages are properly recognized

set -e

# Colours
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Counters
CREATED=0
EXISTED=0
UPDATED=0

log_create() {
    echo -e "${GREEN}[CREATE]${NC} $1"
    ((CREATED++))
}

log_exist() {
    echo -e "${YELLOW}[EXISTS]${NC} $1"
    ((EXISTED++))
}

log_update() {
    echo -e "${BLUE}[UPDATE]${NC} $1"
    ((UPDATED++))
}

echo "Creating __init__.py files..."
echo

# Function to create __init__.py with content
create_init() {
    local dir=$1
    local content=$2
    local file="$dir/__init__.py"
    
    if [ ! -f "$file" ]; then
        echo "$content" > "$file"
        log_create "$file"
    else
        # Check if file is empty or just whitespace
        if [ ! -s "$file" ] || ! grep -q '[^[:space:]]' "$file"; then
            echo "$content" > "$file"
            log_update "$file (was empty)"
        else
            log_exist "$file"
        fi
    fi
}

# 1. Main package
create_init "gdrive_sync" '"""Google Drive Synchronisation Tool."""

__version__ = "1.0.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

# Package metadata
__all__ = [
    "config",
    "domain",
    "services",
    "infrastructure",
    "application",
    "utils",
]
'

# 2. Config module
create_init "gdrive_sync/config" '"""Configuration management.

This module handles loading and saving configuration files
for download, upload, and sync operations.
"""

from gdrive_sync.config.loader import ConfigLoader
from gdrive_sync.config.models import (
    ApplicationConfig,
    DownloadConfig,
    UploadConfig,
    SyncConfig,
)

__all__ = [
    "ConfigLoader",
    "ApplicationConfig",
    "DownloadConfig",
    "UploadConfig",
    "SyncConfig",
]
'

# 3. Domain module
create_init "gdrive_sync/domain" '"""Domain models and business logic.

Contains core business entities and enumerations.
"""

from gdrive_sync.domain.models import (
    PerformanceMetrics,
    SyncState,
    DriveFileInfo,
)
from gdrive_sync.domain.enums import FileCategory

__all__ = [
    "PerformanceMetrics",
    "SyncState",
    "DriveFileInfo",
    "FileCategory",
]
'

# 4. Services module
create_init "gdrive_sync/services" '"""Business logic services.

Contains services that implement core business operations
like authentication, synchronisation, and analysis.
"""

from gdrive_sync.services.auth_service import AuthenticationService
from gdrive_sync.services.exclusion_service import ExclusionService
from gdrive_sync.services.analysis_service import AnalysisService
from gdrive_sync.services.sync_service import SyncService

__all__ = [
    "AuthenticationService",
    "ExclusionService",
    "AnalysisService",
    "SyncService",
]
'

# 5. Infrastructure module
create_init "gdrive_sync/infrastructure" '"""Infrastructure components.

Contains implementations for external integrations like
Google Drive API, file storage, and logging.
"""

__all__ = [
    "drive",
    "storage",
    "logging",
]
'

# 6. Infrastructure - Drive
create_init "gdrive_sync/infrastructure/drive" '"""Google Drive infrastructure.

Handles all interactions with Google Drive API including
file operations and path resolution.
"""

from gdrive_sync.infrastructure.drive.file_handler import DriveFileHandler
from gdrive_sync.infrastructure.drive.path_resolver import PathResolver

__all__ = [
    "DriveFileHandler",
    "PathResolver",
]
'

# 7. Infrastructure - Storage
create_init "gdrive_sync/infrastructure/storage" '"""Storage infrastructure.

Handles local file operations including compression,
metadata management, and space checking.
"""

from gdrive_sync.infrastructure.storage.compression import CompressionHandler
from gdrive_sync.infrastructure.storage.metadata import FileMetadata
from gdrive_sync.infrastructure.storage.space_checker import StorageChecker

__all__ = [
    "CompressionHandler",
    "FileMetadata",
    "StorageChecker",
]
'

# 8. Infrastructure - Logging
create_init "gdrive_sync/infrastructure/logging" '"""Logging infrastructure.

Manages application logging and metrics collection.
"""

from gdrive_sync.infrastructure.logging.metrics_logger import MetricsLogger

__all__ = [
    "MetricsLogger",
]
'

# 9. Application module
create_init "gdrive_sync/application" '"""Application layer.

Contains CLI and user interface components.
"""

from gdrive_sync.application.cli import CLI
from gdrive_sync.application.menu import InteractiveMenu

__all__ = [
    "CLI",
    "InteractiveMenu",
]
'

# 10. Utils module
create_init "gdrive_sync/utils" '"""Utility functions and constants.

Contains helper functions and application constants.
"""

from gdrive_sync.utils.constants import (
    SCOPES,
    EXPORT_FORMATS,
    COMPRESSIBLE_EXTENSIONS,
    COMPRESSION_THRESHOLD,
    DEFAULT_EXCLUSIONS,
)

__all__ = [
    "SCOPES",
    "EXPORT_FORMATS",
    "COMPRESSIBLE_EXTENSIONS",
    "COMPRESSION_THRESHOLD",
    "DEFAULT_EXCLUSIONS",
]
'

# 11. Tests module (main)
create_init "gdrive_sync/tests" '"""Test suite for Google Drive Sync Tool.

Contains unit tests, integration tests, and test fixtures.
Run tests with: pytest gdrive_sync/tests/
"""

# Pytest will automatically discover tests in this package
'

# 12. Test subdirectories
create_init "gdrive_sync/tests/test_domain" '"""Tests for domain models and enums."""
'

create_init "gdrive_sync/tests/test_config" '"""Tests for configuration management."""
'

create_init "gdrive_sync/tests/test_infrastructure" '"""Tests for infrastructure components."""
'

create_init "gdrive_sync/tests/test_infrastructure/test_drive" '"""Tests for Google Drive infrastructure."""
'

create_init "gdrive_sync/tests/test_infrastructure/test_storage" '"""Tests for storage infrastructure."""
'

create_init "gdrive_sync/tests/test_infrastructure/test_logging" '"""Tests for logging infrastructure."""
'

create_init "gdrive_sync/tests/test_services" '"""Tests for business services."""
'

create_init "gdrive_sync/tests/test_application" '"""Tests for application layer."""
'

create_init "gdrive_sync/tests/test_integration" '"""Integration tests for end-to-end workflows."""
'

# Summary
echo
echo "═══════════════════════════════════════════════"
echo "Summary:"
echo "  Created: $CREATED"
echo "  Updated: $UPDATED"
echo "  Existed: $EXISTED"
echo "  Total:   $((CREATED + UPDATED + EXISTED))"
echo "═══════════════════════════════════════════════"
echo
echo "✓ All __init__.py files are in place!"
