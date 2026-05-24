#!/bin/bash
#
# Corpus Forge Launcher for macOS and Linux
#
# This script sets up and runs the Corpus Forge application
# Usage: ./run.sh
#
# Requirements:
# - Python 3.8 or higher installed
# - Internet connection (for first-time setup)

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Make run.py executable
chmod +x run.py

# Run the Python launcher
python3 run.py
