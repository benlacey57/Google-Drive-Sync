#!/bin/bash

# Google Drive Sync Tool - Docker Runner Script
# Quick script to run the application using Docker

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

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    log_error "Docker is not installed"
    log_error "Please install Docker from: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if docker-compose is available
COMPOSE_CMD=""
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
else
    log_error "Docker Compose is not installed"
    log_error "Please install Docker Compose"
    exit 1
fi

# Check if credentials.json exists
if [ ! -f "credentials.json" ]; then
    log_error "credentials.json not found!"
    log_error "Please download OAuth 2.0 credentials from Google Cloud Console"
    log_error "and save as credentials.json in the project root"
    exit 1
fi

# Check if image exists
if ! docker images | grep -q "gdrive-sync"; then
    log_warn "Docker image not found. Building now..."
    $COMPOSE_CMD -f docker/docker-compose.yml build
fi

# Parse arguments for special cases
SHOW_HELP=false
RUN_TESTS=false
START_CRON=false
INTERACTIVE=false

for arg in "$@"; do
    case $arg in
        -h|--help)
            SHOW_HELP=true
            ;;
        --test|--tests)
            RUN_TESTS=true
            ;;
        --cron)
            START_CRON=true
            ;;
        --dev|--bash|--shell)
            INTERACTIVE=true
            ;;
    esac
done

# Show help
if [ "$SHOW_HELP" = true ]; then
    cat << EOF
Google Drive Sync Tool - Docker Runner

Usage: ./run_docker.sh [options] [arguments]

Options:
  -h, --help          Show this help message
  --test, --tests     Run test suite
  --cron              Start cron service for scheduled operations
  --dev, --bash       Start interactive development shell
  --shell             

Examples:
  # Interactive mode (default)
  ./run_docker.sh

  # Run with configuration
  ./run_docker.sh --config download --name photos

  # Run tests
  ./run_docker.sh --test

  # Start cron service
  ./run_docker.sh --cron

  # Development shell
  ./run_docker.sh --dev

  # Analyse storage
  ./run_docker.sh --analyse /photos

  # View statistics
  ./run_docker.sh --stats --days 30

Docker Compose Commands:
  # View logs
  docker-compose -f docker/docker-compose.yml logs -f

  # Stop services
  docker-compose -f docker/docker-compose.yml down

  # Rebuild image
  docker-compose -f docker/docker-compose.yml build

  # Remove volumes
  docker-compose -f docker/docker-compose.yml down -v

For more information, see: docker/README.md
EOF
    exit 0
fi

# Run tests
if [ "$RUN_TESTS" = true ]; then
    log_info "Running tests..."
    $COMPOSE_CMD -f docker/docker-compose.yml run --rm gdrive-sync \
        pytest gdrive_sync/tests/ -v
    exit 0
fi

# Start cron service
if [ "$START_CRON" = true ]; then
    log_info "Starting cron service..."
    log_info "Press Ctrl+C to stop"
    $COMPOSE_CMD -f docker/docker-compose.yml --profile cron up gdrive-cron
    exit 0
fi

# Interactive development shell
if [ "$INTERACTIVE" = true ]; then
    log_info "Starting interactive shell..."
    $COMPOSE_CMD -f docker/docker-compose.yml --profile dev run --rm gdrive-dev bash
    exit 0
fi

# Default: run with arguments
log_info "Starting Google Drive Sync Tool..."

if [ $# -eq 0 ]; then
    # No arguments - run interactively
    $COMPOSE_CMD -f docker/docker-compose.yml run --rm gdrive-sync
else
    # Pass all arguments to the container
    $COMPOSE_CMD -f docker/docker-compose.yml run --rm gdrive-sync python main.py "$@"
fi
