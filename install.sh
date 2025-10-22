#!/bin/bash

# Google Drive Sync Tool - Installation Script
# This script sets up the application for first use

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
║   Google Drive Sync Tool - Installation          ║
║   Professional Drive Management                   ║
╚═══════════════════════════════════════════════════╝

EOF

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
    log_warn "Running as root is not recommended"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Detect OS
log_step "Detecting operating system..."
OS="unknown"
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
    log_info "Detected: $PRETTY_NAME"
elif [ "$(uname)" = "Darwin" ]; then
    OS="macos"
    log_info "Detected: macOS"
else
    log_warn "Could not detect OS"
fi

# Check Python version
log_step "Checking Python version..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    log_info "Found Python $PYTHON_VERSION"
    
    # Check if version is >= 3.9
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    
    if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 9 ]); then
        log_error "Python 3.9 or higher is required"
        log_error "Please upgrade Python and try again"
        exit 1
    fi
else
    log_error "Python 3 is not installed"
    log_error "Please install Python 3.9+ and try again"
    exit 1
fi

# Check pip
log_step "Checking pip..."
if command -v pip3 &> /dev/null; then
    log_info "Found pip3"
else
    log_error "pip3 is not installed"
    log_error "Please install pip3 and try again"
    exit 1
fi

# Installation type
log_step "Select installation type:"
echo "1) Local installation (venv)"
echo "2) Docker installation"
echo "3) Both (recommended)"
read -p "Choice [3]: " INSTALL_TYPE
INSTALL_TYPE=${INSTALL_TYPE:-3}

# Create directories
log_step "Creating directories..."
mkdir -p config
mkdir -p data
mkdir -p downloads
log_info "Directories created"

# Copy example configurations
log_step "Setting up example configurations..."
if [ -d "config_examples" ]; then
    for example in config_examples/*.example; do
        if [ -f "$example" ]; then
            basename=$(basename "$example" .example)
            if [ ! -f "config/$basename" ]; then
                cp "$example" "config/$basename"
                log_info "Created config/$basename (from example)"
            else
                log_warn "config/$basename already exists, skipping"
            fi
        fi
    done
fi

# Copy .gdriveignore
if [ -f ".gdriveignore" ] && [ ! -f "data/exclusions.conf" ]; then
    cp .gdriveignore data/exclusions.conf
    log_info "Created exclusions configuration"
fi

# Local installation
if [ "$INSTALL_TYPE" = "1" ] || [ "$INSTALL_TYPE" = "3" ]; then
    log_step "Setting up Python virtual environment..."
    
    # Create venv
    python3 -m venv venv
    log_info "Virtual environment created"
    
    # Activate venv
    source venv/bin/activate
    
    # Upgrade pip
    log_step "Upgrading pip..."
    pip install --upgrade pip
    
    # Install dependencies
    log_step "Installing dependencies..."
    pip install -r requirements.txt
    log_info "Dependencies installed"
    
    # Install dev dependencies (optional)
    read -p "Install development dependencies? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        pip install -r requirements-dev.txt
        log_info "Development dependencies installed"
    fi
    
    # Make main.py executable
    chmod +x main.py
    log_info "Made main.py executable"
    
    deactivate
fi

# Docker installation
if [ "$INSTALL_TYPE" = "2" ] || [ "$INSTALL_TYPE" = "3" ]; then
    log_step "Checking Docker..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        log_info "Please install Docker from: https://docs.docker.com/get-docker/"
        
        if [ "$INSTALL_TYPE" = "3" ]; then
            log_warn "Continuing with local installation only"
        else
            exit 1
        fi
    else
        DOCKER_VERSION=$(docker --version)
        log_info "Found $DOCKER_VERSION"
        
        if ! command -v docker-compose &> /dev/null; then
            log_warn "docker-compose not found, checking for Docker Compose plugin..."
            if docker compose version &> /dev/null; then
                log_info "Found Docker Compose plugin"
            else
                log_error "Docker Compose is not installed"
                exit 1
            fi
        fi
        
        # Make Docker files executable
        log_step "Setting up Docker files..."
        chmod +x docker/entrypoint.sh
        chmod +x docker/healthcheck.sh
        log_info "Docker files configured"
        
        # Build Docker image (optional)
        read -p "Build Docker image now? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            log_step "Building Docker image..."
            docker-compose -f docker/docker-compose.yml build
            log_info "Docker image built successfully"
        fi
    fi
fi

# Credentials setup
log_step "Setting up Google credentials..."
if [ ! -f "credentials.json" ]; then
    log_warn "credentials.json not found"
    echo
    echo "To complete setup, you need to:"
    echo "1. Go to https://console.cloud.google.com/"
    echo "2. Create a new project or select existing"
    echo "3. Enable Google Drive API"
    echo "4. Create OAuth 2.0 credentials (Desktop app)"
    echo "5. Download credentials.json to this directory"
    echo
    read -p "Do you have credentials.json ready? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        read -p "Enter path to credentials.json: " CREDS_PATH
        if [ -f "$CREDS_PATH" ]; then
            cp "$CREDS_PATH" credentials.json
            chmod 600 credentials.json
            log_info "Credentials copied"
        else
            log_warn "File not found: $CREDS_PATH"
            log_warn "Please copy credentials.json manually"
        fi
    fi
else
    log_info "credentials.json found"
    chmod 600 credentials.json
fi

# Create run scripts
log_step "Creating convenience scripts..."

# Local run script
cat > run_local.sh << 'EOF'
#!/bin/bash
# Quick run script for local installation

if [ ! -d "venv" ]; then
    echo "Error: Virtual environment not found"
    echo "Please run ./install.sh first"
    exit 1
fi

source venv/bin/activate
python main.py "$@"
deactivate
EOF
chmod +x run_local.sh
log_info "Created run_local.sh"

# Docker run script
cat > run_docker.sh << 'EOF'
#!/bin/bash
# Quick run script for Docker

docker-compose -f docker/docker-compose.yml run --rm gdrive-sync "$@"
EOF
chmod +x run_docker.sh
log_info "Created run_docker.sh"

# Create .env file for docker-compose
if [ ! -f "docker/.env" ]; then
    cat > docker/.env << EOF
# Google Drive Sync Environment Variables
TZ=Europe/London
GDRIVE_DATA_DIR=/data
GDRIVE_CONFIG_DIR=/config
GDRIVE_DOWNLOAD_DIR=/downloads
EOF
    log_info "Created docker/.env"
fi

# Summary
log_step "Installation complete!"
echo
echo "═══════════════════════════════════════════════════"
echo "Next steps:"
echo
if [ "$INSTALL_TYPE" = "1" ] || [ "$INSTALL_TYPE" = "3" ]; then
    echo "LOCAL USAGE:"
    echo "  source venv/bin/activate    # Activate environment"
    echo "  python main.py              # Run interactively"
    echo "  ./run_local.sh              # Quick run"
    echo
fi
if [ "$INSTALL_TYPE" = "2" ] || [ "$INSTALL_TYPE" = "3" ]; then
    echo "DOCKER USAGE:"
    echo "  ./run_docker.sh                              # Interactive"
    echo "  docker-compose -f docker/docker-compose.yml up  # Start service"
    echo
fi
echo "CONFIGURATION:"
echo "  Edit files in config/ directory"
echo "  Update config/download.json, upload.json, sync.json"
echo
if [ ! -f "credentials.json" ]; then
    echo "⚠️  WARNING: credentials.json not found!"
    echo "   Get it from: https://console.cloud.google.com/"
fi
echo "═══════════════════════════════════════════════════"
echo
log_info "Installation script finished"
