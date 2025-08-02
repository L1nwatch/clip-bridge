# Unified Clipboard Implementation

## Overview
The clipboard bridge has been simplified to use a unified approach that automatically supports both text and image clipboard operations without mode switching.

## Key Changes

### 1. Removed Dual-Mode Architecture
- **Before**: Had `ENHANCED_CLIPBOARD` flag with separate text-only and enhanced modes
- **After**: Single unified implementation with automatic fallback

### 2. Simplified Code Structure
- Removed `ENHANCED_CLIPBOARD` conditional logic throughout the codebase
- Deleted legacy functions: `set_clipboard_legacy()`, `get_clipboard_legacy()`
- Unified all clipboard operations through `clipboard_utils.py`

### 3. Automatic Fallback System
The system now automatically handles different scenarios:
- **Full Support**: When PIL/Pillow and platform APIs are available → text + image support
- **Text Only**: When enhanced clipboard unavailable → automatic fallback to text-only
- **Error Handling**: Graceful degradation in all error conditions

## Architecture

### Core Components

1. **clipboard_utils.py** - Cross-platform clipboard abstraction
   - `ClipboardData` class for unified data handling
   - `CrossPlatformClipboard` with platform-specific implementations
   - Automatic fallback to pyperclip when enhanced features unavailable

2. **server.py** - Flask server with WebSocket support
   - Unified clipboard monitoring and setting
   - JSON-based message protocol for enhanced data
   - Automatic fallback to text when JSON parsing fails

3. **client.py** - Windows WebSocket client
   - Simplified clipboard monitoring
   - Unified message handling for both text and image data
   - Automatic content type detection

### Data Flow

```
1. Platform Clipboard → ClipboardData object → JSON serialization
2. WebSocket transmission (text or enhanced format)
3. JSON deserialization → ClipboardData object → Platform Clipboard
```

### Fallback Strategy

```
Enhanced Mode (Preferred):
- Cross-platform image support
- Rich metadata (timestamps, sizes)
- Multiple data types

Text-Only Fallback:
- Uses pyperclip for compatibility
- Plain text clipboard operations
- Works in all environments
```

## Benefits

1. **Simplified Maintenance**: No dual-mode conditional logic
2. **Better Reliability**: Automatic fallback prevents failures
3. **Enhanced User Experience**: Seamless text + image support when available
4. **Backward Compatibility**: Still works in text-only environments

## Dependencies

### Required (Core)
```
flask>=2.3.2
flask-cors>=4.0.0
gevent>=23.7.0
gevent-websocket>=0.10.1
loguru>=0.7.0
websocket-client>=1.6.1
pyperclip>=1.9.0
```

### Optional (Enhanced Features)
```
Pillow>=10.2.0  # For image clipboard support
pynput>=1.7.6   # For enhanced clipboard monitoring
```

## Platform Support

### macOS
- **Text**: Full support via pyperclip fallback
- **Images**: Uses `osascript` and `pbpaste` commands
- **Fallback**: pyperclip for text-only mode

### Windows  
- **Text**: Full support via pyperclip fallback
- **Images**: Uses `win32clipboard` and `PIL.ImageGrab`
- **Fallback**: pyperclip for text-only mode

### Linux
- **Text**: Full support via pyperclip
- **Images**: Limited support (depends on clipboard utilities)
- **Fallback**: pyperclip for text-only mode

## Usage

The system now works transparently:

1. **Start the server** (macOS):
   ```bash
   cd utils && python server.py
   ```

2. **Start the client** (Windows):
   ```bash
   cd utils && python client.py
   ```

3. **Copy content** on either platform:
   - Text content is synchronized automatically
   - Images are synchronized when supported
   - System automatically falls back to text-only if needed

No configuration or mode switching required!
