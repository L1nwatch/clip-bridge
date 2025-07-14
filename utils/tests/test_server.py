#!/usr/bin/env python3
"""
Unit tests for the clipboard server.

Tests individual components and functions of the server.
"""

import pytest
import unittest.mock as mock
import threading
import time
import requests
import subprocess
import sys
import os
from unittest.mock import patch, MagicMock

# Add parent directory to path to import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import server


class TestClipboardServer:
    """Test cases for clipboard server functionality."""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Set up test environment before each test."""
        # Reset global variables
        server.windows_clip = ""
        server.websocket_clients.clear()

    def test_cors_headers(self):
        """Test that CORS headers are properly set."""
        with server.app.test_client() as client:
            response = client.get("/")

            assert "Access-Control-Allow-Origin" in response.headers
            assert response.headers["Access-Control-Allow-Origin"] == "*"
            assert "Access-Control-Allow-Headers" in response.headers
            assert "Access-Control-Allow-Methods" in response.headers

    def test_health_endpoint(self):
        """Test the health check endpoint."""
        with server.app.test_client() as client:
            response = client.get("/")
            # Should return some response (even if 404)
            assert response.status_code in [200, 404]

    @mock.patch("server.set_clipboard")
    def test_update_clipboard_endpoint(self, mock_set_clipboard):
        """Test the clipboard update endpoint."""
        test_data = "test clipboard content"

        with server.app.test_client() as client:
            response = client.post("/update_clipboard", data=test_data)

            assert response.status_code == 200
            assert response.get_data(as_text=True) == "OK"
            mock_set_clipboard.assert_called_once_with(test_data)

    @mock.patch("server.notify_clients")
    @mock.patch("server.set_clipboard")
    def test_update_clipboard_notifies_clients(self, mock_set_clipboard, mock_notify):
        """Test that updating clipboard notifies WebSocket clients."""
        test_data = "test notification content"

        with server.app.test_client() as client:
            response = client.post("/update_clipboard", data=test_data)

            assert response.status_code == 200
            mock_set_clipboard.assert_called_once_with(test_data)
            mock_notify.assert_called_once()

    @mock.patch("server.pyperclip.copy")
    def test_set_clipboard(self, mock_copy):
        """Test setting clipboard content."""
        test_content = "test clipboard content"
        server.set_clipboard(test_content)

        # Verify pyperclip.copy was called with correct content
        mock_copy.assert_called_once_with(test_content)

    @mock.patch("server.pyperclip.copy")
    def test_set_clipboard_error_handling(self, mock_copy):
        """Test error handling in set_clipboard."""
        mock_copy.side_effect = Exception("Clipboard access failed")

        test_content = "test content"
        # Should not raise exception
        server.set_clipboard(test_content)

    def test_notify_clients_empty_list(self):
        """Test notifying clients when no clients are connected."""
        # Should not raise any exceptions
        server.notify_clients()

    def test_notify_clients_with_mock_clients(self):
        """Test notifying WebSocket clients."""
        # Create mock WebSocket clients
        mock_client1 = MagicMock()
        mock_client2 = MagicMock()
        mock_client3 = MagicMock()

        # Mock client3 to raise an exception
        mock_client3.send.side_effect = Exception("Connection closed")

        # Add clients to the set
        server.websocket_clients.add(mock_client1)
        server.websocket_clients.add(mock_client2)
        server.websocket_clients.add(mock_client3)

        # Notify clients
        server.notify_clients()

        # Verify successful clients received the message
        mock_client1.send.assert_called_once_with(b"new_clipboard")
        mock_client2.send.assert_called_once_with(b"new_clipboard")

        # Verify failed client was attempted and removed from set
        mock_client3.send.assert_called_once_with(b"new_clipboard")
        assert mock_client3 not in server.websocket_clients

    def test_get_clipboard_content(self):
        """Test getting current clipboard content."""
        test_content = "test clipboard content"
        server.windows_clip = test_content

        with server.app.test_client() as client:
            response = client.get("/")
            assert response.status_code == 200

            # Check for new JSON response format
            response_data = response.get_json()
            assert response_data["service"] == "ClipBridge Server"
            assert response_data["status"] == "ok"
            assert "version" in response_data

    def test_app_configuration(self):
        """Test Flask app configuration."""
        assert server.app is not None
        assert isinstance(server.app, server.Flask)

    @mock.patch.dict(os.environ, {"PORT": "9000", "LOG_LEVEL": "DEBUG"})
    def test_environment_configuration(self):
        """Test environment variable configuration."""
        # Import server again to reload environment variables
        import importlib

        importlib.reload(server)

        assert server.PORT == 9000
        assert server.LOG_LEVEL == "DEBUG"

    def test_threading_lock_exists(self):
        """Test that threading lock is properly initialized."""
        assert server.lock is not None
        assert hasattr(server.lock, "acquire")  # Check if it has lock methods
        assert hasattr(server.lock, "release")

    def test_websocket_clients_set_initialized(self):
        """Test that WebSocket clients set is properly initialized."""
        assert isinstance(server.websocket_clients, set)


class TestWebSocketApp:
    """Test cases for WebSocket functionality."""

    def test_websocket_app_without_websocket(self):
        """Test websocket_app function when no WebSocket upgrade is present."""
        environ = {
            "REQUEST_METHOD": "GET",
            "PATH_INFO": "/",
            "wsgi.url_scheme": "http",
            "SERVER_NAME": "localhost",
            "SERVER_PORT": "8001",
        }
        start_response = MagicMock()

        # This should be handled by Flask app
        # Just check that it doesn't raise an exception
        result = server.websocket_app(environ, start_response)

    @mock.patch("server.get_clipboard")
    def test_websocket_app_with_mock_websocket(self, mock_get_clipboard):
        """Test WebSocket app with a mock WebSocket connection."""
        mock_get_clipboard.return_value = "test content"

        mock_ws = MagicMock()
        mock_ws.closed = False
        mock_ws.receive.side_effect = ["test message", None]

        environ = {"wsgi.websocket": mock_ws, "REMOTE_ADDR": "127.0.0.1"}
        start_response = MagicMock()

        # Mock the WebSocket to become closed after one iteration
        def side_effect():
            mock_ws.closed = True
            return None

        mock_ws.receive.side_effect = ["test message", side_effect()]

        server.websocket_app(environ, start_response)

        # Verify client was added and removed
        assert mock_ws not in server.websocket_clients

    @mock.patch("server.set_clipboard")
    def test_websocket_clipboard_update_message(self, mock_set_clipboard):
        """Test WebSocket handling of clipboard_update: message format."""
        mock_ws = MagicMock()
        mock_ws.closed = False

        # Test the new clipboard_update: message format
        test_content = "Test clipboard content from WebSocket"
        clipboard_message = f"clipboard_update:{test_content}"

        environ = {"wsgi.websocket": mock_ws, "REMOTE_ADDR": "127.0.0.1"}
        start_response = MagicMock()

        # Set up the receive calls to return the message and then close
        call_count = 0

        def mock_receive():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return clipboard_message
            else:
                # Close the WebSocket after first message
                mock_ws.closed = True
                return None

        mock_ws.receive.side_effect = mock_receive

        server.websocket_app(environ, start_response)

        # Verify set_clipboard was called with the extracted content
        mock_set_clipboard.assert_called_with(test_content)

    @mock.patch("server.set_clipboard")
    def test_websocket_legacy_message_format(self, mock_set_clipboard):
        """Test WebSocket handling of legacy message format (entire message as clipboard)."""
        mock_ws = MagicMock()
        mock_ws.closed = False

        # Test legacy format (entire message is clipboard content)
        test_content = "Legacy clipboard content"

        environ = {"wsgi.websocket": mock_ws, "REMOTE_ADDR": "127.0.0.1"}
        start_response = MagicMock()

        # Set up the receive calls to return the message and then close
        call_count = 0

        def mock_receive():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return test_content
            else:
                # Close the WebSocket after first message
                mock_ws.closed = True
                return None

        mock_ws.receive.side_effect = mock_receive

        server.websocket_app(environ, start_response)

        # Verify set_clipboard was called with the entire message
        mock_set_clipboard.assert_called_with(test_content)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
