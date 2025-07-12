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
pyinstaller --onefile --distpath ../dist/python-standalone server.py --name clipbridge-server

# Step 4: Build client executable
echo "🔨 Building client standalone executable..."
pyinstaller --onefile --distpath ../dist/python-standalone client.py --name clipbridge-client

# Step 5: Return to root directory
cd ..

# Step 6: Display results
echo "✅ Build complete!"
echo "📦 Standalone executables created:"
ls -lh dist/python-standalone/

echo "💡 These executables can be run directly without Python or any dependencies installed"
echo "   - Server: dist/python-standalone/clipbridge-server"
echo "   - Client: dist/python-standalone/clipbridge-client"
