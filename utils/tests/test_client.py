#!/usr/bin/env python3
"""
Unit tests for the clipboard client module.
Tests client functionality and server communication.
"""

import pytest
import unittest.mock as mock
import sys
import os
from unittest.mock import patch, MagicMock, call

# Add parent directory to path to import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import client


class TestClipboardClient:
    """Test cases for clipboard client functionality."""

    def test_environment_configuration(self):
        """Test environment variable configuration."""
        assert client.SERVER_HOST is not None
        assert client.SERVER_PORT is not None
        assert client.SERVER_URL is not None

    @mock.patch.dict(os.environ, {"SERVER_HOST": "testhost", "SERVER_PORT": "9000"})
    def test_custom_environment_configuration(self):
        """Test custom environment variable configuration."""
        # Reload the module to pick up new environment variables
        import importlib

        importlib.reload(client)

        assert "testhost" in client.SERVER_URL
        assert "9000" in client.SERVER_URL

    def test_on_message_callback(self):
        """Test WebSocket message callback."""
        mock_ws = MagicMock()

        # Test new_clipboard message (should send get_clipboard request)
        client.on_message(mock_ws, "new_clipboard")
        mock_ws.send.assert_called_with("get_clipboard")

        # Test clipboard_content message
        with patch("client.pyperclip.copy") as mock_copy:
            client.on_message(mock_ws, "clipboard_content:test content")
            mock_copy.assert_called_with("test content")

    def test_on_message_with_exception(self):
        """Test WebSocket message callback with send exception."""
        mock_ws = MagicMock()
        mock_ws.send.side_effect = Exception("WebSocket error")

        # Should not raise exception
        client.on_message(mock_ws, "new_clipboard")

    def test_on_open_callback(self):
        """Test WebSocket connection open callback."""
        mock_ws = MagicMock()
        mock_ws.sock = MagicMock()
        mock_ws.sock.connected = True

        with patch("threading.Thread") as mock_thread:
            mock_thread_instance = MagicMock()
            mock_thread.return_value = mock_thread_instance

            client.on_open(mock_ws)

            # Verify that two threads were created (monitoring + keepalive)
            assert mock_thread.call_count == 2
            # Verify start was called on both threads
            assert mock_thread_instance.start.call_count == 2

    def test_on_close_callback(self):
        """Test WebSocket connection close callback."""
        mock_ws = MagicMock()

        # Should not raise any exceptions
        client.on_close(mock_ws, 1000, "Normal closure")

    def test_on_error_callback(self):
        """Test WebSocket error callback."""
        mock_ws = MagicMock()

        # Should not raise any exceptions
        client.on_error(mock_ws, "Test error")

    @mock.patch("client.threading.Thread")
    def test_on_open_with_pending_updates(self, mock_thread):
        """Test WebSocket on_open with pending clipboard updates."""
        import client

        # Mock WebSocket
        mock_ws = MagicMock()
        mock_ws.sock = MagicMock()
        mock_ws.sock.connected = True

        # Set up pending updates
        client.pending_clipboard_updates = ["pending content 1", "pending content 2"]

        # Mock thread instances
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance

        # Call on_open
        client.on_open(mock_ws)

        # Verify connection was set
        assert client.ws_connection == mock_ws

        # Verify pending updates were processed (sent via WebSocket)
        expected_calls = [
            call("clipboard_update:pending content 1"),
            call("clipboard_update:pending content 2"),
        ]
        mock_ws.send.assert_has_calls(expected_calls)

        # Verify pending updates were cleared
        assert len(client.pending_clipboard_updates) == 0

    def test_send_clipboard_to_server_websocket_success(self):
        """Test successful clipboard sending via WebSocket."""
        import client

        # Mock WebSocket connection
        mock_ws = MagicMock()
        mock_ws.sock = MagicMock()
        mock_ws.sock.connected = True

        # Set the global WebSocket connection
        client.ws_connection = mock_ws

        test_content = "test clipboard content"
        result = client.send_clipboard_to_server(test_content)

        # Verify WebSocket send was called with correct format
        expected_message = f"clipboard_update:{test_content}"
        mock_ws.send.assert_called_once_with(expected_message)
        assert result is True

    def test_send_clipboard_to_server_no_connection(self):
        """Test clipboard sending when no WebSocket connection exists."""
        import client

        # Clear any existing connection
        client.ws_connection = None
        client.pending_clipboard_updates = []  # Reset pending updates

        test_content = "test clipboard content"
        result = client.send_clipboard_to_server(test_content)

        # Should add to pending queue
        assert result is False
        assert len(client.pending_clipboard_updates) == 1
        assert client.pending_clipboard_updates[0] == test_content

    def test_send_clipboard_to_server_disconnected_websocket(self):
        """Test clipboard sending when WebSocket is disconnected."""
        import client

        # Mock disconnected WebSocket
        mock_ws = MagicMock()
        mock_ws.sock = MagicMock()
        mock_ws.sock.connected = False
        client.ws_connection = mock_ws
        client.pending_clipboard_updates = []  # Reset pending updates

        test_content = "test clipboard content"
        result = client.send_clipboard_to_server(test_content)

        # Should add to pending queue
        assert result is False
        assert len(client.pending_clipboard_updates) == 1
        assert client.pending_clipboard_updates[0] == test_content

    def test_send_clipboard_to_server_websocket_exception(self):
        """Test clipboard sending with WebSocket exception."""
        import client

        # Mock WebSocket that raises exception on send
        mock_ws = MagicMock()
        mock_ws.sock = MagicMock()
        mock_ws.sock.connected = True
        mock_ws.send.side_effect = Exception("WebSocket error")

        client.ws_connection = mock_ws
        client.pending_clipboard_updates = []  # Reset pending updates

        test_content = "test clipboard content"
        result = client.send_clipboard_to_server(test_content)

        # Should handle exception and add to pending queue
        assert result is False
        assert len(client.pending_clipboard_updates) == 1
        assert client.pending_clipboard_updates[0] == test_content

    def test_pending_clipboard_updates_limit(self):
        """Test that pending clipboard updates are limited to 10 items."""
        import client

        client.ws_connection = None
        client.pending_clipboard_updates = []  # Reset pending updates

        # Add 15 items to exceed the limit
        for i in range(15):
            client.send_clipboard_to_server(f"test content {i}")

        # Should only keep the latest 10
        assert len(client.pending_clipboard_updates) == 10
        # Should contain items 5-14 (latest 10)
        assert client.pending_clipboard_updates[0] == "test content 5"
        assert client.pending_clipboard_updates[-1] == "test content 14"

    def test_module_constants(self):
        """Test that module constants are properly defined."""
        assert hasattr(client, "SERVER_HOST")
        assert hasattr(client, "SERVER_PORT")
        assert hasattr(client, "SERVER_URL")

        # Verify URL format
        assert client.SERVER_URL.startswith("ws://")
        assert "/ws" in client.SERVER_URL

    def test_logger_configuration(self):
        """Test that loggers are properly configured."""
        # Verify logger exists
        assert client.logger is not None

        # Verify UI logger exists
        assert client.ui_logger is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
