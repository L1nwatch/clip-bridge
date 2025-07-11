#!/usr/bin/env python3
"""
Unit tests for the clipboard server module.
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

    @mock.patch("server.get_mac_clipboard")
    def test_update_clipboard_endpoint(self, mock_get_clipboard):
        """Test the clipboard update endpoint."""
        mock_get_clipboard.return_value = "test clipboard content"

        with server.app.test_client() as client:
            response = client.post("/update_clipboard")

            assert response.status_code == 200
            assert response.get_data(as_text=True) == "OK"
            mock_get_clipboard.assert_called_once()

    @mock.patch("server.notify_clients")
    @mock.patch("server.get_mac_clipboard")
    def test_update_clipboard_notifies_clients(self, mock_get_clipboard, mock_notify):
        """Test that updating clipboard notifies WebSocket clients."""
        mock_get_clipboard.return_value = "test notification content"

        with server.app.test_client() as client:
            response = client.post("/update_clipboard")

            assert response.status_code == 200
            mock_get_clipboard.assert_called_once()
            mock_notify.assert_called_once()

    @mock.patch("subprocess.Popen")
    def test_set_mac_clipboard(self, mock_popen):
        """Test setting clipboard content on macOS."""
        mock_process = MagicMock()
        mock_popen.return_value = mock_process

        test_content = "test clipboard content"
        server.set_mac_clipboard(test_content)

        # Verify subprocess was called with correct parameters
        mock_popen.assert_called_once_with(["pbcopy"], stdin=subprocess.PIPE)
        mock_process.communicate.assert_called_once_with(test_content.encode())

    @mock.patch("subprocess.Popen")
    def test_set_mac_clipboard_error_handling(self, mock_popen):
        """Test error handling in set_mac_clipboard."""
        mock_popen.side_effect = Exception("Process failed")

        test_content = "test content"
        # Should not raise exception
        server.set_mac_clipboard(test_content)

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
        mock_client1.send.assert_called_once_with("new_clipboard")
        mock_client2.send.assert_called_once_with("new_clipboard")

        # Verify failed client was attempted and removed from set
        mock_client3.send.assert_called_once_with("new_clipboard")
        assert mock_client3 not in server.websocket_clients

    def test_get_clipboard_content(self):
        """Test getting current clipboard content."""
        test_content = "test clipboard content"
        server.windows_clip = test_content

        with server.app.test_client() as client:
            response = client.get("/")
            assert response.status_code == 200
            assert "Clipboard Bridge Server is running" in response.get_data(
                as_text=True
            )

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

    @mock.patch("server.get_mac_clipboard")
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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
