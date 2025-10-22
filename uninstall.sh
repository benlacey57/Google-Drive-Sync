#!/bin/bash

# Google Drive Sync Tool - Uninstallation Script
# This script removes the application and optionally cleans up data

set -e

# Colours
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "\n${BLUE}==>${NC} ${1}"
}

# Banner
cat << "EOF"
╔═══════════════════════════════════════════════════╗
║   Google Drive Sync Tool - Uninstallation        ║
╚═══════════════════════════════════════════════════╝

EOF

log_warn "This script will remove Google Drive Sync Tool"
echo
read -p "Are you sure you want to continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log_info "Uninstallation cancelled"
    exit 0
fi

# Check what's installed
FOUND_LOCAL=false
FOUND_DOCKER=false

if [ -d "venv" ]; then
    FOUND_LOCAL=true
    log_info "Found local installation"
fi

if command -v docker &> /dev/null; then
    if docker images | grep -q "gdrive-sync"; then
        FOUND_DOCKER=true
        log_info "Found Docker installation"
    fi
fi

if [ "$FOUND_LOCAL" = false ] && [ "$FOUND_DOCKER" = false ]; then
    log_warn "No installation found"
    exit 0
fi

# Uninstall local
if [ "$FOUND_LOCAL" = true ]; then
    log_step "Removing local installation..."
    
    # Remove virtual environment
    if [ -d "venv" ]; then
        rm -rf venv
        log_info "Removed virtual environment"
    fi
    
    # Remove run script
    if [ -f "run_local.sh" ]; then
        rm -f run_local.sh
        log_info "Removed run_local.sh"
    fi
fi

# Uninstall Docker
if [ "$FOUND_DOCKER" = true ]; then
    log_step "Removing Docker installation..."
    
    # Stop containers
    log_info "Stopping containers..."
    docker-compose -f docker/docker-compose.yml down 2>/dev/null || true
    
    # Ask about volumes
    echo
    read -p "Remove Docker volumes? This will delete all data! (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_warn "Removing volumes..."
        docker-compose -f docker/docker-compose.yml down -v 2>/dev/null || true
        
        # Remove individual volumes if they exist
        docker volume rm gdrive-data 2>/dev/null || true
        docker volume rm gdrive-token 2>/dev/null || true
        docker volume rm gdrive-downloads 2>/dev/null || true
        
        log_info "Volumes removed"
    else
        log_info "Volumes preserved"
    fi
    
    # Remove images
    echo
    read -p "Remove Docker images? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "Removing images..."
        docker rmi gdrive-sync:latest 2>/dev/null || true
        docker rmi gdrive-sync:dev 2>/dev/null || true
        log_info "Images removed"
    fi
    
    # Remove network
    docker network rm gdrive-network 2>/dev/null || true
    
    # Remove run script
    if [ -f "run_docker.sh" ]; then
        rm -f run_docker.sh
        log_info "Removed run_docker.sh"
    fi
fi

# Ask about configuration
log_step "Cleaning up configuration..."
echo
read -p "Remove configuration files? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ -d "config" ]; then
        rm -rf config
        log_info "Removed config directory"
    fi
fi

# Ask about data
echo
read -p "Remove data directory (logs, metrics, state)? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ -d "data" ]; then
        rm -rf data
        log_info "Removed data directory"
    fi
fi

# Ask about downloads
echo
read -p "Remove downloads directory? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ -d "downloads" ]; then
        rm -rf downloads
        log_info "Removed downloads directory"
    fi
fi

# Ask about credentials
echo
log_warn "Credentials handling"
read -p "Remove credentials.json? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ -f "credentials.json" ]; then
        rm -f credentials.json
        log_info "Removed credentials.json"
    fi
fi

echo
read -p "Remove token.json? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ -f "token.json" ]; then
        rm -f token.json
        log_info "Removed token.json"
    fi
fi

# Clean up build artifacts
log_step "Cleaning up build artifacts..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true
rm -rf .pytest_cache 2>/dev/null || true
rm -rf htmlcov 2>/dev/null || true
rm -rf .coverage 2>/dev/null || true
rm -rf dist 2>/dev/null || true
rm -rf build 2>/dev/null || true
log_info "Build artifacts cleaned"

# Revoke Google access
echo
echo "═══════════════════════════════════════════════════"
echo "IMPORTANT: Revoke Google Drive Access"
echo
echo "To complete uninstallation, revoke API access:"
echo "1. Visit: https://myaccount.google.com/permissions"
echo "2. Find 'Google Drive Sync Tool' or your app name"
echo "3. Click 'Remove Access'"
echo "═══════════════════════════════════════════════════"
echo

# Summary
log_step "Uninstallation complete!"
echo
log_info "The application has been removed"
echo
echo "The following were preserved (if they exist):"
echo "  - Source code (gdrive_sync/)"
echo "  - Docker configuration (docker/)"
echo "  - Documentation files"
echo
echo "To completely remove everything:"
echo "  rm -rf $(pwd)"
echo
log_info "Thank you for using Google Drive Sync Tool!"
