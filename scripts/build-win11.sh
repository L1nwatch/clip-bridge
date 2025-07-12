#!/bin/bash

# Build script for Windows 11 executable
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
rm -rf dist/electron
rm -rf dist/python
rm -rf build

# Step 1: Build Python server executable for Windows
echo "🐍 Building Python server for Windows..."
if [ ! -d "utils/.venv" ]; then
    echo "📦 Creating Python virtual environment..."
    cd utils
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    pip install pyinstaller
    cd ..
else
    echo "📦 Using existing Python virtual environment..."
    cd utils
    source .venv/bin/activate
    cd ..
fi

# Create the Python executable for Windows
echo "🔨 Creating Windows Python executable..."
cd utils
source .venv/bin/activate
pyinstaller --distpath ../dist/python server-win.spec
cd ..

# Step 2: Install npm dependencies
echo "📦 Installing npm dependencies..."
npm install

# Step 3: Build React app
echo "⚛️  Building React application..."
npm run build

# Step 4: Build Electron app for Windows
echo "🖥️  Building Electron app for Windows 11..."
npx electron-builder --win --x64

echo "✅ Build completed!"
echo "📁 Output files:"
echo "   - Windows Installer: dist/electron/ClipBridge Setup *.exe"
echo "   - Windows Portable: dist/electron/ClipBridge-*-win.zip"
echo "   - Python Server: dist/python/server.exe"

echo ""
echo "🚀 To run on Windows 11:"
echo "   1. Copy the installer to a Windows 11 machine"
echo "   2. Run the .exe installer"
echo "   3. The app will be installed and ready to use"
