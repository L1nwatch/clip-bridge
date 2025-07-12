#!/bin/bash

# Build script for W# Create the Python distribution for Windows (source files instead of executable)
echo "📁 Copying Python source files for bundling..."
mkdir -p dist/python
cp utils/server.py utils/client.py utils/requirements.txt dist/python/ 11 executable
# This script builds both the Python server and the Electron app for Windows

set -e

echo "🏗️  Building ClipBridge for Windows 11..."

# Check if we have the necessary tools
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed. Please install Node.js first."
    exit 1
fi

if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "❌ Python is not installed. Please install Python first."
    exit 1
fi

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf dist/electron build

# Step 1: Build Python server executable for Windows
echo "🐍 Building Python server for Windows..."
if [ ! -d "utils/.venv" ]; then
    echo "📦 Creating Python virtual environment..."
    cd utils && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && pip install pyinstaller && cd ..
else
    echo "📦 Using existing Python virtual environment..."
fi

# Create the Python distribution for Windows (source files instead of executable)
echo "� Copying Python source files for bundling..."
mkdir -p dist/python
cp utils/server.py dist/python/
cp utils/client.py dist/python/
cp utils/requirements.txt dist/python/

echo "✅ Python source files prepared for bundling"

# Step 2: Install npm dependencies
echo "📦 Installing npm dependencies..."
npm install

# Step 3: Build React app
echo "⚛️  Building React application..."
npm run build

# Step 4: Build Electron app for Windows
echo "🖥️  Building Electron app for Windows 11..."
npx electron-builder --win --x64

# Step 5: Clean artifacts - keep only final .exe file
echo "🧽 Cleaning build artifacts..."
cd dist/electron
find . -type f ! -name '*.dmg' ! -name '*.exe' -delete
rm -rf mac* win* linux* *.yml *.yaml
find . -type d -empty -delete
cd ../..

echo "✅ Build completed!"
echo "📁 Output files:"
echo "   - Windows x64 Installer: dist/electron/ClipBridge Setup *.exe"
echo "   - Python Source Files: dist/python/"

echo ""
echo "🚀 To run on Windows 11:"
echo "   1. Copy the installer to a Windows 11 machine"
echo "   2. Run the .exe installer"
echo "   3. Make sure Python 3.8+ is installed with required packages:"
echo "      pip install flask flask-cors pyperclip gevent gevent-websocket loguru requests websocket-client"
echo "   4. The app will be installed and ready to use"
