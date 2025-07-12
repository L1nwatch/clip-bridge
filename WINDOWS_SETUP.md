# Windows Installation Guide

## Prerequisites
Install these on your Windows machine:

1. **Python 3.8 or later**
   - Download from https://python.org
   - ⚠️ **IMPORTANT**: Check "Add Python to PATH" during installation

2. **Required Python packages**:
   ```cmd
   pip install flask flask-cors pyperclip gevent gevent-websocket loguru requests websocket-client
   ```

## Installation Steps

1. **Download & Install ClipBridge**
   - Run `ClipBridge Setup 0.1.0.exe` 
   - Or extract `ClipBridge-0.1.0-win.zip`

2. **Verify Python Installation**
   ```cmd
   python --version
   pip list | findstr "flask pyperclip"
   ```

## Usage

### Automatic Mode (Recommended)
1. Start ClipBridge application
2. Enter your Mac's IP address in the app
3. The app will automatically:
   - Connect to your Mac server
   - Sync clipboards bidirectionally

### Manual Mode (for testing)
1. **On Mac**: Start the server (done automatically by the Mac app)
2. **On Windows**: Run the client manually:
   ```cmd
   cd "C:\Users\%USERNAME%\AppData\Local\Programs\ClipBridge\resources\python"
   set SERVER_HOST=192.168.1.100
   python client.py
   ```

## How It Works

### Bidirectional Sync:
- **Mac → Windows**: When you copy something on Mac, it automatically appears in Windows clipboard
- **Windows → Mac**: When you copy something on Windows, it automatically appears in Mac clipboard

### Connection:
- Windows acts as **Client**
- Mac acts as **Server** 
- Real-time WebSocket connection for instant sync

## Troubleshooting

### "WebSocket error: Handshake status 404"
- Make sure the Mac server is running
- Check if the IP address is correct
- Verify firewall settings allow port 8000

### "ModuleNotFoundError: No module named 'pyperclip'"
```cmd
pip install pyperclip flask flask-cors gevent gevent-websocket loguru requests websocket-client
```

### "python is not recognized"
- Reinstall Python with "Add to PATH" checked
- Or manually add Python to your Windows PATH

### Connection timeout
- Check Mac IP address is correct
- Ensure both devices are on the same network
- Try disabling Windows Firewall temporarily

## Network Setup

1. **Find your Mac's IP address**:
   ```bash
   # On Mac, run in Terminal:
   ifconfig | grep "inet " | grep -v 127.0.0.1
   ```

2. **Use that IP in Windows app** (e.g., `192.168.1.100`)

3. **Firewall**: Ensure port 8000 is open on Mac
