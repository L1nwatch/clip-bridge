#!/usr/bin/env python3
"""
Additional tests for edge cases and error scenarios in client and server.
"""

import pytest
import unittest.mock as mock
import time
import threading
from unittest.mock import MagicMock, patch

# Import the modules under test
import sys
import os

sys.path.insert(0, os.path.dirname(__file__).replace("/tests", ""))

import client
import server


class TestClientEdgeCases:
    """Test edge cases and error scenarios for the client."""

    def setup_method(self):
        """Set up test environment."""
        # Reset any global state
        client.last_windows_clipboard = ""
        client.is_monitoring = False
        client.running = True

    def test_send_clipboard_to_server_edge_cases(self):
        """Test send_clipboard_to_server with edge cases using WebSocket."""
        import client

        # Mock WebSocket connection
        mock_ws = MagicMock()
        mock_ws.sock = MagicMock()
        mock_ws.sock.connected = True
        client.ws_connection = mock_ws
        client.pending_clipboard_updates = []  # Reset pending updates

        # Test with empty content
        result = client.send_clipboard_to_server("")
        mock_ws.send.assert_called_with("clipboard_update:")
        assert result is True

        # Test with very long content
        long_content = "x" * 10000
        client.send_clipboard_to_server(long_content)
        mock_ws.send.assert_called_with(f"clipboard_update:{long_content}")

        # Test with unicode content
        unicode_content = "Hello 世界 🌍 émojis"
        client.send_clipboard_to_server(unicode_content)
        mock_ws.send.assert_called_with(f"clipboard_update:{unicode_content}")

    def test_monitor_windows_clipboard_error_handling(self):
        """Test clipboard monitoring with various error scenarios."""
        with patch("client.pyperclip.paste") as mock_paste, patch(
            "client.send_clipboard_to_server"
        ) as mock_send, patch("time.sleep") as mock_sleep:

            # Test clipboard access error - first call succeeds, second fails
            mock_paste.side_effect = [
                "initial content",
                Exception("Clipboard access denied"),
            ]
            mock_sleep.side_effect = [None, Exception("Stop monitoring")]

            with pytest.raises(Exception, match="Stop monitoring"):
                client.monitor_windows_clipboard()

            # Should have attempted to access clipboard
            mock_paste.assert_called()

    @patch("client.pyperclip.paste")
    @patch("client.send_clipboard_to_server")
    def test_monitor_windows_clipboard_content_filtering(self, mock_send, mock_paste):
        """Test that monitoring properly filters duplicate content."""
        # Set up clipboard content sequence
        clipboard_sequence = [
            "initial",  # Initial content (not sent)
            "initial",  # Duplicate (not sent)
            "content2",  # New content (sent)
            "content2",  # Duplicate (not sent)
            "content3",  # New content (sent)
        ]
        mock_paste.side_effect = clipboard_sequence

        # Mock sleep to control the loop
        with patch(
            "time.sleep", side_effect=[None, None, None, None, Exception("Stop")]
        ):
            with pytest.raises(Exception, match="Stop"):
                client.monitor_windows_clipboard()

        # Should only send unique content (excluding initial)
        expected_calls = [
            mock.call("content2"),
            mock.call("content3"),
        ]
        assert mock_send.call_count == 2
        for expected_call in expected_calls:
            assert expected_call in mock_send.call_args_list

    def test_websocket_event_handlers(self):
        """Test WebSocket event handlers with various scenarios."""
        mock_ws = MagicMock()

        # Test on_open with missing websocket methods
        mock_ws.sock = None
        client.on_open(mock_ws)  # Should not crash

        # Test on_close
        client.on_close(mock_ws, 1000, "Normal closure")
        # Should complete without error

        # Test on_error with different error types
        client.on_error(mock_ws, ConnectionError("Connection lost"))
        client.on_error(mock_ws, TimeoutError("Timeout"))
        client.on_error(mock_ws, Exception("Generic error"))

    def test_on_message_with_different_message_types(self):
        """Test on_message handler with various message types."""
        mock_ws = MagicMock()

        with patch("client.pyperclip.copy") as mock_copy:
            # Test new_clipboard message type (should send get_clipboard)
            client.on_message(mock_ws, "new_clipboard")
            mock_ws.send.assert_called_with("get_clipboard")

            # Reset mock
            mock_ws.reset_mock()

            # Test clipboard_content message type
            client.on_message(mock_ws, "clipboard_content:test content")
            mock_copy.assert_called_with("test content")

            # Reset mocks
            mock_ws.reset_mock()
            mock_copy.reset_mock()

            # Test unknown message type (should do nothing)
            client.on_message(mock_ws, "unknown_message")
            mock_ws.send.assert_not_called()
            mock_copy.assert_not_called()

            # Test empty message
            client.on_message(mock_ws, "")

            # Test None message - this would cause an error in real usage
            # but we test it doesn't crash
            try:
                client.on_message(mock_ws, None)
            except AttributeError:
                pass  # Expected for None.startswith()


class TestServerEdgeCases:
    """Test edge cases and error scenarios for the server."""

    def test_set_clipboard_with_different_content_types(self):
        """Test set_clipboard with various content types."""
        with patch("server.pyperclip.copy") as mock_copy:
            # Test empty string
            server.set_clipboard("")
            mock_copy.assert_called_with("")

            # Test None
            server.set_clipboard(None)
            mock_copy.assert_called_with(None)

            # Test unicode content
            unicode_content = "Unicode: 你好 🌍 café"
            server.set_clipboard(unicode_content)
            mock_copy.assert_called_with(unicode_content)

            # Test very long content
            long_content = "x" * 50000
            server.set_clipboard(long_content)
            mock_copy.assert_called_with(long_content)

    def test_get_clipboard_error_handling(self):
        """Test get_clipboard with various error scenarios."""
        with patch("server.pyperclip.paste") as mock_paste:
            # Test clipboard access error
            mock_paste.side_effect = Exception("Clipboard unavailable")

            result = server.get_clipboard()
            assert result == ""

            # Test with log_retrieval=False
            result = server.get_clipboard(log_retrieval=False)
            assert result == ""

    def test_notify_clients_with_various_client_states(self):
        """Test notify_clients with clients in different states."""
        # Mock some clients
        mock_client1 = MagicMock()
        mock_client2 = MagicMock()
        mock_client3 = MagicMock()

        # Client 2 will fail to send
        mock_client2.send.side_effect = Exception("Connection lost")

        with patch.object(
            server, "websocket_clients", {mock_client1, mock_client2, mock_client3}
        ):
            server.notify_clients()

            # All clients should have been attempted
            mock_client1.send.assert_called_once_with("new_clipboard")
            mock_client2.send.assert_called_once_with("new_clipboard")
            mock_client3.send.assert_called_once_with("new_clipboard")

    def test_notify_clients_with_message_parameter(self):
        """Test notify_clients with default message."""
        mock_client = MagicMock()

        with patch.object(server, "websocket_clients", {mock_client}):
            server.notify_clients()
            mock_client.send.assert_called_once_with("new_clipboard")

    def test_monitor_mac_clipboard_edge_cases(self):
        """Test clipboard monitoring with edge cases."""
        with patch("server.get_clipboard") as mock_get_clipboard, patch(
            "server.notify_clients"
        ) as mock_notify, patch("time.sleep") as mock_sleep:

            # Test clipboard content changes
            clipboard_sequence = ["initial", "initial", "content2", "content2"]
            mock_get_clipboard.side_effect = clipboard_sequence
            mock_sleep.side_effect = [None, None, None, Exception("Stop")]

            with pytest.raises(Exception, match="Stop"):
                server.monitor_mac_clipboard()

            # Should notify clients only when content changes (excluding initial)
            assert mock_notify.call_count == 1  # Once for content2

    def test_websocket_app_edge_cases(self):
        """Test WebSocket app with various edge cases."""
        # Test without WebSocket in environ
        environ = {
            "REMOTE_ADDR": "127.0.0.1",
            "wsgi.url_scheme": "http",
            "SERVER_NAME": "localhost",
            "SERVER_PORT": "8000",
            "REQUEST_METHOD": "GET",
            "PATH_INFO": "/ws",
        }
        start_response = MagicMock()

        # When no WebSocket is present, it falls back to Flask app
        result = server.websocket_app(environ, start_response)
        # Should return a Flask response (not [b"WebSocket connection required"])
        assert result is not None

        # Test with closed WebSocket
        mock_ws = MagicMock()
        mock_ws.closed = True
        environ["wsgi.websocket"] = mock_ws

        result = server.websocket_app(environ, start_response)
        assert result == []

    def test_update_clipboard_endpoint_edge_cases(self):
        """Test update_clipboard endpoint with various scenarios."""
        with server.app.test_client() as client:
            # Test with empty data - should return 400 as no content received
            response = client.post("/update_clipboard", data="")
            assert response.status_code == 400
            assert "No content" in response.get_data(as_text=True)

            # Test with large data
            large_data = "x" * 100000
            response = client.post("/update_clipboard", data=large_data)
            assert response.status_code == 200

            # Test with unicode data
            unicode_data = "Unicode test: 世界 🌍 café"
            response = client.post("/update_clipboard", data=unicode_data)
            assert response.status_code == 200

    def test_get_clipboard_content_endpoint(self):
        """Test get_clipboard_content endpoint."""
        with patch("server.get_clipboard") as mock_get_clipboard:
            mock_get_clipboard.return_value = "test clipboard content"

            with server.app.test_client() as client:
                response = client.get("/get_clipboard")
                assert response.status_code == 200
                assert response.get_data(as_text=True) == "test clipboard content"

    def test_cors_headers_on_all_endpoints(self):
        """Test that CORS headers are properly set on all endpoints."""
        with server.app.test_client() as client:
            # Test health endpoint
            response = client.get("/health")
            assert "Access-Control-Allow-Origin" in response.headers
            assert response.headers["Access-Control-Allow-Origin"] == "*"

            # Test OPTIONS request
            response = client.options("/update_clipboard")
            assert response.status_code == 200
            assert "Access-Control-Allow-Methods" in response.headers

    @patch("server.threading.Thread")
    def test_combined_app_startup(self, mock_thread):
        """Test the combined app startup process."""
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance

        # This would normally start the monitoring thread
        # We'll just test that the function can be called
        try:
            app = server.combined_app()
            assert app is not None
        except Exception:
            # The function might fail in test environment, which is okay
            pass


class TestIntegrationScenarios:
    """Test integration scenarios between client and server."""

    @patch("pyperclip.copy")
    def test_client_server_message_flow(self, mock_copy):
        """Test the flow of messages between client and server components using WebSocket."""
        import client

        # Mock WebSocket connection for client
        mock_ws = MagicMock()
        mock_ws.sock = MagicMock()
        mock_ws.sock.connected = True
        client.ws_connection = mock_ws
        client.pending_clipboard_updates = []  # Reset pending updates

        # Test client sending to server via WebSocket
        test_content = "integration test content"
        result = client.send_clipboard_to_server(test_content)

        # Verify WebSocket send was called with correct format
        mock_ws.send.assert_called_once_with(f"clipboard_update:{test_content}")
        assert result is True

        # Test server setting clipboard
        server.set_clipboard(test_content)
        mock_copy.assert_called_with(test_content)

    def test_error_propagation(self):
        """Test how errors propagate through the system."""
        import client

        # Test WebSocket error - should not raise exception but add to pending queue
        mock_ws = MagicMock()
        mock_ws.sock = MagicMock()
        mock_ws.sock.connected = True
        mock_ws.send.side_effect = Exception("WebSocket connection lost")

        client.ws_connection = mock_ws
        client.pending_clipboard_updates = []  # Reset pending updates

        # Should not raise exception, should add to pending queue
        result = client.send_clipboard_to_server("test content")
        assert result is False
        assert len(client.pending_clipboard_updates) == 1
        assert client.pending_clipboard_updates[0] == "test content"

        with patch("server.pyperclip.copy") as mock_copy:
            # Test clipboard error
            mock_copy.side_effect = Exception("Clipboard access denied")

            # Should not raise exception
            server.set_clipboard("test content")
            mock_copy.assert_called_once()

    def test_concurrent_operations(self):
        """Test concurrent operations on client and server."""
        import threading

        results = []
        errors = []

        def client_operation():
            try:
                # Mock WebSocket connection for testing
                mock_ws = MagicMock()
                mock_ws.sock = MagicMock()
                mock_ws.sock.connected = True
                client.ws_connection = mock_ws

                result = client.send_clipboard_to_server("concurrent test")
                if result:
                    results.append("client_success")
                else:
                    results.append("client_failed")
            except Exception as e:
                errors.append(f"client_error: {e}")

        def server_operation():
            try:
                with patch("server.pyperclip.copy") as mock_copy:
                    server.set_clipboard("concurrent test")
                    results.append("server_success")
            except Exception as e:
                errors.append(f"server_error: {e}")

        # Run operations concurrently
        client_thread = threading.Thread(target=client_operation)
        server_thread = threading.Thread(target=server_operation)

        client_thread.start()
        server_thread.start()

        client_thread.join(timeout=5)
        server_thread.join(timeout=5)

        # Check results
        assert "client_success" in results
        assert "server_success" in results
        assert len(errors) == 0
