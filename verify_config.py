#!/usr/bin/env python3
"""
BensBot System Verification Tool
This script checks for required components and proper configuration
"""

import os
import sys
import subprocess
import json
from pathlib import Path

# ANSI colors
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
RED = '\033[0;31m'
BLUE = '\033[0;34m'
NC = '\033[0m'  # No Color

def print_color(color, message):
    print(f"{color}{message}{NC}")

def check_environment():
    """Check the Python environment and path setup"""
    print_color(BLUE, "\n== Checking Environment ==")
    
    # Check Python version
    print(f"Python version: {sys.version}")
    
    # Check PYTHONPATH
    pythonpath = os.environ.get('PYTHONPATH', '')
    if '/Users/bendickinson/Desktop/Trading:BenBot' in pythonpath:
        print_color(GREEN, "✓ PYTHONPATH includes project root")
    else:
        print_color(YELLOW, f"⚠ PYTHONPATH does not include project root: {pythonpath}")
        print_color(YELLOW, "  Add this to your ~/.bash_profile or ~/.zshrc:")
        print_color(YELLOW, "  export PYTHONPATH=\"$PYTHONPATH:/Users/bendickinson/Desktop/Trading:BenBot\"")

    # Check virtual environment
    venv_path = Path("/Users/bendickinson/Desktop/trading_venv")
    if venv_path.exists():
        print_color(GREEN, "✓ Virtual environment found")
    else:
        print_color(YELLOW, "⚠ Virtual environment not found at expected location")
        print_color(YELLOW, "  Create it with: python -m venv /Users/bendickinson/Desktop/trading_venv")

def check_backend():
    """Check the FastAPI backend configuration"""
    print_color(BLUE, "\n== Checking Backend ==")
    
    # Check for FastAPI installation
    try:
        subprocess.run([sys.executable, "-c", "import fastapi"], check=True, capture_output=True)
        print_color(GREEN, "✓ FastAPI is installed")
    except (subprocess.CalledProcessError, ImportError):
        print_color(YELLOW, "⚠ FastAPI is not installed in current environment")
        print_color(YELLOW, "  Install it with: pip install fastapi uvicorn")
    
    # Check for API module
    api_path = Path("/Users/bendickinson/Desktop/Trading:BenBot/trading_bot/api")
    if api_path.exists():
        print_color(GREEN, "✓ API directory exists")
        
        # Check for app.py
        app_file = api_path / "app.py"
        if app_file.exists():
            print_color(GREEN, "✓ app.py found")
        else:
            print_color(RED, "✗ app.py not found! FastAPI launcher won't work")
            # List files in the directory to help identify the correct module
            print("Files in api directory:")
            for file in api_path.glob("*.py"):
                print(f"  - {file.name}")
    else:
        print_color(RED, "✗ API directory not found! Backend won't start")

def check_frontend():
    """Check the React frontend configuration"""
    print_color(BLUE, "\n== Checking Frontend ==")
    
    frontend_path = Path("/Users/bendickinson/Desktop/Trading:BenBot/trading-dashboard")
    if frontend_path.exists():
        print_color(GREEN, "✓ Dashboard directory exists")
        
        # Check package.json
        package_json = frontend_path / "package.json"
        if package_json.exists():
            print_color(GREEN, "✓ package.json found")
            
            try:
                with open(package_json, 'r') as f:
                    pkg_data = json.load(f)
                
                # Check for start or dev script
                scripts = pkg_data.get('scripts', {})
                if 'start' in scripts:
                    print_color(GREEN, f"✓ npm start command found: {scripts['start']}")
                elif 'dev' in scripts:
                    print_color(GREEN, f"✓ npm run dev command found: {scripts['dev']}")
                else:
                    print_color(YELLOW, "⚠ No start or dev script found in package.json")
                    print_color(YELLOW, "  Available scripts:")
                    for script, command in scripts.items():
                        print(f"  - {script}: {command}")
                    
                # Check if API URL is hardcoded
                if frontend_path.joinpath('src').exists():
                    api_files = list(frontend_path.glob('src/**/*.js')) + list(frontend_path.glob('src/**/*.ts'))
                    api_endpoint_check = False
                    
                    for file in api_files:
                        with open(file, 'r') as f:
                            content = f.read()
                            if 'localhost:8000' in content:
                                print_color(GREEN, f"✓ API endpoint configuration found in {file.relative_to(frontend_path)}")
                                api_endpoint_check = True
                                break
                    
                    if not api_endpoint_check:
                        print_color(YELLOW, "⚠ Could not verify API endpoint configuration")
                        print_color(YELLOW, "  Make sure frontend is configured to use http://localhost:8000")
            
            except (json.JSONDecodeError, IOError) as e:
                print_color(RED, f"✗ Error reading package.json: {e}")
        else:
            print_color(RED, "✗ package.json not found! Frontend won't start")
    else:
        print_color(RED, "✗ Dashboard directory not found! Frontend won't start")

def check_launch_script():
    """Check the launch script configuration"""
    print_color(BLUE, "\n== Checking Launch Script ==")
    
    script_path = Path("/Users/bendickinson/Desktop/Trading:BenBot/start_bensbot.sh")
    if script_path.exists():
        print_color(GREEN, "✓ start_bensbot.sh found")
        
        # Check executable permission
        if os.access(script_path, os.X_OK):
            print_color(GREEN, "✓ script is executable")
        else:
            print_color(YELLOW, "⚠ script is not executable")
            print_color(YELLOW, "  Run: chmod +x /Users/bendickinson/Desktop/Trading:BenBot/start_bensbot.sh")
    else:
        print_color(RED, "✗ start_bensbot.sh not found!")

def main():
    print_color(BLUE, "BensBot System Verification")
    print_color(BLUE, "==========================")
    
    check_environment()
    check_backend()
    check_frontend()
    check_launch_script()
    
    print_color(BLUE, "\n== Summary ==")
    print("Run the system with: ./start_bensbot.sh")
    print("This will start both backend and frontend components")
    print("Press Ctrl+C to stop all components when finished")
    
if __name__ == "__main__":
    main()
