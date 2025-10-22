#!/bin/bash

# Health check script for Google Drive Sync container

# Check if Python is working
python3 -c "import sys; sys.exit(0)" || exit 1

# Check if required directories exist and are accessible
test -d /data || exit 1
test -w /data || exit 1

# Check if credentials exist
test -f /app/credentials.json || exit 1

# Check if main.py exists
test -f /app/main.py || exit 1

# All checks passed
exit 0
