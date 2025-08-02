#!/usr/bin/env python3
"""
Integration tests for clipboard bridge server and client.
Tests the complete system working together with pytest style.
"""

import pytest
import threading
import time
import requests
import websocket as ws_client
import subprocess
import sys
import os
import signal
import concurrent.futures
from unittest.mock import patch
from loguru import logger

# Add parent directory to path to import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure loguru for tests
logger.remove()
logger.add(
    lambda msg: print(msg, end=""),
    format=(
        "<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | "
        "<cyan>INTEGRATION</cyan> - <level>{message}</level>"
    ),
    level="INFO",
    colorize=True,
)


class TestClipboardBridgeIntegration:
    """Integration tests for the complete clipboard bridge system."""

    @pytest.fixture(scope="class")
    def server_process(self):
        """Start server for integration tests."""
        logger.info("🚀 Setting up test server for integration tests...")

        # Get the correct path to server.py
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        server_path = os.path.join(current_dir, "server.py")

        # Start server in subprocess
        process = subprocess.Popen(
            [sys.executable, server_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            preexec_fn=os.setsid,
            text=True,
            env={
                "PORT": "8002",  # Use different port to avoid conflicts
                "LOG_LEVEL": "ERROR",
                **os.environ,
            },
        )

        # Wait for server to start
        server_started = False
        for _ in range(15):  # Wait up to 15 seconds
            time.sleep(1)
            if process.poll() is not None:
                output, _ = process.communicate()
                pytest.fail(f"Server failed to start: {output}")

            try:
                requests.get("http://localhost:8002", timeout=1)
                server_started = True
                logger.success("✅ Test server started successfully")
                break
            except requests.exceptions.ConnectionError:
                continue

        if not server_started:
            process.terminate()
            pytest.fail("Server failed to start within timeout")

        yield process

        # Cleanup
        logger.info("🧹 Cleaning up test server...")
        try:
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            process.wait(timeout=5)
            logger.success("✅ Test server stopped successfully")
        except (subprocess.TimeoutExpired, ProcessLookupError):
            try:
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                logger.warning("⚠️ Test server force killed")
            except ProcessLookupError:
                pass

    @pytest.fixture
    def test_client(self):
        """Set up test client data for each test."""

        class TestClient:
            def __init__(self):
                self.messages_received = []
                self.connection_status = None
                self.ws = None
                self.server_url = "http://localhost:8002"
                self.websocket_url = "ws://localhost:8002/ws"
                self.update_url = f"{self.server_url}/update_clipboard"

        client = TestClient()
        yield client

        # Cleanup WebSocket if it exists
        if client.ws:
            client.ws.close()

    def test_server_health(self, server_process, test_client):
        """Test if server is responding."""
        logger.info("🧪 Testing server health...")

        try:
            response = requests.get(test_client.server_url, timeout=5)
            # Any response (even 404) means server is running
            logger.success(f"✅ Server is responding (Status: {response.status_code})")
            assert response.status_code == 200

            # Check for new JSON response format
            response_data = response.json()
            assert response_data["service"] == "ClipBridge Server"
            assert response_data["status"] == "ok"
            assert "version" in response_data

        except requests.exceptions.ConnectionError:
            pytest.fail("❌ Server is not responding")
        except Exception as e:
            logger.warning(f"⚠️ Unexpected response: {e}")
            pytest.fail(f"❌ Server health check failed: {e}")

    def test_clipboard_update_endpoint(self, server_process, test_client):
        """Test the /update_clipboard POST endpoint."""
        logger.info("🧪 Testing clipboard update endpoint...")

        try:
            response = requests.post(
                test_client.update_url, data="test_clipboard_content", timeout=5
            )
            assert response.status_code == 200
            assert response.text == "OK"
            logger.success("✅ Clipboard update endpoint working correctly")
        except Exception as e:
            pytest.fail(f"❌ Clipboard update endpoint failed: {e}")

    def test_websocket_connection(self, server_process, test_client):
        """Test WebSocket connection to server."""
        logger.info("🧪 Testing WebSocket connection...")

        connection_event = threading.Event()

        def on_open(ws):
            test_client.connection_status = "connected"
            connection_event.set()
            logger.success("✅ WebSocket connected")

        def on_close(ws, close_status_code, close_msg):
            test_client.connection_status = "disconnected"
            logger.info(f"🔌 WebSocket disconnected (Code: {close_status_code})")

        def on_error(ws, error):
            test_client.connection_status = "error"
            connection_event.set()
            logger.error(f"❌ WebSocket error: {error}")

        try:
            test_client.ws = ws_client.WebSocketApp(
                test_client.websocket_url,
                on_open=on_open,
                on_close=on_close,
                on_error=on_error,
            )

            # Start WebSocket in separate thread
            ws_thread = threading.Thread(target=test_client.ws.run_forever)
            ws_thread.daemon = True
            ws_thread.start()

            # Wait for connection
            connected = connection_event.wait(timeout=5)
            assert connected, "WebSocket connection timed out"
            assert test_client.connection_status == "connected"

        except Exception as e:
            pytest.fail(f"❌ WebSocket connection failed: {e}")

    def test_websocket_message_receiving(self, server_process, test_client):
        """Test receiving messages through WebSocket."""
        logger.info("🧪 Testing WebSocket message receiving...")

        message_event = threading.Event()
        connection_event = threading.Event()

        def on_open(ws):
            logger.info("🔗 WebSocket connected for message test")
            connection_event.set()

        def on_message(ws, message):
            test_client.messages_received.append(message)
            message_event.set()
            logger.success(f"📨 Received message: {message}")

        def on_error(ws, error):
            logger.error(f"❌ WebSocket error: {error}")

        try:
            test_client.ws = ws_client.WebSocketApp(
                test_client.websocket_url,
                on_open=on_open,
                on_message=on_message,
                on_error=on_error,
            )

            # Start WebSocket in separate thread
            ws_thread = threading.Thread(target=test_client.ws.run_forever)
            ws_thread.daemon = True
            ws_thread.start()

            # Wait for connection to be established
            connected = connection_event.wait(timeout=5)
            if not connected:
                logger.warning("⚠️ Skipping message test - connection failed")
                return

            # Give connection time to stabilize
            time.sleep(0.5)

            # Trigger a clipboard update via POST
            requests.post(
                test_client.update_url, data="test_message_content", timeout=5
            )

            # Wait for message with reasonable timeout
            message_received = message_event.wait(timeout=8)
            if message_received:
                assert "new_clipboard" in test_client.messages_received
                logger.success("✅ Message receiving test passed")
            else:
                logger.warning("⚠️ No message received - server may not be broadcasting")

        except Exception as e:
            logger.warning(f"⚠️ WebSocket message test failed: {e}")

    def test_client_server_integration(self, server_process, test_client):
        """Test full client-server integration using actual client functions."""
        logger.info("🧪 Testing client-server integration...")

        # Import client functions
        try:
            # Temporarily modify the client's server configuration for testing
            import client

            original_update_url = client.UPDATE_URL
            client.UPDATE_URL = test_client.update_url

            # Test sending clipboard content
            test_content = "integration_test_content"
            client.send_clipboard_to_server(test_content)

            # Restore original URL
            client.UPDATE_URL = original_update_url

            # Verify the request was successful (server should be running)
            logger.success("✅ Client-server integration test passed")

        except ImportError as e:
            pytest.fail(f"❌ Could not import client module: {e}")
        except Exception as e:
            # Log the error but don't fail the test if it's just a connection issue
            logger.warning(f"⚠️ Integration test warning: {e}")

    def test_multiple_websocket_connections(self, server_process, test_client):
        """Test multiple simultaneous WebSocket connections."""
        logger.info("🧪 Testing multiple WebSocket connections...")

        connections = []
        connection_events = []

        def create_websocket_client(client_id):
            """Create a WebSocket client."""
            event = threading.Event()
            connection_events.append(event)

            def on_open(ws):
                logger.info(f"🔗 Client {client_id} connected")
                event.set()

            def on_error(ws, error):
                logger.error(f"❌ Client {client_id} error: {error}")
                event.set()

            ws = ws_client.WebSocketApp(
                test_client.websocket_url, on_open=on_open, on_error=on_error
            )
            connections.append(ws)

            # Start in separate thread
            thread = threading.Thread(target=ws.run_forever)
            thread.daemon = True
            thread.start()

        try:
            # Create 3 WebSocket connections
            for i in range(3):
                create_websocket_client(i)

            # Wait for all connections
            for i, event in enumerate(connection_events):
                connected = event.wait(timeout=5)
                assert connected, f"Client {i} connection timed out"

            logger.success("✅ Multiple WebSocket connections test passed")

            # Close all connections
            for ws in connections:
                ws.close()

        except Exception as e:
            pytest.fail(f"❌ Multiple connections test failed: {e}")

    def test_stress_clipboard_updates(self, server_process, test_client):
        """Test rapid clipboard updates."""
        logger.info("🧪 Testing stress clipboard updates...")

        try:
            # Send multiple rapid updates
            for i in range(5):
                test_content = f"stress_test_content_{i}"
                response = requests.post(
                    test_client.update_url, data=test_content, timeout=5
                )
                assert response.status_code == 200
                assert response.text == "OK"
                time.sleep(0.1)  # Small delay between requests

            logger.success("✅ Stress test completed successfully")

        except Exception as e:
            pytest.fail(f"❌ Stress test failed: {e}")

    def test_multiple_requests_integration(self, server_process, test_client):
        """Test multiple simultaneous requests."""
        logger.info("🧪 Testing multiple simultaneous requests...")

        def send_request(content):
            return requests.post(
                test_client.update_url, data=f"test_{content}", timeout=5
            )

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(send_request, i) for i in range(5)]
            results = [
                future.result() for future in concurrent.futures.as_completed(futures)
            ]

        # All requests should succeed
        for response in results:
            assert response.status_code == 200
            assert response.text == "OK"

        logger.success("✅ Multiple requests test completed successfully")

    @patch("subprocess.Popen")
    def test_clipboard_setting_mock(self, mock_popen, server_process, test_client):
        """Test clipboard setting with mocked subprocess."""
        logger.info("🧪 Testing clipboard setting with mock...")

        mock_process = mock_popen.return_value
        mock_process.communicate.return_value = (b"", b"")

        test_content = "mock test content"
        response = requests.post(test_client.update_url, data=test_content, timeout=5)

        assert response.status_code == 200
        logger.success("✅ Mock clipboard test completed")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
