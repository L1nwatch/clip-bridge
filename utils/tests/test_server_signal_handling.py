#!/usr/bin/env python3
"""
Tests for server signal handling and graceful shutdown functionality.
"""

import pytest
import sys
import os
import signal
from unittest.mock import patch, MagicMock

# Add parent directory to path to import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import server


class TestServerSignalHandling:
    """Test cases for server signal handling and graceful shutdown."""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Set up test environment before each test."""
        # Reset global variables
        server.running = True
        server.websocket_clients.clear()

    def teardown_method(self):
        """Clean up after each test."""
        server.running = False
        server.websocket_clients.clear()

    def test_signal_handler_sets_running_false(self):
        """Test that signal handler sets running to False."""
        with patch("sys.exit") as mock_exit:
            with patch("time.sleep"):
                # Call signal handler
                server.signal_handler(signal.SIGTERM, None)

                # Verify running is set to False
                assert server.running is False
                mock_exit.assert_called_once_with(0)

    def test_signal_handler_closes_websocket_clients(self):
        """Test that signal handler closes all WebSocket clients."""
        # Create mock WebSocket clients
        mock_client1 = MagicMock()
        mock_client2 = MagicMock()
        server.websocket_clients.add(mock_client1)
        server.websocket_clients.add(mock_client2)

        with patch("sys.exit"):
            with patch("time.sleep"):
                # Call signal handler
                server.signal_handler(signal.SIGINT, None)

                # Verify all clients were closed
                mock_client1.close.assert_called_once()
                mock_client2.close.assert_called_once()
                assert len(server.websocket_clients) == 0

    def test_signal_handler_handles_websocket_close_error(self):
        """Test that signal handler handles WebSocket close errors gracefully."""
        # Create a mock WebSocket that raises an error on close
        mock_client = MagicMock()
        mock_client.close.side_effect = Exception("Connection already closed")
        server.websocket_clients.add(mock_client)

        with patch("sys.exit"):
            with patch("time.sleep"):
                # Should not raise an exception
                server.signal_handler(signal.SIGTERM, None)

                # Verify close was attempted and clients cleared
                mock_client.close.assert_called_once()
                assert len(server.websocket_clients) == 0

    def test_cleanup_on_exit_sets_running_false(self):
        """Test that cleanup function sets running to False."""
        server.running = True
        server.cleanup_on_exit()
        assert server.running is False

    @patch("signal.signal")
    def test_signal_handlers_are_registered(self, mock_signal):
        """Test that signal handlers are properly registered."""
        # Import the module to trigger signal registration
        import importlib

        importlib.reload(server)

        # Verify signal handlers were registered
        expected_calls = [
            ((signal.SIGINT, server.signal_handler),),
            ((signal.SIGTERM, server.signal_handler),),
        ]

        # Check if SIGHUP is available (Unix systems)
        if hasattr(signal, "SIGHUP"):
            expected_calls.append(((signal.SIGHUP, server.signal_handler),))

        # Verify the calls were made
        for expected_call in expected_calls:
            assert expected_call in mock_signal.call_args_list

    @patch("atexit.register")
    def test_atexit_cleanup_registered(self, mock_atexit):
        """Test that atexit cleanup function is registered."""
        # Import the module to trigger atexit registration
        import importlib

        importlib.reload(server)

        # Verify atexit.register was called with cleanup function
        mock_atexit.assert_called_with(server.cleanup_on_exit)

    def test_monitor_mac_clipboard_respects_running_flag(self):
        """Test that clipboard monitor stops when running is False."""
        server.running = False

        # Mock get_clipboard to return some data initially
        with patch("server.get_clipboard") as mock_get_clipboard:
            mock_clipboard_data = MagicMock()
            mock_clipboard_data.to_json.return_value = '{"test": "data"}'
            mock_clipboard_data.data_type = "text"
            mock_clipboard_data.content = "test content"
            mock_get_clipboard.return_value = mock_clipboard_data

            # Mock notify_clients to track if it gets called
            with patch("server.notify_clients") as mock_notify:
                # Call monitor function - it should exit immediately
                server.monitor_mac_clipboard()

                # Since running=False, the loop should not run
                # and notify_clients should not be called
                mock_notify.assert_not_called()

    def test_monitor_mac_clipboard_loop_with_running_true(self):
        """Test that clipboard monitor runs when running is True."""
        server.running = True

        with patch("server.get_clipboard") as mock_get_clipboard:
            with patch("server.notify_clients") as mock_notify:
                with patch("time.sleep") as mock_sleep:
                    # Mock clipboard data - make initial and current different 
                    # to trigger notify_clients
                    mock_initial_data = MagicMock()
                    mock_initial_data.to_json.return_value = '{"test": "initial"}'
                    mock_initial_data.data_type = "text"
                    mock_initial_data.content = "initial content"
                    
                    mock_current_data = MagicMock()
                    mock_current_data.to_json.return_value = '{"test": "changed"}'
                    mock_current_data.data_type = "text"
                    mock_current_data.content = "changed content"
                    
                    # Return initial data first, then changed data
                    mock_get_clipboard.side_effect = [mock_initial_data, mock_current_data]

                    # Set up the loop to run only once by changing running to False after sleep
                    def set_running_false(*args):
                        server.running = False

                    mock_sleep.side_effect = set_running_false

                    # Call monitor function
                    server.monitor_mac_clipboard()

                    # Verify it tried to get clipboard content and called sleep
                    assert mock_get_clipboard.call_count == 2  # Initial + loop check
                    mock_sleep.assert_called_once_with(1)
                    # Verify notify_clients was called when clipboard changed
                    mock_notify.assert_called()


class TestServerGracefulShutdown:
    """Integration tests for server graceful shutdown process."""

    def test_signal_handler_integration(self):
        """Test the complete signal handling flow."""
        # Set up mock clients
        mock_client1 = MagicMock()
        mock_client2 = MagicMock()
        server.websocket_clients.add(mock_client1)
        server.websocket_clients.add(mock_client2)
        server.running = True

        with patch("sys.exit") as mock_exit:
            with patch("time.sleep") as mock_sleep:
                # Simulate receiving SIGTERM
                server.signal_handler(signal.SIGTERM, None)

                # Verify the complete flow
                assert server.running is False
                mock_client1.close.assert_called_once()
                mock_client2.close.assert_called_once()
                assert len(server.websocket_clients) == 0
                mock_sleep.assert_called_once_with(1)  # Give threads time to cleanup
                mock_exit.assert_called_once_with(0)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
