#!/bin/bash
set -e

# Entrypoint script for Google Drive Sync
# Handles initialization and runtime configuration

# Colours for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Colour

# Function to log messages
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_debug() {
    if [ "${DEBUG}" = "true" ]; then
        echo -e "${BLUE}[DEBUG]${NC} $1"
    fi
}

# Function to handle signals
cleanup() {
    log_info "Received shutdown signal, cleaning up..."
    
    # Kill child processes
    if [ -n "${CHILD_PID}" ]; then
        kill -TERM "${CHILD_PID}" 2>/dev/null || true
        wait "${CHILD_PID}" 2>/dev/null || true
    fi
    
    log_info "Cleanup complete"
    exit 0
}

# Trap signals
trap cleanup SIGTERM SIGINT SIGQUIT

# Banner
cat << "EOF"
  ____                   _        ____       _            
 / ___| ___   ___   __ _| | ___  |  _ \ _ __(_)_   _____  
| |  _ / _ \ / _ \ / _` | |/ _ \ | | | | '__| \ \ / / _ \ 
| |_| | (_) | (_) | (_| | |  __/ | |_| | |  | |\ V /  __/ 
 \____|\___/ \___/ \__, |_|\___| |____/|_|  |_| \_/ \___| 
                   |___/                                   
    ____                   _____           _ 
   / ___| _   _ _ __   ___|_   _|__   ___ | |
   \___ \| | | | '_ \ / __| | |/ _ \ / _ \| |
    ___) | |_| | | | | (__  | | (_) | (_) | |
   |____/ \__, |_| |_|\___| |_|\___/ \___/|_|
          |___/                               

EOF

log_info "Starting Google Drive Sync Tool v1.0.0"
log_info "User: $(whoami) ($(id -u):$(id -g))"
log_info "Working directory: $(pwd)"

# Check if credentials exist
if [ ! -f "/app/credentials.json" ]; then
    log_error "credentials.json not found!"
    log_error "Please mount your credentials.json file:"
    log_error "  -v /path/to/credentials.json:/app/credentials.json:ro"
    exit 1
fi

log_info "Found credentials.json"

# Ensure data directories exist with correct permissions
log_info "Setting up data directories..."

mkdir -p "${GDRIVE_DATA_DIR}/logs" || log_warn "Could not create logs directory"
mkdir -p "${GDRIVE_DATA_DIR}/metrics" || log_warn "Could not create metrics directory"
mkdir -p "${GDRIVE_DATA_DIR}/state" || log_warn "Could not create state directory"
mkdir -p "${GDRIVE_DOWNLOAD_DIR}" || log_warn "Could not create downloads directory"

# Check permissions
if [ ! -w "${GDRIVE_DATA_DIR}" ]; then
    log_warn "Data directory is not writable: ${GDRIVE_DATA_DIR}"
fi

# Check for token
if [ -f "/app/token/token.json" ]; then
    log_info "Found existing authentication token"
    # Create symlink if needed
    if [ ! -L "/app/token.json" ] && [ ! -f "/app/token.json" ]; then
        ln -s /app/token/token.json /app/token.json || log_warn "Could not create token symlink"
    fi
else
    log_warn "No authentication token found - first run will require authentication"
fi

# Display configuration
log_info "Configuration:"
log_info "  Data directory: ${GDRIVE_DATA_DIR}"
log_info "  Config directory: ${GDRIVE_CONFIG_DIR}"
log_info "  Download directory: ${GDRIVE_DOWNLOAD_DIR}"
log_info "  Timezone: ${TZ:-UTC}"

# Check if running in cron mode
if [ "${CRON_ENABLED}" = "true" ]; then
    log_info "Starting in CRON mode..."
    
    # Check if crontab file exists
    if [ ! -f "/etc/cron.d/gdrive-sync" ]; then
        log_error "Crontab file not found at /etc/cron.d/gdrive-sync"
        log_error "Please mount your crontab file:"
        log_error "  -v /path/to/crontab:/etc/cron.d/gdrive-sync:ro"
        exit 1
    fi
    
    # Set proper permissions on crontab
    chmod 0644 /etc/cron.d/gdrive-sync
    
    # Create cron log
    touch "${GDRIVE_DATA_DIR}/logs/cron.log"
    
    log_info "Crontab loaded:"
    cat /etc/cron.d/gdrive-sync
    
    # Start cron in foreground
    log_info "Starting cron daemon..."
    exec cron -f -L 15
    
else
    log_info "Starting in INTERACTIVE mode..."
    
    # Check if first argument is a shell
    if [ "$1" = "bash" ] || [ "$1" = "sh" ]; then
        log_info "Starting interactive shell..."
        exec "$@"
    else
        # Execute the main command
        log_info "Executing: $*"
        exec "$@" &
        CHILD_PID=$!
        
        # Wait for child process
        wait "${CHILD_PID}"
        EXIT_CODE=$?
        
        log_info "Process exited with code: ${EXIT_CODE}"
        exit ${EXIT_CODE}
    fi
fi
