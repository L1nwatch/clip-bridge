#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Unicode clipboard handling specifically for the Windows encoding fix.
"""

import pytest
from unittest.mock import patch
from clipboard_utils import ClipboardData, CrossPlatformClipboard


class TestUnicodeWindowsClipboard:
    """Test Unicode handling for Windows clipboard operations."""

    @patch("platform.system")
    @patch("clipboard_utils.win32clipboard", create=True)
    @patch("clipboard_utils.win32con", create=True)
    def test_windows_unicode_clipboard_set(
        self, mock_win32con, mock_win32clipboard, mock_platform
    ):
        """Test setting Unicode text with emojis to Windows clipboard."""
        mock_platform.return_value = "Windows"

        # Mock Windows clipboard operations
        mock_win32clipboard.OpenClipboard.return_value = None
        mock_win32clipboard.EmptyClipboard.return_value = None
        mock_win32clipboard.SetClipboardData.return_value = None
        mock_win32clipboard.CloseClipboard.return_value = None
        mock_win32con.CF_UNICODETEXT = 13

        clipboard = CrossPlatformClipboard()
        clipboard.platform = "Windows"

        # Test with Unicode text containing emojis and special characters
        unicode_text = (
            "2025-08-03 00:04:23,023 - INFO - 📊 Unevaluated solutions: 0\n"
            "📋 Unevaluated problems: 0\n"
            "✅ Problems Qwen can solve (reward > 0): 731\n"
            "📈 Total evaluated solutions: 3215\n"
            "🔥 Qwen solve rate: 14.5% (731/5048)"
        )

        test_data = ClipboardData(unicode_text, "text")
        result = clipboard._set_windows_clipboard(test_data)

        # Verify the result
        assert result is True

        # Verify that SetClipboardData was called with CF_UNICODETEXT
        mock_win32clipboard.SetClipboardData.assert_called_once_with(
            mock_win32con.CF_UNICODETEXT, unicode_text
        )

        # Verify proper clipboard handling
        mock_win32clipboard.OpenClipboard.assert_called_once()
        mock_win32clipboard.EmptyClipboard.assert_called_once()
        mock_win32clipboard.CloseClipboard.assert_called_once()

    @patch("platform.system")
    @patch("clipboard_utils.win32clipboard", create=True)
    @patch("clipboard_utils.win32con", create=True)
    def test_windows_unicode_clipboard_get(
        self, mock_win32con, mock_win32clipboard, mock_platform
    ):
        """Test getting Unicode text from Windows clipboard."""
        mock_platform.return_value = "Windows"

        # Unicode text with emojis
        unicode_text = "Hello 世界 🌍 📊 ✅ 🔥"

        # Mock Windows clipboard operations
        mock_win32clipboard.OpenClipboard.return_value = None
        mock_win32clipboard.IsClipboardFormatAvailable.side_effect = lambda fmt: (
            fmt == mock_win32con.CF_UNICODETEXT
        )
        mock_win32clipboard.GetClipboardData.return_value = unicode_text
        mock_win32clipboard.CloseClipboard.return_value = None
        mock_win32con.CF_UNICODETEXT = 13
        mock_win32con.CF_DIB = 8

        clipboard = CrossPlatformClipboard()
        clipboard.platform = "Windows"
        result = clipboard._get_windows_clipboard()

        # Verify the result
        assert result is not None
        assert result.content == unicode_text
        assert result.data_type == "text"

        # Verify that GetClipboardData was called with CF_UNICODETEXT
        mock_win32clipboard.GetClipboardData.assert_called_with(
            mock_win32con.CF_UNICODETEXT
        )

    def test_clipboard_data_unicode_json_serialization(self):
        """Test that ClipboardData properly handles Unicode in JSON serialization."""
        # Test with Unicode text containing emojis
        unicode_text = (
            "📊 Statistics: 📋 Problems: 0, ✅ Solved: 731, "
            "📈 Total: 3215, 🔥 Rate: 14.5%"
        )

        clipboard_data = ClipboardData(unicode_text, "text")

        # Test JSON serialization
        json_str = clipboard_data.to_json()
        assert unicode_text in json_str

        # Test JSON deserialization
        restored_data = ClipboardData.from_json(json_str)
        assert restored_data.content == unicode_text
        assert restored_data.data_type == "text"

    def test_fallback_unicode_handling(self):
        """Test Unicode handling when falling back to pyperclip."""
        # Since we're on macOS, win32clipboard will naturally be None
        # This tests the actual fallback path that would be used on Windows
        # when pywin32 is not installed

        import clipboard_utils

        # Save original values
        original_platform = clipboard_utils.platform.system()
        original_win32clipboard = getattr(clipboard_utils, "win32clipboard", None)

        try:
            # Mock platform to be Windows
            clipboard_utils.platform.system = lambda: "Windows"
            # Ensure win32clipboard is None (simulating missing pywin32)
            clipboard_utils.win32clipboard = None

            unicode_text = "📊 Test with emojis 🔥"
            clipboard_data = ClipboardData(unicode_text, "text")

            clipboard = CrossPlatformClipboard()
            clipboard.platform = "Windows"

            # Mock pyperclip for the test
            with patch("pyperclip.copy") as mock_copy:
                # Test fallback clipboard setting
                result = clipboard._set_windows_clipboard(clipboard_data)

                # Should succeed using pyperclip fallback
                assert result is True
                mock_copy.assert_called_once_with(unicode_text)

        finally:
            # Restore original values
            clipboard_utils.platform.system = lambda: original_platform
            if hasattr(clipboard_utils, "win32clipboard"):
                clipboard_utils.win32clipboard = original_win32clipboard


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
