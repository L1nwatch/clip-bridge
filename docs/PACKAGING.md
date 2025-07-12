# ClipBridge Packaging Guide

This guide explains how to package ClipBridge for distribution on Windows and macOS.

## Prerequisites

1. **Node.js** (v14 or higher)
2. **Python** (3.9 or higher) 
3. **Virtual environment** set up in `utils/.venv/`
4. **PyInstaller** installed in the virtual environment

## Quick Start

### Build Everything
```bash
# Build both Python executables and Electron app
./build-all.sh
```

### Build Python Only
```bash
# Build Python server executable
./build-python.sh
```

### Build Electron Only
```bash
# Build React app and package Electron
npm run electron:dist
```

## Platform-Specific Builds

### For Current Platform
```bash
npm run dist:mac      # macOS only
npm run dist:win      # Windows only (when run on Windows)
```

### Cross-Platform Build
```bash
npm run dist:all      # Both macOS and Windows
```

## Manual Steps

### 1. Install Dependencies
```bash
# Install Node.js dependencies
npm install

# Install Python dependencies
cd utils
source .venv/bin/activate
pip install -r requirements.txt
pip install pyinstaller
```

### 2. Build Python Executable
```bash
cd utils
source .venv/bin/activate
pyinstaller --clean --noconfirm server.spec
```

### 3. Build React App
```bash
npm run build
```

### 4. Package Electron App
```bash
npm run electron:dist
```

## Output Locations

- **Electron Apps**: `dist/electron/`
  - macOS: `ClipBridge-0.1.0.dmg` and `ClipBridge-0.1.0-mac.zip`
  - Windows: `ClipBridge Setup 0.1.0.exe` and `ClipBridge-0.1.0-win.zip`

- **Python Executables**: `dist/python/`
  - macOS/Linux: `clipbridge-server`
  - Windows: `clipbridge-server.exe`

## Icons

Replace the placeholder files in `assets/` with actual icons:
- `assets/icon.icns` - macOS icon (512x512, 256x256, 128x128, 64x64, 32x32, 16x16)
- `assets/icon.ico` - Windows icon (256x256, 128x128, 64x64, 48x48, 32x32, 16x16)

You can create these from a PNG using:
- **macOS**: `iconutil -c icns icon.iconset/`
- **Windows**: Online converters or ImageMagick

## Distribution

### macOS
1. **DMG**: Double-click to mount, drag to Applications
2. **ZIP**: Extract and copy to Applications folder

### Windows
1. **NSIS Installer**: Run the `.exe` installer
2. **ZIP**: Extract to desired location

## Troubleshooting

### Python Dependencies Missing
```bash
cd utils
source .venv/bin/activate
pip install -r requirements.txt
```

### Electron Build Fails
```bash
# Clean and rebuild
rm -rf node_modules dist
npm install
npm run build
npm run electron:dist
```

### PyInstaller Issues
```bash
# Clean PyInstaller cache
rm -rf utils/build utils/dist
cd utils
source .venv/bin/activate
pyinstaller --clean --noconfirm server.spec
```

## Development vs Production

The app automatically detects the environment:

- **Development**: Uses Python scripts directly with virtual environment
- **Production**: Uses bundled Python executables from `resources/python/`

## Signing (Optional)

For production distribution, consider code signing:

### macOS
```bash
# Add to package.json build config
"mac": {
  "identity": "Developer ID Application: Your Name"
}
```

### Windows
```bash
# Add to package.json build config
"win": {
  "certificateFile": "cert.p12",
  "certificatePassword": "password"
}
```
