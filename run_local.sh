#!/bin/bash

# Google Drive Sync Tool - Local Runner Script
# Quick script to run the application using local Python virtual environment

set -e

# Colours
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    log_error "Virtual environment not found"
    log_error "Please run ./install.sh first"
    exit 1
fi

# Check if credentials.json exists
if [ ! -f "credentials.json" ]; then
    log_error "credentials.json not found!"
    log_error "Please download OAuth 2.0 credentials from Google Cloud Console"
    log_error "and save as credentials.json in the project root"
    exit 1
fi

# Parse arguments for special cases
SHOW_HELP=false
RUN_TESTS=false

for arg in "$@"; do
    case $arg in
        -h|--help)
            SHOW_HELP=true
            ;;
        --test|--tests)
            RUN_TESTS=true
            ;;
    esac
done

# Show help
if [ "$SHOW_HELP" = true ]; then
    cat << EOF
Google Drive Sync Tool - Local Runner

Usage: ./run_local.sh [options] [arguments]

Options:
  -h, --help          Show this help message
  --test, --tests     Run test suite

Examples:
  # Interactive mode (default)
  ./run_local.sh

  # Run with configuration
  ./run_local.sh --config download --name photos

  # Run tests
  ./run_local.sh --test

  # Analyse storage
  ./run_local.sh --analyse /photos

  # View statistics
  ./run_local.sh --stats --days 30

Manual Activation:
  # Activate virtual environment
  source venv/bin/activate

  # Run application
  python main.py

  # Deactivate when done
  deactivate

For more information, see: README.md
EOF
    exit 0
fi

# Activate virtual environment
log_info "Activating virtual environment..."
source venv/bin/activate

# Run tests
if [ "$RUN_TESTS" = true ]; then
    log_info "Running tests..."
    pytest gdrive_sync/tests/ -v
    EXIT_CODE=$?
    deactivate
    exit $EXIT_CODE
fi

# Run the application
log_info "Starting Google Drive Sync Tool..."
python main.py "$@"
EXIT_CODE=$?

# Deactivate virtual environment
deactivate

exit $EXIT_CODE
