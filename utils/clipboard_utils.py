#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cross-platform clipboard utilities for handling both text and image data.

This module provides a unified interface for clipboard operations across
macOS and Windows, supporting both text and image content.
"""

import os
import platform
import subprocess
import tempfile
import base64
import io
import json
from typing import Optional, Dict, Any
from PIL import Image
from loguru import logger

# Platform-specific imports
if platform.system() == "Windows":
    try:
        import win32clipboard
        import win32con
        from PIL import ImageGrab
    except ImportError:
        logger.warning(
            "Win32 clipboard modules not available, falling back to pyperclip"
        )
        win32clipboard = None


class ClipboardData:
    """Container for clipboard data with type information."""

    def __init__(self, content: Any, data_type: str, metadata: Optional[Dict] = None):
        self.content = content
        self.data_type = data_type  # 'text' or 'image'
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        if self.data_type == "image":
            # Convert PIL Image to base64 string
            buffer = io.BytesIO()
            image_format = self.metadata.get("format", "PNG")
            self.content.save(buffer, format=image_format)
            buffer.seek(0)
            image_bytes = buffer.read()
            content_b64 = base64.b64encode(image_bytes).decode("utf-8")

            return {
                "content": content_b64,
                "data_type": self.data_type,
                "metadata": self.metadata,
            }
        else:
            return {
                "content": str(self.content),
                "data_type": self.data_type,
                "metadata": self.metadata,
            }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ClipboardData":
        """Create ClipboardData from dictionary."""
        if data["data_type"] == "image":
            # Convert base64 string back to PIL Image
            image_bytes = base64.b64decode(data["content"])
            buffer = io.BytesIO(image_bytes)
            image = Image.open(buffer)
            return cls(image, data["data_type"], data["metadata"])
        else:
            return cls(data["content"], data["data_type"], data["metadata"])

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str) -> "ClipboardData":
        """Create ClipboardData from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)


class CrossPlatformClipboard:
    """Cross-platform clipboard handler supporting text and images."""

    def __init__(self):
        self.platform = platform.system()
        logger.info(f"Initializing clipboard handler for {self.platform}")

        if self.platform == "Windows" and win32clipboard is None:
            logger.warning(
                "Windows clipboard API not available - install pywin32 for full image support"
            )
            logger.info(
                "Image clipboard functionality will be limited to text descriptions"
            )
            logger.info("To enable full image support, run: pip install pywin32")

    def get_clipboard_data(self) -> Optional[ClipboardData]:
        """Get current clipboard content (text or image)."""
        try:
            if self.platform == "Darwin":
                return self._get_macos_clipboard()
            elif self.platform == "Windows":
                return self._get_windows_clipboard()
            else:
                # Fallback to text-only for unsupported platforms
                import pyperclip

                text = pyperclip.paste()
                if text:
                    return ClipboardData(text, "text")
                return None
        except Exception as e:
            logger.error(f"Failed to get clipboard content: {e}")
            return None

    def set_clipboard_data(self, clipboard_data: ClipboardData) -> bool:
        """Set clipboard content (text or image)."""
        try:
            if self.platform == "Darwin":
                return self._set_macos_clipboard(clipboard_data)
            elif self.platform == "Windows":
                return self._set_windows_clipboard(clipboard_data)
            else:
                # Fallback to text-only for unsupported platforms
                if clipboard_data.data_type == "text":
                    import pyperclip

                    pyperclip.copy(str(clipboard_data.content))
                    return True
                else:
                    logger.warning("Image clipboard not supported on this platform")
                    return False
        except Exception as e:
            logger.error(f"Failed to set clipboard content: {e}")
            return False

    def _get_macos_clipboard(self) -> Optional[ClipboardData]:
        """Get clipboard content on macOS."""
        try:
            # First try to get image data using osascript to write to temp file
            result = subprocess.run(
                ["osascript", "-e", "the clipboard as «class PNGf»"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0 and result.stdout.strip():
                # There's image data in clipboard
                # Use osascript to save image to temp file, then read it
                with tempfile.NamedTemporaryFile(
                    suffix=".png", delete=False
                ) as temp_file:
                    temp_path = temp_file.name

                try:
                    # Use osascript to write image data to file
                    write_result = subprocess.run(
                        [
                            "osascript",
                            "-e",
                            f"""set imageData to the clipboard as «class PNGf»
set imageFile to open for access POSIX file "{temp_path}" with write permission
write imageData to imageFile
close access imageFile""",
                        ],
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )

                    if write_result.returncode == 0 and os.path.exists(temp_path):
                        # Read the image file
                        with open(temp_path, "rb") as f:
                            image_data = f.read()

                        if len(image_data) > 0:
                            try:
                                # Convert to PIL Image
                                image = Image.open(io.BytesIO(image_data))
                                metadata = {
                                    "format": "PNG",
                                    "size": image.size,
                                    "mode": image.mode,
                                }
                                return ClipboardData(image, "image", metadata)
                            except Exception as e:
                                logger.debug(f"Failed to process image data: {e}")
                finally:
                    # Clean up temp file
                    try:
                        os.unlink(temp_path)
                    except Exception:
                        pass

            # If no image or image processing failed, try text
            text_result = subprocess.run(
                ["pbpaste"], capture_output=True, text=True, timeout=5
            )

            if text_result.returncode == 0:
                text = text_result.stdout
                if text:
                    return ClipboardData(text, "text")

            return None

        except subprocess.TimeoutExpired:
            logger.error("Clipboard access timed out")
            return None
        except Exception as e:
            logger.error(f"macOS clipboard error: {e}")
            return None

    def _set_macos_clipboard(self, clipboard_data: ClipboardData) -> bool:
        """Set clipboard content on macOS."""
        try:
            if clipboard_data.data_type == "text":
                # Set text content
                process = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE, text=True)
                process.communicate(input=str(clipboard_data.content))
                return process.returncode == 0

            elif clipboard_data.data_type == "image":
                # Set image content
                with tempfile.NamedTemporaryFile(
                    suffix=".png", delete=False
                ) as temp_file:
                    clipboard_data.content.save(temp_file.name, "PNG")

                    # Use osascript to set image to clipboard
                    result = subprocess.run(
                        [
                            "osascript",
                            "-e",
                            (
                                f"set the clipboard to (read POSIX file "
                                f'"{temp_file.name}" as «class PNGf»)'
                            ),
                        ],
                        timeout=5,
                    )

                    # Clean up temp file
                    os.unlink(temp_file.name)

                    return result.returncode == 0

            return False

        except Exception as e:
            logger.error(f"Failed to set macOS clipboard: {e}")
            return False

    def _get_windows_clipboard(self) -> Optional[ClipboardData]:
        """Get clipboard content on Windows."""
        if win32clipboard is None:
            # Fallback to pyperclip for text only
            try:
                import pyperclip

                text = pyperclip.paste()
                if text:
                    return ClipboardData(text, "text")
                return None
            except Exception as e:
                logger.error(f"Fallback clipboard access failed: {e}")
                return None

        try:
            win32clipboard.OpenClipboard()

            # Try to get image first
            if win32clipboard.IsClipboardFormatAvailable(win32con.CF_DIB):
                try:
                    # Get image using PIL ImageGrab
                    image = ImageGrab.grabclipboard()
                    if image is not None:
                        metadata = {
                            "format": "PNG",
                            "size": image.size,
                            "mode": image.mode,
                        }
                        win32clipboard.CloseClipboard()
                        return ClipboardData(image, "image", metadata)
                except Exception as e:
                    logger.debug(f"Failed to get image from clipboard: {e}")

            # Try to get text
            if win32clipboard.IsClipboardFormatAvailable(win32con.CF_UNICODETEXT):
                text = win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT)
                win32clipboard.CloseClipboard()
                if text:
                    return ClipboardData(text, "text")
            elif win32clipboard.IsClipboardFormatAvailable(win32con.CF_TEXT):
                text = win32clipboard.GetClipboardData(win32con.CF_TEXT)
                win32clipboard.CloseClipboard()
                if text:
                    return ClipboardData(text.decode("utf-8", errors="ignore"), "text")

            win32clipboard.CloseClipboard()
            return None

        except Exception as e:
            try:
                win32clipboard.CloseClipboard()
            except Exception:
                pass
            logger.error(f"Windows clipboard error: {e}")
            return None

    def _set_windows_clipboard(self, clipboard_data: ClipboardData) -> bool:
        """Set clipboard content on Windows."""
        if win32clipboard is None:
            # Fallback to pyperclip for text only
            if clipboard_data.data_type == "text":
                try:
                    import pyperclip

                    pyperclip.copy(str(clipboard_data.content))
                    return True
                except Exception as e:
                    logger.error(f"Fallback clipboard set failed: {e}")
                    return False
            else:
                logger.info(
                    "Image clipboard requires pywin32 package. Install with: pip install pywin32"
                )
                logger.info("Falling back to text-only clipboard functionality")
                # Try to save image as a file path or description as fallback
                try:
                    if hasattr(clipboard_data.content, "size"):
                        size_info = f"Image [{clipboard_data.content.size[0]}x{clipboard_data.content.size[1]}]"
                        import pyperclip

                        pyperclip.copy(f"Image data: {size_info}")
                        logger.info(
                            f"Copied image description to clipboard: {size_info}"
                        )
                        return True
                except Exception as e:
                    logger.debug(f"Fallback image description failed: {e}")
                return False

        try:
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()

            if clipboard_data.data_type == "text":
                # Set text content
                win32clipboard.SetClipboardText(str(clipboard_data.content))

            elif clipboard_data.data_type == "image":
                # Convert PIL Image to format suitable for clipboard
                output = io.BytesIO()
                clipboard_data.content.save(output, format="BMP")
                data = output.getvalue()[14:]  # Remove BMP header
                win32clipboard.SetClipboardData(win32con.CF_DIB, data)

            win32clipboard.CloseClipboard()
            return True

        except Exception as e:
            try:
                win32clipboard.CloseClipboard()
            except Exception:
                pass
            logger.error(f"Failed to set Windows clipboard: {e}")
            return False


# Global clipboard instance
clipboard = CrossPlatformClipboard()


def get_clipboard() -> Optional[ClipboardData]:
    """Get current clipboard content."""
    return clipboard.get_clipboard_data()


def set_clipboard(data: ClipboardData) -> bool:
    """Set clipboard content."""
    return clipboard.set_clipboard_data(data)


def get_clipboard_text() -> str:
    """Get clipboard text content (legacy compatibility)."""
    data = get_clipboard()
    if data and data.data_type == "text":
        return str(data.content)
    return ""


def set_clipboard_text(text: str) -> bool:
    """Set clipboard text content (legacy compatibility)."""
    data = ClipboardData(text, "text")
    return set_clipboard(data)
