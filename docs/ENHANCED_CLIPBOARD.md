# Enhanced Clipboard Support

ClipBridge now supports both **text and image** clipboard synchronization across devices!

## 🆕 New Features

### Image Clipboard Support
- **Copy images between devices**: Images copied on one device automatically appear on connected devices
- **Cross-platform compatibility**: Works on both macOS and Windows
- **Multiple image formats**: Supports PNG, JPEG, BMP, and other common formats
- **Automatic format conversion**: Images are optimized for clipboard compatibility

### Enhanced Protocol
- **Backward compatibility**: Still works with text-only clients
- **JSON-based messaging**: Rich metadata support for images
- **Automatic fallback**: Gracefully degrades to text-only mode if image support unavailable

## 🔧 Technical Implementation

### Clipboard Data Structure
```python
{
    "content": "<base64-encoded-image-data-or-text>",
    "data_type": "text|image",
    "metadata": {
        "format": "PNG|JPEG|etc",
        "size": [width, height],
        "mode": "RGB|RGBA|etc"
    }
}
```

### Platform-Specific Features

#### macOS
- Uses `pbpaste`/`pbcopy` for text
- Uses `osascript` for image operations
- Supports all native macOS clipboard formats

#### Windows
- Uses Win32 clipboard API when available
- Falls back to pyperclip for text-only
- Direct PIL ImageGrab integration for images

## 📋 Usage Examples

### Text Clipboard (Legacy Compatible)
```python
from clipboard_utils import ClipboardData, set_clipboard, get_clipboard

# Set text
text_data = ClipboardData("Hello World!", 'text')
set_clipboard(text_data)

# Get clipboard content
data = get_clipboard()
if data and data.data_type == 'text':
    print(f"Text: {data.content}")
```

### Image Clipboard (New!)
```python
from PIL import Image
from clipboard_utils import ClipboardData, set_clipboard, get_clipboard

# Set image
image = Image.open("screenshot.png")
image_data = ClipboardData(image, 'image', {
    'format': 'PNG',
    'size': image.size,
    'mode': image.mode
})
set_clipboard(image_data)

# Get image
data = get_clipboard()
if data and data.data_type == 'image':
    print(f"Image size: {data.metadata['size']}")
    data.content.save("received_image.png")
```

## 🚀 Installation

### Additional Dependencies
```bash
pip install Pillow pynput
```

### Windows-Specific (Optional for better image support)
```bash
pip install pywin32
```

## 🧪 Testing

Run the enhanced clipboard test:
```bash
cd utils
python test_enhanced_clipboard.py
```

## 🔄 Migration from Text-Only

The enhanced clipboard system is **fully backward compatible**:

1. **Existing clients**: Continue to work with text-only mode
2. **Mixed environments**: Enhanced clients can communicate with legacy clients
3. **Automatic detection**: System automatically detects capabilities and adjusts

## ⚠️ Limitations

### Image Size
- Large images are automatically compressed
- Base64 encoding increases data size by ~33%
- WebSocket message size limits may apply

### Platform Support
- **Full support**: macOS, Windows 10/11
- **Text-only fallback**: Linux and other platforms
- **CI/Headless**: Automatic graceful degradation

### Performance
- Image operations are slower than text
- Network bandwidth considerations for large images
- Memory usage increases with image size

## 🔧 Configuration

### Environment Variables
```bash
# Force text-only mode (disable image support)
export CLIPBOARD_TEXT_ONLY=true

# Image compression quality (1-100)
export CLIPBOARD_IMAGE_QUALITY=85

# Maximum image dimensions
export CLIPBOARD_MAX_WIDTH=1920
export CLIPBOARD_MAX_HEIGHT=1080
```

## 📊 Monitoring

Enhanced logging shows clipboard operations:
```
📋 Mac clipboard changed to: image: (1024, 768)...
📤 Sending enhanced clipboard via WebSocket: image: (1024, 768)...
✅ Windows clipboard updated successfully: image: (1024, 768)...
```

## 🐛 Troubleshooting

### "Enhanced clipboard not available"
- Install missing dependencies: `pip install Pillow pynput`
- On Windows: `pip install pywin32` for better support

### "Image clipboard not supported"
- Check platform compatibility
- Verify clipboard access permissions
- Try text-only mode as fallback

### Performance Issues
- Reduce image quality in configuration
- Check network bandwidth
- Monitor memory usage
