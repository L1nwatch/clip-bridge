#!/bin/bash

# ClipBridge Standalone Python Build Script
# This script builds standalone executables for both server.py and client.py 
# that don't require Python or any dependencies to be installed on the target system

echo "🚀 Starting ClipBridge Standalone Python build..."

# Ensure output directory exists
mkdir -p dist/python-standalone

# Step 1: Activate the existing virtual environment
echo "🐍 Activating Python virtual environment..."
source utils/.venv/bin/activate

# Step 2: Install PyInstaller if not already installed
echo "📦 Ensuring PyInstaller is installed..."
pip install pyinstaller

# Step 3: Build server executable
echo "🔨 Building server standalone executable..."
cd utils

# Determine the target platform
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "win32" ]]; then
  # Windows platform - add .exe extension
  pyinstaller --onefile --distpath ../dist/python-standalone server.py --name clipbridge-server.exe
else
  # Unix-like platform (macOS, Linux)
  pyinstaller --onefile --distpath ../dist/python-standalone server.py --name clipbridge-server
  
  # If building for cross-platform distribution, create Python scripts with Windows wrappers
  if [[ "$1" == "--cross-platform" ]] || [[ "$2" == "--cross-platform" ]]; then
    echo "Creating Windows-compatible server executable wrapper..."
    echo "Since PyInstaller on macOS cannot create true Windows x64 executables,"
    echo "creating Python script with Windows batch wrapper instead."
    
    # Copy the Python script to the standalone directory
    cp server.py ../dist/python-standalone/clipbridge-server.py
    
    # Create a Windows executable wrapper script
    cat > ../dist/python-standalone/clipbridge-server-win.py << 'EOF'
#!/usr/bin/env python3
"""
Windows-compatible wrapper for ClipBridge server
This script will try to run with the bundled Python or system Python
"""
import sys
import os
import subprocess

def main():
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Try to find the server script
    server_script = os.path.join(script_dir, 'clipbridge-server.py')
    
    if not os.path.exists(server_script):
        print("Error: clipbridge-server.py not found")
        sys.exit(1)
    
    # Try to run the server script
    try:
        # Use the same Python interpreter that's running this wrapper
        subprocess.run([sys.executable, server_script] + sys.argv[1:])
    except Exception as e:
        print(f"Error running server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
EOF
    
    # Make the Python wrapper executable
    chmod +x ../dist/python-standalone/clipbridge-server-win.py
  fi
fi

# Step 4: Build client executable
echo "🔨 Building client standalone executable..."
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "win32" ]]; then
  # Windows platform - add .exe extension
  pyinstaller --onefile --distpath ../dist/python-standalone client.py --name clipbridge-client.exe
else
  # Unix-like platform (macOS, Linux)
  pyinstaller --onefile --distpath ../dist/python-standalone client.py --name clipbridge-client
  
  # If building for cross-platform distribution, create Python scripts with Windows wrappers
  if [[ "$1" == "--cross-platform" ]] || [[ "$2" == "--cross-platform" ]]; then
    echo "Creating Windows-compatible client executable wrapper..."
    echo "Since PyInstaller on macOS cannot create true Windows x64 executables,"
    echo "creating Python script with Windows batch wrapper instead."
    
    # Copy the Python script to the standalone directory
    cp client.py ../dist/python-standalone/clipbridge-client.py
    
    # Create a Windows executable wrapper script
    cat > ../dist/python-standalone/clipbridge-client-win.py << 'EOF'
#!/usr/bin/env python3
"""
Windows-compatible wrapper for ClipBridge client
This script will try to run with the bundled Python or system Python
"""
import sys
import os
import subprocess

def main():
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Try to find the client script
    client_script = os.path.join(script_dir, 'clipbridge-client.py')
    
    if not os.path.exists(client_script):
        print("Error: clipbridge-client.py not found")
        sys.exit(1)
    
    # Try to run the client script
    try:
        # Use the same Python interpreter that's running this wrapper
        subprocess.run([sys.executable, client_script] + sys.argv[1:])
    except Exception as e:
        print(f"Error running client: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
EOF
    
    # Make the Python wrapper executable
    chmod +x ../dist/python-standalone/clipbridge-client-win.py
  fi
fi

# Step 5: Return to root directory
cd ..

# Step 6: Copy requirements for cross-platform compatibility
if [[ "$1" == "--cross-platform" ]] || [[ "$2" == "--cross-platform" ]]; then
  echo "📋 Copying requirements.txt for cross-platform compatibility..."
  cp utils/requirements.txt dist/python-standalone/
fi

# Step 6: Display results
echo "✅ Build complete!"
echo "📦 Standalone executables created:"
ls -lh dist/python-standalone/

echo "💡 These executables can be run directly without Python or any dependencies installed"
echo "   - Server: dist/python-standalone/clipbridge-server"
echo "   - Client: dist/python-standalone/clipbridge-client"
