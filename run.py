#!/usr/bin/env python3
"""
Corpus Forge Launcher
=====================

This script:
1. Checks/creates Python virtual environment
2. Installs required dependencies
3. Starts the Flask application
4. Opens the app in your default browser
5. Displays the localhost link

Usage:
    python run.py
    or
    python3 run.py

Works on: Windows, Mac, Linux
"""

import os
import sys
import subprocess
import platform
import time
import webbrowser
from pathlib import Path

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text):
    """Print a formatted header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}")
    print(text.center(60))
    print('='*60 + f"{Colors.ENDC}\n")

def print_success(text):
    """Print success message."""
    print(f"{Colors.GREEN}✓ {text}{Colors.ENDC}")

def print_error(text):
    """Print error message."""
    print(f"{Colors.RED}✗ {text}{Colors.ENDC}")

def print_info(text):
    """Print info message."""
    print(f"{Colors.CYAN}ℹ {text}{Colors.ENDC}")

def get_venv_path():
    """Get the virtual environment path."""
    return Path(__file__).parent / ".venv"

def get_pip_executable():
    """Get the pip executable path for the current environment."""
    is_windows = platform.system() == "Windows"
    venv_path = get_venv_path()
    
    if is_windows:
        return venv_path / "Scripts" / "pip.exe"
    else:
        return venv_path / "bin" / "pip"

def get_python_executable():
    """Get the Python executable path for the current environment."""
    is_windows = platform.system() == "Windows"
    venv_path = get_venv_path()
    
    if is_windows:
        return venv_path / "Scripts" / "python.exe"
    else:
        return venv_path / "bin" / "python"

def create_venv():
    """Create virtual environment if it doesn't exist."""
    venv_path = get_venv_path()
    
    if venv_path.exists():
        print_success("Virtual environment already exists")
        return True
    
    print_info("Creating virtual environment...")
    try:
        subprocess.check_call([sys.executable, "-m", "venv", str(venv_path)])
        print_success(f"Virtual environment created at {venv_path}")
        return True
    except Exception as e:
        print_error(f"Failed to create virtual environment: {e}")
        return False

def upgrade_pip():
    """Upgrade pip to latest version."""
    pip_path = get_pip_executable()
    print_info("Upgrading pip...")
    try:
        subprocess.check_call([str(pip_path), "install", "--upgrade", "pip"])
        print_success("pip upgraded")
        return True
    except Exception as e:
        print_error(f"Failed to upgrade pip: {e}")
        return False

def install_requirements():
    """Install required packages from requirements.txt."""
    requirements_path = Path(__file__).parent / "requirements.txt"
    pip_path = get_pip_executable()
    
    if not requirements_path.exists():
        print_error(f"requirements.txt not found at {requirements_path}")
        return False
    
    print_info("Installing dependencies from requirements.txt...")
    try:
        subprocess.check_call([str(pip_path), "install", "-r", str(requirements_path)])
        print_success("All dependencies installed successfully")
        return True
    except Exception as e:
        print_error(f"Failed to install requirements: {e}")
        return False

def run_app():
    """Run the Flask application."""
    python_path = get_python_executable()
    app_path = Path(__file__).parent / "app.py"
    
    print_info("Starting Flask application...")
    try:
        # Get local IP for display
        import socket
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        
        print_header("Corpus Forge is Running!")
        print(f"{Colors.GREEN}{Colors.BOLD}The app is now running locally.{Colors.ENDC}")
        print(f"\n{Colors.BOLD}Access the application at:{Colors.ENDC}")
        print(f"  • {Colors.CYAN}http://localhost:5000{Colors.ENDC}")
        print(f"  • {Colors.CYAN}http://127.0.0.1:5000{Colors.ENDC}")
        print(f"  • {Colors.CYAN}http://{local_ip}:5000{Colors.ENDC}")
        print(f"\n{Colors.YELLOW}Press Ctrl+C to stop the server{Colors.ENDC}\n")
        
        # Open browser
        print_info("Opening browser...")
        webbrowser.open("http://localhost:5000")
        time.sleep(1)
        
        # Run Flask app
        subprocess.run([str(python_path), str(app_path)])
        
    except KeyboardInterrupt:
        print_info("\nShutting down gracefully...")
        print_success("Application stopped")
    except Exception as e:
        print_error(f"Failed to run application: {e}")
        return False
    
    return True

def main():
    """Main entry point."""
    print_header("Corpus Forge Setup & Launch")
    
    # Check Python version
    print_info(f"Python {platform.python_version()} on {platform.system()}")
    
    # Step 1: Create virtual environment
    print_header("Step 1: Virtual Environment")
    if not create_venv():
        print_error("Failed to setup virtual environment")
        sys.exit(1)
    
    # Step 2: Upgrade pip
    print_header("Step 2: Upgrade pip")
    if not upgrade_pip():
        print_error("Failed to upgrade pip")
        sys.exit(1)
    
    # Step 3: Install requirements
    print_header("Step 3: Install Dependencies")
    if not install_requirements():
        print_error("Failed to install dependencies")
        sys.exit(1)
    
    # Step 4: Run application
    print_header("Step 4: Launch Application")
    run_app()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Interrupted by user{Colors.ENDC}")
        sys.exit(0)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        sys.exit(1)
