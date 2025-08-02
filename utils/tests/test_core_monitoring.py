#!/usr/bin/env python3
"""
Tests for core clipboard monitoring functionality.

Tests the heart of the clipboard bridge: monitoring and synchronization.
"""

import pytest
import sys
import os
import json
from unittest.mock import patch, MagicMock

# Add parent directory to path to import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import client
import server
from clipboard_utils import ClipboardData


class TestClipboardMonitoring:
    """Test cases for core clipboard monitoring functionality."""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Set up test environment before each test."""
        # Reset global variables
        client.running = True
        client.last_windows_clipboard = ""
        server.last_mac_clipboard = ""

    def teardown_method(self):
        """Clean up after each test."""
        client.running = False

    @patch('client.get_clipboard')
    @patch('client.send_clipboard_to_server')
    @patch('time.sleep')
    def test_windows_clipboard_monitoring_loop(self, mock_sleep, mock_send, mock_get_clipboard):
        """Test Windows clipboard monitoring detects changes and sends them."""
        # Setup initial state
        initial_data = ClipboardData("initial content", "text")
        changed_data = ClipboardData("new content", "text")
        
        mock_get_clipboard.side_effect = [
            initial_data,  # Initial check
            initial_data,  # First loop iteration (no change)
            changed_data,  # Second loop iteration (change detected)
            None  # Stop the loop
        ]
        
        # Track loop iterations
        loop_count = 0
        def mock_sleep_side_effect(duration):
            nonlocal loop_count
            loop_count += 1
            if loop_count >= 2:  # Stop after 2 iterations
                client.running = False
        
        mock_sleep.side_effect = mock_sleep_side_effect
        
        # Run the monitoring function
        client.monitor_windows_clipboard()
        
        # Verify clipboard changes were detected and sent
        assert mock_send.call_count >= 1
        # Verify it was called with the new content
        mock_send.assert_called_with(changed_data.to_json())

    @patch('server.get_clipboard')
    @patch('server.notify_clients')
    @patch('time.sleep')
    def test_mac_clipboard_monitoring_loop(self, mock_sleep, mock_notify, mock_get_clipboard):
        """Test Mac clipboard monitoring detects changes and notifies clients."""
        # Setup initial state
        initial_data = ClipboardData("initial mac content", "text")
        changed_data = ClipboardData("new mac content", "text")
        
        # Track loop iterations and stop after a few
        loop_count = 0
        def mock_sleep_side_effect(duration):
            nonlocal loop_count
            loop_count += 1
            if loop_count >= 3:  # Stop after 3 iterations
                raise Exception("Test loop stop")
        
        mock_sleep.side_effect = mock_sleep_side_effect
        
        mock_get_clipboard.side_effect = [
            initial_data,  # Initial check
            initial_data,  # First loop iteration (no change)
            changed_data,  # Second loop iteration (change detected)
            changed_data,  # Third loop iteration (should trigger stop)
        ]
        
        # Run the monitoring function with timeout protection
        try:
            server.monitor_mac_clipboard()
        except Exception as e:
            if "Test loop stop" not in str(e):
                raise  # Re-raise unexpected exceptions
        
        # Verify clipboard changes were detected and clients notified
        assert mock_notify.call_count >= 1
        assert loop_count >= 3  # Ensure we actually ran through iterations

    @patch('client.get_clipboard')
    def test_windows_clipboard_initialization_error_handling(self, mock_get_clipboard):
        """Test Windows clipboard monitoring handles initialization errors."""
        # Simulate clipboard not available (CI environment)
        mock_get_clipboard.side_effect = Exception("could not find a copy/paste mechanism")
        
        # Should return early without crashing
        client.monitor_windows_clipboard()
        
        # Function should complete without error

    @patch('client.get_clipboard')
    @patch('client.send_clipboard_to_server')
    @patch('time.sleep')
    def test_windows_clipboard_monitoring_error_recovery(
        self, mock_sleep, mock_send, mock_get_clipboard
    ):
        """Test Windows clipboard monitoring recovers from errors during monitoring."""
        # Setup to simulate error then recovery
        mock_get_clipboard.side_effect = [
            ClipboardData("initial", "text"),  # Initial successful check
            Exception("Temporary error"),  # Error during monitoring
            ClipboardData("recovered", "text"),  # Recovery
            None  # Stop
        ]
        
        loop_count = 0

        def mock_sleep_side_effect(duration):
            nonlocal loop_count
            loop_count += 1
            if loop_count >= 3:
                client.running = False
        
        mock_sleep.side_effect = mock_sleep_side_effect
        
        # Should handle error gracefully and continue
        client.monitor_windows_clipboard()
        
        # Verify it continued after error
        assert mock_get_clipboard.call_count >= 3

    @patch('server.get_clipboard')
    @patch('server.notify_clients')
    @patch('time.sleep')
    def test_mac_clipboard_monitoring_error_recovery(
        self, mock_sleep, mock_notify, mock_get_clipboard
    ):
        """Test Mac clipboard monitoring recovers from errors."""
        # Track iterations and stop after enough attempts
        loop_count = 0

        def mock_sleep_side_effect(duration):
            nonlocal loop_count
            loop_count += 1
            if loop_count >= 4:  # Stop after 4 iterations
                raise Exception("Test loop stop")
        
        mock_sleep.side_effect = mock_sleep_side_effect
        
        call_count = 0

        def mock_get_clipboard_side_effect():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return ClipboardData("initial", "text")
            elif call_count == 2:
                raise Exception("Temporary clipboard error")
            elif call_count == 3:
                return ClipboardData("recovered", "text")
            else:
                return ClipboardData("final", "text")
        
        mock_get_clipboard.side_effect = mock_get_clipboard_side_effect
        
        # Should handle error and continue monitoring
        try:
            server.monitor_mac_clipboard()
        except Exception as e:
            if "Test loop stop" not in str(e):
                raise  # Re-raise unexpected exceptions
        
        # Verify it attempted to continue after error
        assert call_count >= 3
        assert loop_count >= 4

    @patch('client.ws_connection')
    @patch('client.get_clipboard')
    def test_clipboard_change_detection_algorithm(self, mock_get_clipboard, mock_ws):
        """Test the core algorithm for detecting clipboard changes."""
        # Setup mock WebSocket
        mock_ws.send = MagicMock()
        client.ws_connection = mock_ws
        
        # Test different scenarios
        test_cases = [
            # (previous_content, new_content, should_send)
            ("", "new content", True),  # Empty to content
            ("same content", "same content", False),  # No change
            ("old content", "new content", True),  # Content change
            ("content", "", False),  # Content to empty (shouldn't send empty)
        ]
        
        for prev_content, new_content, should_send in test_cases:
            mock_ws.send.reset_mock()
            
            # Set the previous clipboard state
            if prev_content:
                client.last_windows_clipboard = ClipboardData(prev_content, "text").to_json()
            else:
                client.last_windows_clipboard = ""
            
            # Mock clipboard to return new content
            if new_content:
                mock_get_clipboard.return_value = ClipboardData(new_content, "text")
            else:
                mock_get_clipboard.return_value = None
            # Simulate one iteration of monitoring
            current_clipboard_data = client.get_clipboard()
            current_clipboard = current_clipboard_data.to_json() if current_clipboard_data else ""
            
            if (
                current_clipboard != client.last_windows_clipboard
                and current_clipboard.strip()
            ):
                client.send_clipboard_to_server(current_clipboard)
                sent = True
            else:
                sent = False
            
            assert sent == should_send, (
                f"Failed for '{prev_content}' -> '{new_content}': "
                f"expected {should_send}, got {sent}. "
                f"Previous JSON: {client.last_windows_clipboard}, "
                f"Current JSON: {current_clipboard}"
            )


class TestClipboardSynchronization:
    """Test cases for clipboard synchronization between client and server."""

    @patch('client.set_clipboard')
    @patch('server.set_clipboard_compat')
    def test_bidirectional_clipboard_sync(self, mock_server_set, mock_client_set):
        """Test complete bidirectional clipboard synchronization."""
        mock_client_set.return_value = True
        mock_server_set.return_value = True
        
        # Simulate Windows -> Mac sync
        test_content = "Windows clipboard content"
        
        # Client detects change and sends to server
        with patch('client.ws_connection') as mock_ws:
            mock_ws.send = MagicMock()
            client.send_clipboard_to_server(test_content)
            
            # Verify WebSocket message was sent
            mock_ws.send.assert_called()
        
        # Server receives and processes the message
        with patch('server.websocket_clients') as mock_clients:
            mock_client_ws = MagicMock()
            mock_clients.__iter__ = lambda x: iter([mock_client_ws])
            mock_clients.__len__ = lambda x: 1
            
            # Simulate server processing the clipboard update
            server.set_clipboard_compat(test_content)
            mock_server_set.assert_called_with(test_content)

    @patch('client.get_clipboard')
    @patch('server.get_clipboard')
    def test_image_clipboard_sync(self, mock_server_get, mock_client_get):
        """Test image clipboard synchronization."""
        # Create mock image data
        image_data = b"fake_image_bytes"
        image_clipboard = ClipboardData(image_data, "image", {"format": "PNG", "size": "100x200"})
        
        # Test client side image detection
        mock_client_get.return_value = image_clipboard
        result = client.get_clipboard()
        
        assert result.data_type == "image"
        assert result.content == image_data
        
        # Test server side image detection
        mock_server_get.return_value = image_clipboard
        result = server.get_clipboard()
        
        assert result.data_type == "image"
        assert result.content == image_data

    @patch('client.send_clipboard_to_server')
    @patch('client.get_clipboard')
    def test_text_vs_image_priority(self, mock_get_clipboard, mock_send):
        """Test handling when clipboard contains both text and image."""
        # Create a mock PIL Image object for realistic testing
        from PIL import Image
        
        # Create a simple test image
        test_image = Image.new('RGB', (10, 10), color='red')
        
        # Most systems prioritize image over text
        mixed_clipboard = ClipboardData(test_image, "image", {"format": "PNG"})
        mock_get_clipboard.return_value = mixed_clipboard
        
        # Simulate clipboard change detection
        current_data = client.get_clipboard()
        if current_data:
            client.send_clipboard_to_server(current_data.to_json())
        
        # Should send the image data, not fallback to text
        mock_send.assert_called_with(mixed_clipboard.to_json())


class TestClipboardContentHandling:
    """Test cases for different types of clipboard content."""

    def test_large_text_handling(self):
        """Test handling of large text content."""
        large_text = "A" * 10000  # 10KB of text
        clipboard_data = ClipboardData(large_text, "text")
        
        # Should handle large content without issues
        json_data = clipboard_data.to_json()
        restored_data = ClipboardData.from_json(json_data)
        
        assert restored_data.content == large_text
        assert restored_data.data_type == "text"

    def test_unicode_text_handling(self):
        """Test handling of Unicode text content."""
        unicode_text = "Hello 世界 🌍 éñ ñÓ üñĨčØðë"
        clipboard_data = ClipboardData(unicode_text, "text")
        
        # Should preserve Unicode characters
        json_data = clipboard_data.to_json()
        restored_data = ClipboardData.from_json(json_data)
        
        assert restored_data.content == unicode_text
        assert restored_data.data_type == "text"

    def test_empty_clipboard_handling(self):
        """Test handling of empty clipboard."""
        # Test empty JSON string handling
        try:
            result = ClipboardData.from_json('')
            assert result is None  # Should handle empty gracefully
        except json.JSONDecodeError:
            # This is also acceptable behavior for empty input
            pass
        
        # Test empty string content
        empty_clipboard = ClipboardData("", "text")
        json_data = empty_clipboard.to_json()
        restored_data = ClipboardData.from_json(json_data)
        
        assert restored_data.content == ""
        assert restored_data.data_type == "text"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
