#!/bin/bash

# ClipBridge Windows 11 Build Script (Standalone Version)
# This script builds the Windows 11 executable with embedded standalone Python executables

echo "🚀 Starting ClipBridge Windows 11 build..."

# Step 1: Clean previous builds
echo "🧹 Cleaning previous builds..."
# Safety check: Make sure we're in the project directory
if [ ! -f "package.json" ]; then
  echo "❌ ERROR: package.json not found. Make sure you're running this script from the project root directory."
  exit 1
fi

# Safe cleanup with verification
if [ -d "dist/electron" ]; then
  echo "   Removing dist/electron directory..."
  rm -rf dist/electron
fi

if [ -d "build" ]; then
  echo "   Removing build directory..."
  rm -rf build
fi

# Step 2: Build standalone Python executables
echo "🐍 Building standalone Python executables..."
./scripts/build-standalone-python.sh

# Verify the standalone executables were created
echo "✅ Verifying standalone executables..."
if [ ! -f "dist/python-standalone/clipbridge-server" ] && [ ! -f "dist/python-standalone/clipbridge-server.exe" ]; then
  echo "❌ ERROR: Standalone server executable was not created!"
  exit 1
fi
if [ ! -f "dist/python-standalone/clipbridge-client" ] && [ ! -f "dist/python-standalone/clipbridge-client.exe" ]; then
  echo "❌ ERROR: Standalone client executable was not created!"
  exit 1
fi
echo "✅ Standalone executables verified successfully"

# Step 3: Install npm dependencies
echo "📦 Installing npm dependencies..."
npm install

# Step 4: Build React application
echo "⚛️ Building React application..."
npm run build:clean

# Step 5: Build Electron app for Windows 11
echo "🖥️ Building Electron app for Windows 11..."
# Use a separate config file instead of package.json
npx electron-builder --win --x64 --config electron-builder.json

# Optional: Check the contents of the packaged app before cleanup
echo "📦 Checking package contents before cleanup..."
if [ -d "dist/electron/win-unpacked/resources" ]; then
  echo "Contents of resources directory:"
  ls -la dist/electron/win-unpacked/resources/
  
  echo "Contents of python-standalone directory (if it exists):"
  if [ -d "dist/electron/win-unpacked/resources/python-standalone" ]; then
    ls -la dist/electron/win-unpacked/resources/python-standalone/
    
    # Check file permissions
    echo "File permissions for python-standalone executables:"
    ls -la dist/electron/win-unpacked/resources/python-standalone/clipbridge-server*
    ls -la dist/electron/win-unpacked/resources/python-standalone/clipbridge-client*
  else
    echo "❌ WARNING: python-standalone directory not found in packaged app!"
  fi
else
  echo "❌ WARNING: resources directory not found in packaged app!"
fi

# Step 6: Clean up artifacts - keep only final .exe file
echo "🧽 Cleaning build artifacts..."
# Safety check: Make sure we're in the correct directory
if [ -d "dist/electron" ]; then
  cd dist/electron
  
  # Check if we have any .exe files before deleting other files
  if ls *.exe 1> /dev/null 2>&1; then
    echo "   Found .exe files, cleaning up other artifacts..."
    # Delete files that aren't .exe or .dmg files
    find . -type f ! -name '*.dmg' ! -name '*.exe' -delete
    
    # Safe removal of specific directories
    for dir in mac win linux; do
      if [ -d "$dir" ]; then
        echo "   Removing $dir directory..."
        rm -rf "$dir"
      fi
    done
    
    # Remove YAML files separately
    rm -f *.yml *.yaml
    
    # Clean up empty directories
    find . -type d -empty -delete
  else
    echo "❌ WARNING: No .exe files found in dist/electron. Skipping cleanup to prevent data loss."
  fi
  
  cd ../..
else
  echo "❌ WARNING: dist/electron directory not found. Skipping cleanup."
fi

# Step 7: Show results
echo "✅ Build completed!"
echo "📁 Output files:"
ls -la dist/electron/

echo "🚀 To run on Windows 11:"
echo "   1. Copy the installer to a Windows 11 machine"
echo "   2. Run the .exe installer"
echo "   3. The app will be installed and ready to use (no Python dependencies required)"
