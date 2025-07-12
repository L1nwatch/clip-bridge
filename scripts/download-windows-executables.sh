#!/bin/bash

# Download Windows Executables from GitHub Actions
# This script downloads the latest Windows x64 executables built by GitHub Actions

echo "🔄 Downloading Windows executables from GitHub Actions..."

# Create the output directory
mkdir -p dist/python-standalone

# Check if GitHub CLI is available
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI (gh) is not installed."
    echo "   Please install it from: https://cli.github.com/"
    echo "   Or build locally using: ./scripts/build-standalone-python.sh --cross-platform"
    exit 1
fi

# Check if we're authenticated
if ! gh auth status &> /dev/null; then
    echo "❌ Not authenticated with GitHub CLI."
    echo "   Please run: gh auth login"
    exit 1
fi

echo "📥 Fetching latest Windows build artifacts..."

# Download the latest Windows executables
if gh run download --name windows-x64-executables --dir dist/python-standalone/ 2>/dev/null; then
    echo "✅ Successfully downloaded Windows executables!"
    
    # Verify the files
    if [ -f "dist/python-standalone/clipbridge-server.exe" ] && [ -f "dist/python-standalone/clipbridge-client.exe" ]; then
        echo "✅ Verified downloaded files:"
        ls -lh dist/python-standalone/clipbridge-*.exe
        
        # Make them executable
        chmod +x dist/python-standalone/clipbridge-*.exe
        
        echo ""
        echo "🎉 Windows executables are ready!"
        echo "   Server: dist/python-standalone/clipbridge-server.exe"
        echo "   Client: dist/python-standalone/clipbridge-client.exe"
        echo ""
        echo "💡 You can now run: ./scripts/build-win11.sh"
    else
        echo "❌ Downloaded files are incomplete or corrupted"
        exit 1
    fi
else
    echo "❌ Failed to download Windows executables from GitHub Actions"
    echo "   This could mean:"
    echo "   1. No recent successful builds with Windows artifacts"
    echo "   2. Network connectivity issues"
    echo "   3. Repository access issues"
    echo ""
    echo "💡 Alternative: Build locally using:"
    echo "   ./scripts/build-standalone-python.sh --cross-platform"
    echo "   (Note: This creates macOS executables with .exe extension, not true Windows executables)"
    exit 1
fi
