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
