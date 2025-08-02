#!/usr/bin/env python3
"""
Tests for client signal handling and graceful shutdown functionality.
"""

import pytest
import sys
import os
import time
import signal
import threading
from unittest.mock import patch, MagicMock

# Add parent directory to path to import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import client


class TestSignalHandling:
    """Test cases for signal handling and graceful shutdown."""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Set up test environment before each test."""
        # Reset global variables
        client.running = True
        client.ws_connection_global = None

    def teardown_method(self):
        """Clean up after each test."""
        client.running = False
        client.ws_connection_global = None

    def test_signal_handler_sets_running_false(self):
        """Test that signal handler sets running to False."""
        # Mock sys.exit to prevent actual exit during test
        with patch("sys.exit") as mock_exit:
            with patch("time.sleep"):  # Mock sleep to speed up test
                # Call signal handler
                client.signal_handler(signal.SIGTERM, None)

                # Verify running is set to False
                assert client.running is False
                mock_exit.assert_called_once_with(0)

    def test_signal_handler_closes_websocket(self):
        """Test that signal handler closes WebSocket connection."""
        # Create a mock WebSocket
        mock_ws = MagicMock()
        client.ws_connection_global = mock_ws

        with patch("sys.exit"):
            with patch("time.sleep"):
                # Call signal handler
                client.signal_handler(signal.SIGINT, None)

                # Verify WebSocket close was called
                mock_ws.close.assert_called_once()

    def test_signal_handler_handles_websocket_close_error(self):
        """Test that signal handler handles WebSocket close errors gracefully."""
        # Create a mock WebSocket that raises an error on close
        mock_ws = MagicMock()
        mock_ws.close.side_effect = Exception("Connection already closed")
        client.ws_connection_global = mock_ws

        with patch("sys.exit"):
            with patch("time.sleep"):
                # Should not raise an exception
                client.signal_handler(signal.SIGTERM, None)

                # Verify close was attempted
                mock_ws.close.assert_called_once()

    def test_cleanup_on_exit_sets_running_false(self):
        """Test that cleanup function sets running to False."""
        client.running = True
        client.cleanup_on_exit()
        assert client.running is False

    @patch("signal.signal")
    def test_signal_handlers_are_registered(self, mock_signal):
        """Test that signal handlers are properly registered."""
        # Import the module to trigger signal registration
        import importlib

        importlib.reload(client)

        # Verify signal handlers were registered
        expected_calls = [
            ((signal.SIGINT, client.signal_handler),),
            ((signal.SIGTERM, client.signal_handler),),
        ]

        # Check if SIGHUP is available (Unix systems)
        if hasattr(signal, "SIGHUP"):
            expected_calls.append(((signal.SIGHUP, client.signal_handler),))

        # Verify the calls were made
        for expected_call in expected_calls:
            assert expected_call in mock_signal.call_args_list

    def test_ws_connection_global_updated_in_on_open(self):
        """Test that global WebSocket reference is set in on_open."""
        mock_ws = MagicMock()

        # Call on_open
        client.on_open(mock_ws)

        # Verify global reference is set
        assert client.ws_connection_global is mock_ws
        assert client.ws_connection is mock_ws

    def test_ws_connection_global_cleared_in_on_close(self):
        """Test that global WebSocket reference is cleared in on_close."""
        # Set up initial state
        mock_ws = MagicMock()
        client.ws_connection_global = mock_ws
        client.running = True

        # Call on_close
        client.on_close(mock_ws, 1000, "Normal closure")

        # Verify global reference is cleared and running is set to False
        assert client.ws_connection_global is None
        assert client.running is False

    @patch("atexit.register")
    def test_atexit_cleanup_registered(self, mock_atexit):
        """Test that atexit cleanup function is registered."""
        # Import the module to trigger atexit registration
        import importlib

        importlib.reload(client)

        # Verify atexit.register was called with cleanup function
        mock_atexit.assert_called_with(client.cleanup_on_exit)


class TestGracefulShutdown:
    """Integration tests for graceful shutdown process."""

    def test_signal_handler_integration(self):
        """Test the complete signal handling flow."""
        mock_ws = MagicMock()
        client.ws_connection_global = mock_ws
        client.running = True

        with patch("sys.exit") as mock_exit:
            with patch("time.sleep") as mock_sleep:
                # Simulate receiving SIGTERM
                client.signal_handler(signal.SIGTERM, None)

                # Verify the complete flow
                assert client.running is False
                mock_ws.close.assert_called_once()
                mock_sleep.assert_called_once_with(1)  # Give threads time to cleanup
                mock_exit.assert_called_once_with(0)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
