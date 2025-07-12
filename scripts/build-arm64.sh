#!/bin/bash

# ClipBridge ARM64 Mac Build Script
# This script builds only the ARM64 DMG for macOS and cleans up unnecessary files

echo "🚀 Starting ClipBridge ARM64 Mac build..."

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

# Step 2: Ensure icons are present
echo "🎨 Checking application icons..."
if [ ! -f "assets/icon.icns" ] || [ ! -s "assets/icon.icns" ]; then
    echo "   Creating icons..."
    python3 -c "
from PIL import Image, ImageDraw
import os

# Create a 512x512 image with transparent background
size = 512
img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# Colors
bg_color = (240, 240, 240, 255)
border_color = (51, 51, 51, 255)
clip_color = (102, 102, 102, 255)
accent_color = (76, 175, 80, 255)
text_color = (51, 51, 51, 255)

# Draw clipboard background
margin = 64
clipboard_width = size - 2 * margin
clipboard_height = int(clipboard_width * 1.5)
clipboard_x = margin
clipboard_y = margin

# Main clipboard rectangle
draw.rounded_rectangle(
    [clipboard_x, clipboard_y, clipboard_x + clipboard_width, clipboard_y + clipboard_height],
    radius=16, fill=bg_color, outline=border_color, width=8
)

# Clipboard clip
clip_width = clipboard_width // 3
clip_height = 64
clip_x = clipboard_x + (clipboard_width - clip_width) // 2
clip_y = clipboard_y - clip_height // 2

draw.rounded_rectangle(
    [clip_x, clip_y, clip_x + clip_width, clip_y + clip_height],
    radius=8, fill=clip_color, outline=border_color, width=4
)

# Inner clip area
inner_margin = 16
draw.rounded_rectangle(
    [clip_x + inner_margin, clip_y + inner_margin, 
     clip_x + clip_width - inner_margin, clip_y + clip_height - inner_margin],
    radius=4, fill=bg_color
)

# Document lines
line_start_x = clipboard_x + 32
line_width = clipboard_width - 64
line_y_start = clipboard_y + 80
line_spacing = 32
line_height = 8

for i in range(5):
    y = line_y_start + i * line_spacing
    width = line_width if i % 3 != 2 else line_width * 0.75
    draw.rounded_rectangle(
        [line_start_x, y, line_start_x + width, y + line_height],
        radius=4, fill=text_color
    )

# Connection symbol (circle)
center_x = clipboard_x + clipboard_width // 2
center_y = clipboard_y + clipboard_height * 0.6
circle_radius = 24

draw.ellipse(
    [center_x - circle_radius, center_y - circle_radius, 
     center_x + circle_radius, center_y + circle_radius],
    fill=accent_color, outline=border_color, width=4
)

# Connection lines
line_y1 = center_y + 32
line_y2 = center_y + 48
line_length = 48
line_start = center_x - line_length // 2

draw.rounded_rectangle(
    [line_start, line_y1, line_start + line_length, line_y1 + 8],
    radius=4, fill=accent_color
)
draw.rounded_rectangle(
    [line_start, line_y2, line_start + line_length, line_y2 + 8],
    radius=4, fill=accent_color
)

# Save the image
img.save('assets/icon.png')
"
    
    # Create ICNS and ICO files
    mkdir -p assets/iconset.iconset
    sizes=(16 32 128 256 512)
    for size in "${sizes[@]}"; do
        sips -z $size $size assets/icon.png --out assets/iconset.iconset/icon_${size}x${size}.png >/dev/null 2>&1
        if [ $size -le 256 ]; then
            double_size=$((size * 2))
            sips -z $double_size $double_size assets/icon.png --out assets/iconset.iconset/icon_${size}x${size}@2x.png >/dev/null 2>&1
        fi
    done
    
    # Create ICNS file and cleanup safely
    iconutil -c icns assets/iconset.iconset --output assets/icon.icns >/dev/null 2>&1
    if [ -f "assets/icon.icns" ] && [ -d "assets/iconset.iconset" ]; then
        echo "   Removing temporary iconset directory..."
        rm -rf assets/iconset.iconset
    fi
    
    python3 -c "
from PIL import Image
img = Image.open('assets/icon.png')
sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
icons = [img.resize(size, Image.Resampling.LANCZOS) for size in sizes]
img.save('assets/icon.ico', format='ICO', sizes=[(icon.width, icon.height) for icon in icons])
" 2>/dev/null || echo "   Note: ICO creation requires Pillow"
    
    echo "   ✅ Icons created successfully"
else
    echo "   ✅ Icons already exist"
fi

# Step 3: Build standalone Python executables only
echo "🐍 Building standalone Python executables..."
./scripts/build-standalone-python.sh

# Step 4: Build React app and Electron DMG (ARM64 only)
echo "⚛️  Building React app and Electron DMG..."
npm run build:clean && npx electron-builder --mac --arm64 --config config/electron-builder.json

# Step 5: Clean up artifacts - keep only final .dmg file
echo "🧽 Cleaning build artifacts..."
# Safety check: Make sure we're in the correct directory
if [ -d "dist/electron" ]; then
  cd dist/electron
  
  # Check if we have any .dmg files before deleting other files
  if ls *.dmg 1> /dev/null 2>&1; then
    echo "   Found .dmg files, cleaning up other artifacts..."
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
    echo "❌ WARNING: No .dmg files found in dist/electron. Skipping cleanup to prevent data loss."
  fi
  
  cd ../..
else
  echo "❌ WARNING: dist/electron directory not found. Skipping cleanup."
fi

# Step 6: Show results
echo "✅ Build complete!"
echo "📦 Distribution file:"
ls -la dist/electron/
echo "📊 File size:"
du -h dist/electron/ClipBridge-0.1.0-arm64.dmg
echo ""
echo "🎉 Ready for distribution: dist/electron/ClipBridge-0.1.0-arm64.dmg"
echo "💡 Size breakdown: ~112MB (includes Electron runtime + standalone Python executables + React app)"
