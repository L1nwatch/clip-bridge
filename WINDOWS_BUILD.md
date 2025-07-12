# Windows Build Information

## Overview
This Windows build uses Python source files instead of a compiled executable for maximum compatibility.

## Requirements
The Windows machine where this app runs must have:
1. **Python 3.8 or later** installed from https://python.org
2. **Python packages** installed:
   ```bash
   pip install flask flask-cors pyperclip
   ```

## How It Works
- The app automatically detects system Python when launched
- It runs the bundled `server.py` script using the system Python interpreter
- This approach avoids cross-compilation issues between macOS and Windows

## Troubleshooting
If the app fails to start:
1. Verify Python is installed: `python --version`
2. Install required packages: `pip install -r requirements.txt` (using the bundled requirements.txt)
3. Make sure Python is in your system PATH

## File Structure
The Windows app includes:
- `resources/python/server.py` - Main server script
- `resources/python/client.py` - Client communication script  
- `resources/python/requirements.txt` - Python dependencies
- `resources/python/README.md` - Installation instructions

This solution provides better compatibility across different Windows configurations compared to a single compiled executable.
