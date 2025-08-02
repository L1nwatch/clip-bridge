#!/usr/bin/env python3
"""
Unit tests for clipboard_utils module.

Tests the core clipboard functionality including ClipboardData class
and cross-platform clipboard operations.
"""

import pytest
import json
import base64
import sys
import os
import subprocess
from unittest.mock import patch, MagicMock

# Add parent directory to path to import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from clipboard_utils import (
    ClipboardData, 
    CrossPlatformClipboard,
    get_clipboard,
    set_clipboard,
    get_clipboard_text,
    set_clipboard_text
)


class TestClipboardData:
    """Test cases for ClipboardData class."""

    def test_init_text_data(self):
        """Test ClipboardData initialization with text."""
        content = "Hello, World!"
        data_type = "text"
        clipboard_data = ClipboardData(content, data_type)
        
        assert clipboard_data.content == content
        assert clipboard_data.data_type == data_type
        assert clipboard_data.metadata == {}

    def test_init_with_metadata(self):
        """Test ClipboardData initialization with metadata."""
        content = "Test content"
        data_type = "text"
        metadata = {"source": "test", "timestamp": 1234567890}
        
        clipboard_data = ClipboardData(content, data_type, metadata)
        
        assert clipboard_data.content == content
        assert clipboard_data.data_type == data_type
        assert clipboard_data.metadata == metadata

    def test_to_dict_text(self):
        """Test converting text ClipboardData to dictionary."""
        content = "Sample text"
        data_type = "text"
        metadata = {"app": "test"}
        
        clipboard_data = ClipboardData(content, data_type, metadata)
        result = clipboard_data.to_dict()
        
        expected = {
            "content": content,
            "data_type": data_type,
            "metadata": metadata
        }
        assert result == expected

    def test_to_dict_image(self):
        """Test converting image ClipboardData to dictionary."""
        # Create a mock PIL Image object for image data
        from unittest.mock import MagicMock
        mock_image = MagicMock()
        data_type = "image"
        metadata = {"format": "PNG", "size": "100x200"}
        
        clipboard_data = ClipboardData(mock_image, data_type, metadata)
        
        # Mock the PIL Image save operation
        image_bytes = b"fake_image_data"
        with patch('clipboard_utils.io.BytesIO') as mock_bytesio:
            mock_buffer = MagicMock()
            mock_bytesio.return_value = mock_buffer
            mock_buffer.read.return_value = image_bytes
            
            result = clipboard_data.to_dict()
            
            # Verify the structure
            assert result["data_type"] == data_type
            assert result["metadata"] == metadata
            # The save method should have been called on the mock image
            mock_image.save.assert_called_once_with(mock_buffer, format="PNG")

    def test_from_dict_text(self):
        """Test creating ClipboardData from dictionary with text."""
        data = {
            "content": "Test text content",
            "data_type": "text",
            "metadata": {"source": "test"}
        }
        
        clipboard_data = ClipboardData.from_dict(data)
        
        assert clipboard_data.content == data["content"]
        assert clipboard_data.data_type == data["data_type"]
        assert clipboard_data.metadata == data["metadata"]

    def test_from_dict_image(self):
        """Test creating ClipboardData from dictionary with image."""
        image_bytes = b"fake_image_data"
        base64_content = base64.b64encode(image_bytes).decode('utf-8')
        
        data = {
            "content": base64_content,
            "data_type": "image",
            "metadata": {"format": "png"}
        }
        
        # Mock PIL Image.open since we're using fake data
        with patch('clipboard_utils.Image.open') as mock_image_open:
            mock_image = MagicMock()
            mock_image_open.return_value = mock_image
            
            clipboard_data = ClipboardData.from_dict(data)
            
            assert clipboard_data.content == mock_image  # Should be the PIL Image object
            assert clipboard_data.data_type == "image"
            assert clipboard_data.metadata == {"format": "png"}

    def test_to_json(self):
        """Test converting ClipboardData to JSON string."""
        content = "JSON test content"
        data_type = "text"
        metadata = {"test": True}
        
        clipboard_data = ClipboardData(content, data_type, metadata)
        json_str = clipboard_data.to_json()
        
        # Parse back to verify structure
        parsed = json.loads(json_str)
        assert parsed["content"] == content
        assert parsed["data_type"] == data_type
        assert parsed["metadata"] == metadata

    def test_from_json(self):
        """Test creating ClipboardData from JSON string."""
        data = {
            "content": "From JSON test",
            "data_type": "text",
            "metadata": {"parsed": True}
        }
        json_str = json.dumps(data)
        
        clipboard_data = ClipboardData.from_json(json_str)
        
        assert clipboard_data.content == data["content"]
        assert clipboard_data.data_type == data["data_type"]
        assert clipboard_data.metadata == data["metadata"]

    def test_json_roundtrip(self):
        """Test JSON serialization and deserialization roundtrip."""
        original = ClipboardData("Roundtrip test", "text", {"test": "value"})
        json_str = original.to_json()
        restored = ClipboardData.from_json(json_str)
        
        assert restored.content == original.content
        assert restored.data_type == original.data_type
        assert restored.metadata == original.metadata


class TestCrossPlatformClipboard:
    """Test cases for CrossPlatformClipboard class."""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Set up test environment before each test."""
        self.clipboard = CrossPlatformClipboard()

    @patch('platform.system')
    def test_init_sets_platform(self, mock_platform):
        """Test that initialization detects platform correctly."""
        mock_platform.return_value = "Darwin"
        clipboard = CrossPlatformClipboard()
        assert clipboard.platform == "Darwin"

    @patch('clipboard_utils.subprocess.run')
    @patch('platform.system')
    def test_get_macos_text_clipboard(self, mock_platform, mock_subprocess):
        """Test getting text from macOS clipboard."""
        mock_platform.return_value = "Darwin"
        mock_subprocess.return_value.stdout = "Hello from macOS"
        mock_subprocess.return_value.returncode = 0
        
        clipboard = CrossPlatformClipboard()
        result = clipboard._get_macos_clipboard()
        
        assert result is not None
        assert result.content == "Hello from macOS"
        assert result.data_type == "text"

    @patch('clipboard_utils.subprocess.run')
    @patch('platform.system')
    def test_get_macos_clipboard_error(self, mock_platform, mock_subprocess):
        """Test macOS clipboard access error handling."""
        mock_platform.return_value = "Darwin"
        mock_subprocess.side_effect = Exception("Command failed")
        
        clipboard = CrossPlatformClipboard()
        result = clipboard._get_macos_clipboard()
        
        assert result is None

    @patch('clipboard_utils.subprocess.Popen')
    @patch('platform.system')
    def test_set_macos_text_clipboard(self, mock_platform, mock_popen):
        """Test setting text to macOS clipboard."""
        mock_platform.return_value = "Darwin"
        
        # Mock subprocess.Popen
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_popen.return_value = mock_process
        
        # Create clipboard instance after mocking platform
        clipboard = CrossPlatformClipboard()
        clipboard.platform = "Darwin"  # Ensure platform is set
        
        test_data = ClipboardData("Test macOS set", "text")
        result = clipboard._set_macos_clipboard(test_data)
        
        assert result is True
        mock_popen.assert_called_once_with(['pbcopy'], stdin=subprocess.PIPE, text=True)
        mock_process.communicate.assert_called_once_with(input="Test macOS set")

    @patch('platform.system')
    def test_get_clipboard_data_macos(self, mock_platform):
        """Test get_clipboard_data method on macOS."""
        mock_platform.return_value = "Darwin"
        
        with patch.object(CrossPlatformClipboard, '_get_macos_clipboard') as mock_get:
            mock_get.return_value = ClipboardData("macOS test", "text")
            
            clipboard = CrossPlatformClipboard()
            result = clipboard.get_clipboard_data()
            
            assert result is not None
            assert result.content == "macOS test"
            mock_get.assert_called_once()

    @patch('platform.system')
    def test_set_clipboard_data_macos(self, mock_platform):
        """Test set_clipboard_data method on macOS."""
        mock_platform.return_value = "Darwin"
        
        with patch.object(CrossPlatformClipboard, '_set_macos_clipboard') as mock_set:
            mock_set.return_value = True
            
            clipboard = CrossPlatformClipboard()
            test_data = ClipboardData("Set macOS test", "text")
            result = clipboard.set_clipboard_data(test_data)
            
            assert result is True
            mock_set.assert_called_once_with(test_data)

    @patch('platform.system')
    def test_unsupported_platform(self, mock_platform):
        """Test behavior on unsupported platform."""
        mock_platform.return_value = "UnsupportedOS"
        
        clipboard = CrossPlatformClipboard()
        
        # Should return None for unsupported platforms
        result = clipboard.get_clipboard_data()
        assert result is None
        
        test_data = ClipboardData("Test", "text")
        set_result = clipboard.set_clipboard_data(test_data)
        assert set_result is False


class TestClipboardFunctions:
    """Test cases for module-level clipboard functions."""

    @patch('clipboard_utils.clipboard')
    def test_get_clipboard(self, mock_clipboard_instance):
        """Test get_clipboard function."""
        expected_data = ClipboardData("Function test", "text")
        mock_clipboard_instance.get_clipboard_data.return_value = expected_data
        
        result = get_clipboard()
        
        assert result == expected_data
        mock_clipboard_instance.get_clipboard_data.assert_called_once()

    @patch('clipboard_utils.clipboard')
    def test_set_clipboard(self, mock_clipboard_instance):
        """Test set_clipboard function."""
        mock_clipboard_instance.set_clipboard_data.return_value = True
        
        test_data = ClipboardData("Function set test", "text")
        result = set_clipboard(test_data)
        
        assert result is True
        mock_clipboard_instance.set_clipboard_data.assert_called_once_with(test_data)

    @patch('clipboard_utils.get_clipboard')
    def test_get_clipboard_text(self, mock_get_clipboard):
        """Test get_clipboard_text function."""
        mock_get_clipboard.return_value = ClipboardData("Text function test", "text")
        
        result = get_clipboard_text()
        
        assert result == "Text function test"
        mock_get_clipboard.assert_called_once()

    @patch('clipboard_utils.get_clipboard')
    def test_get_clipboard_text_no_data(self, mock_get_clipboard):
        """Test get_clipboard_text when no data available."""
        mock_get_clipboard.return_value = None
        
        result = get_clipboard_text()
        
        assert result == ""
        mock_get_clipboard.assert_called_once()

    @patch('clipboard_utils.get_clipboard')
    def test_get_clipboard_text_non_text_data(self, mock_get_clipboard):
        """Test get_clipboard_text with non-text data."""
        mock_get_clipboard.return_value = ClipboardData(b"image_data", "image")
        
        result = get_clipboard_text()
        
        assert result == ""
        mock_get_clipboard.assert_called_once()

    @patch('clipboard_utils.set_clipboard')
    def test_set_clipboard_text(self, mock_set_clipboard):
        """Test set_clipboard_text function."""
        mock_set_clipboard.return_value = True
        
        result = set_clipboard_text("Text to set")
        
        assert result is True
        mock_set_clipboard.assert_called_once()
        # Verify the ClipboardData object was created correctly
        call_args = mock_set_clipboard.call_args[0][0]
        assert call_args.content == "Text to set"
        assert call_args.data_type == "text"


class TestWindowsClipboard:
    """Test cases for Windows-specific clipboard functionality."""

    @patch('platform.system')
    @patch('clipboard_utils.win32clipboard', create=True)
    @patch('clipboard_utils.win32con', create=True)
    def test_get_windows_text_clipboard(self, mock_win32con, mock_win32clipboard, mock_platform):
        """Test getting text from Windows clipboard."""
        mock_platform.return_value = "Windows"
        
        # Mock Windows clipboard operations
        mock_win32clipboard.OpenClipboard.return_value = None
        mock_win32clipboard.IsClipboardFormatAvailable.return_value = True
        mock_win32clipboard.GetClipboardData.return_value = "Windows test text"
        mock_win32clipboard.CloseClipboard.return_value = None
        mock_win32clipboard.CF_UNICODETEXT = 13
        mock_win32clipboard.CF_DIB = 8
        mock_win32con.CF_UNICODETEXT = 13
        mock_win32con.CF_DIB = 8
        
        clipboard = CrossPlatformClipboard()
        clipboard.platform = "Windows"  # Ensure platform is set
        result = clipboard._get_windows_clipboard()
        
        assert result is not None
        assert result.content == "Windows test text"
        assert result.data_type == "text"

    @patch('platform.system')
    @patch('clipboard_utils.win32clipboard', create=True)
    @patch('clipboard_utils.win32con', create=True)
    def test_set_windows_text_clipboard(self, mock_win32con, mock_win32clipboard, mock_platform):
        """Test setting text to Windows clipboard."""
        mock_platform.return_value = "Windows"
        
        # Mock Windows clipboard operations
        mock_win32clipboard.OpenClipboard.return_value = None
        mock_win32clipboard.EmptyClipboard.return_value = None
        mock_win32clipboard.SetClipboardData.return_value = None
        mock_win32clipboard.CloseClipboard.return_value = None
        mock_win32clipboard.CF_UNICODETEXT = 13
        mock_win32con.CF_UNICODETEXT = 13
        
        clipboard = CrossPlatformClipboard()
        clipboard.platform = "Windows"  # Ensure platform is set
        test_data = ClipboardData("Windows set test", "text")
        result = clipboard._set_windows_clipboard(test_data)
        
        assert result is True

    @patch('platform.system')
    @patch('clipboard_utils.win32clipboard', create=True)
    def test_windows_clipboard_error_handling(self, mock_win32clipboard, mock_platform):
        """Test Windows clipboard error handling."""
        mock_platform.return_value = "Windows"
        mock_win32clipboard.OpenClipboard.side_effect = Exception("Clipboard busy")
        
        clipboard = CrossPlatformClipboard()
        clipboard.platform = "Windows"  # Ensure platform is set
        result = clipboard._get_windows_clipboard()
        
        assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
