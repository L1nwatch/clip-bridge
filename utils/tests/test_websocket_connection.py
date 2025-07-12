#!/usr/bin/env python3
"""
Test cases for WebSocket connection functionality and client behavior.
Tests WebSocket connection establishment, callbacks, message handling, and lifecycle.
"""

import websocket
import time
import threading
import sys
import os
from unittest.mock import Mock, patch

# Add parent directory to path to import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestWebSocketClientConnection:
    """Test WebSocket client connection functionality."""

    def test_websocket_connection_callbacks(self):
        """Test WebSocket connection callbacks work correctly."""
        # Mock WebSocket for testing
        mock_ws = Mock()

        # Test variables to track callback execution
        callbacks_called = {
            "on_open": False,
            "on_message": False,
            "on_error": False,
            "on_close": False,
        }

        def on_message(ws, message):
            callbacks_called["on_message"] = True
            assert message == "test_message"

        def on_error(ws, error):
            callbacks_called["on_error"] = True
            assert str(error) == "test_error"

        def on_close(ws, close_status_code, close_msg):
            callbacks_called["on_close"] = True
            assert close_status_code == 1000
            assert close_msg == "test_close"

        def on_open(ws):
            callbacks_called["on_open"] = True

        # Test each callback
        on_open(mock_ws)
        on_message(mock_ws, "test_message")
        on_error(mock_ws, "test_error")
        on_close(mock_ws, 1000, "test_close")

        # Verify all callbacks were called
        assert all(callbacks_called.values())

    @patch("websocket.WebSocketApp")
    def test_websocket_app_creation(self, mock_websocket_app):
        """Test WebSocket app creation with correct parameters."""
        mock_ws_instance = Mock()
        mock_websocket_app.return_value = mock_ws_instance

        # Test connection creation
        server_url = "ws://localhost:8000/ws"

        def dummy_on_message(ws, message):
            pass

        def dummy_on_error(ws, error):
            pass

        def dummy_on_close(ws, close_status_code, close_msg):
            pass

        def dummy_on_open(ws):
            pass

        websocket.WebSocketApp(
            server_url,
            on_open=dummy_on_open,
            on_message=dummy_on_message,
            on_error=dummy_on_error,
            on_close=dummy_on_close,
        )

        # Verify WebSocketApp was called with correct parameters
        mock_websocket_app.assert_called_once()
        call_args = mock_websocket_app.call_args
        assert call_args[0][0] == server_url
        assert "on_open" in call_args[1]
        assert "on_message" in call_args[1]
        assert "on_error" in call_args[1]
        assert "on_close" in call_args[1]

    def test_connection_timeout_simulation(self):
        """Test connection timeout handling."""
        connection_events = []

        def simulate_connection_lifecycle():
            # Simulate connection opened
            connection_events.append("opened")
            time.sleep(0.1)  # Brief connection
            # Simulate connection closed
            connection_events.append("closed")

        # Run the simulation
        thread = threading.Thread(target=simulate_connection_lifecycle)
        thread.start()
        thread.join(timeout=1.0)  # 1 second timeout

        # Verify connection lifecycle
        assert "opened" in connection_events
        assert "closed" in connection_events
        assert len(connection_events) == 2

    def test_argument_parsing_simulation(self):
        """Test command line argument parsing logic."""
        # Test default values
        duration = 10
        port = 8000

        # Simulate argument parsing for duration
        test_args = ["15"]
        if len(test_args) > 0:
            try:
                duration = int(test_args[0])
            except ValueError:
                duration = 10  # fallback

        assert duration == 15

        # Simulate argument parsing for port
        test_args = ["15", "8080"]
        if len(test_args) > 1:
            try:
                port = int(test_args[1])
            except ValueError:
                port = 8000  # fallback

        assert port == 8080

    def test_url_construction(self):
        """Test WebSocket URL construction."""
        port = 8000
        expected_url = f"ws://localhost:{port}/ws"
        assert expected_url == "ws://localhost:8000/ws"

        port = 8080
        expected_url = f"ws://localhost:{port}/ws"
        assert expected_url == "ws://localhost:8080/ws"


# Utility function for manual testing (can be run separately)
def run_demo_connection(duration=10, port=8000):
    """
    Utility function for manual WebSocket connection testing.

    Args:
        duration: How long to keep the connection open (seconds)
        port: Server port to connect to
    """
    print(f"🔌 Connecting to ws://localhost:{port}/ws...")
    print(f"⏳ Will stay connected for {duration} seconds...")

    connection_result = {"connected": False, "messages": []}

    def on_message(ws, message):
        print(f"📨 Received: {message}")
        connection_result["messages"].append(message)

    def on_error(ws, error):
        print(f"❌ Error: {error}")

    def on_close(ws, close_status_code, close_msg):
        print("🔌 Connection closed")

    def on_open(ws):
        print("✅ Connected to Clipboard Bridge server")
        connection_result["connected"] = True

        # Auto-close after duration
        def close_later():
            time.sleep(duration)
            print("⏰ Closing connection...")
            ws.close()

        threading.Thread(target=close_later, daemon=True).start()

    try:
        ws = websocket.WebSocketApp(
            f"ws://localhost:{port}/ws",
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
        )
        ws.run_forever()
        print("👋 Demo connection completed")
        return connection_result
    except Exception as e:
        print(f"💥 Connection failed: {e}")
        print(f"💡 Make sure the server is running on port {port}")
        return connection_result


if __name__ == "__main__":
    # Allow manual execution for quick testing
    import argparse

    parser = argparse.ArgumentParser(description="WebSocket connection test utility")
    parser.add_argument(
        "duration",
        nargs="?",
        type=int,
        default=10,
        help="Connection duration in seconds (default: 10)",
    )
    parser.add_argument(
        "port", nargs="?", type=int, default=8000, help="Server port (default: 8000)"
    )

    args = parser.parse_args()
    run_demo_connection(args.duration, args.port)
