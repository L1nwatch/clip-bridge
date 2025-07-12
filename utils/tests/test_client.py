#!/usr/bin/env python3
"""
Unit tests for the clipboard client module.
Tests client functionality and server communication.
"""

import pytest
import unittest.mock as mock
import sys
import os
from unittest.mock import patch, MagicMock

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
        assert client.UPDATE_URL is not None

    @mock.patch.dict(os.environ, {"SERVER_HOST": "testhost", "SERVER_PORT": "9000"})
    def test_custom_environment_configuration(self):
        """Test custom environment variable configuration."""
        # Reload the module to pick up new environment variables
        import importlib

        importlib.reload(client)

        assert "testhost" in client.SERVER_URL
        assert "9000" in client.SERVER_URL
        assert "9000" in client.UPDATE_URL

    def test_on_message_callback(self):
        """Test WebSocket message callback."""
        mock_ws = MagicMock()

        with patch("client.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.text = "test clipboard content"
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            # Test the on_message function
            client.on_message(mock_ws, "new_clipboard")

            # Verify that a request was made to fetch clipboard
            mock_get.assert_called_once_with(client.GET_CLIPBOARD_URL, timeout=5)

    def test_on_message_with_exception(self):
        """Test WebSocket message callback with network exception."""
        mock_ws = MagicMock()

        with patch("client.requests.get") as mock_get:
            mock_get.side_effect = Exception("Network error")

            # Should not raise exception
            client.on_message(mock_ws, "new_clipboard")

            mock_get.assert_called_once_with(client.GET_CLIPBOARD_URL, timeout=5)

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

    @mock.patch("client.requests.post")
    def test_send_clipboard_to_server_success(self, mock_post):
        """Test successful clipboard sending."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        test_content = "test clipboard content"
        client.send_clipboard_to_server(test_content)

        mock_post.assert_called_once_with(
            client.UPDATE_URL, data=test_content, timeout=5
        )

    @mock.patch("client.requests.post")
    def test_send_clipboard_to_server_failure(self, mock_post):
        """Test clipboard sending with server error."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response

        test_content = "test clipboard content"
        client.send_clipboard_to_server(test_content)

        mock_post.assert_called_once_with(
            client.UPDATE_URL, data=test_content, timeout=5
        )

    @mock.patch("client.requests.post")
    def test_send_clipboard_to_server_exception(self, mock_post):
        """Test clipboard sending with network exception."""
        mock_post.side_effect = Exception("Network error")

        test_content = "test clipboard content"
        # Should not raise exception
        client.send_clipboard_to_server(test_content)

        mock_post.assert_called_once_with(
            client.UPDATE_URL, data=test_content, timeout=5
        )

    def test_module_constants(self):
        """Test that module constants are properly defined."""
        assert hasattr(client, "SERVER_HOST")
        assert hasattr(client, "SERVER_PORT")
        assert hasattr(client, "SERVER_URL")
        assert hasattr(client, "UPDATE_URL")

        # Verify URL format
        assert client.SERVER_URL.startswith("ws://")
        assert "/ws" in client.SERVER_URL
        assert client.UPDATE_URL.startswith("http://")
        assert "/update_clipboard" in client.UPDATE_URL

    def test_logger_configuration(self):
        """Test that loggers are properly configured."""
        # Verify logger exists
        assert client.logger is not None

        # Verify UI logger exists
        assert client.ui_logger is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
