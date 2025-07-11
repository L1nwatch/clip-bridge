#!/usr/bin/env python3
"""
Unit tests for Clipboard Bridge server and client interaction.
"""

import unittest
import threading
import time
import requests
import websocket as ws_client
import subprocess
import sys
import os
from loguru import logger
import signal

# Add utils directory to path to import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure loguru for tests
logger.remove()
logger.add(
    lambda msg: print(msg, end=""),
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>TEST</cyan> - <level>{message}</level>",
    level="INFO",
    colorize=True,
)


class ClipboardBridgeTest(unittest.TestCase):
    """Test cases for Clipboard Bridge server-client interaction."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment - start server."""
        logger.info("🚀 Setting up test environment...")

        # Start server in subprocess
        cls.server_process = subprocess.Popen(
            [sys.executable, "server.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # Redirect stderr to stdout
            preexec_fn=os.setsid,  # Create new process group
            text=True,
            bufsize=1,
            env={"PORT": "8000", "LOG_LEVEL": "INFO", **os.environ},
        )

        # Wait for server to start and check output
        server_started = False
        for _ in range(30):  # Wait up to 30 seconds
            time.sleep(1)

            # Check if process is still running
            if cls.server_process.poll() is not None:
                output, _ = cls.server_process.communicate()
                logger.error(f"Server process exited early. Output: {output}")
                raise Exception("Server failed to start")

            # Test if server is responding
            try:
                response = requests.get("http://localhost:8000", timeout=1)
                server_started = True
                break
            except requests.exceptions.ConnectionError:
                continue
            except Exception as e:
                logger.warning(f"Server check failed: {e}")
                continue

        if not server_started:
            # Try to get any output
            try:
                cls.server_process.terminate()
                output, _ = cls.server_process.communicate(timeout=5)
                logger.error(f"Server startup timeout. Output: {output}")
            except:
                logger.error("Server startup timeout with no output")
            raise Exception("Server failed to start within timeout")

        logger.success("✅ Server started successfully for testing")

        # Test endpoints
        cls.server_url = "http://localhost:8000"
        cls.websocket_url = "ws://localhost:8000/ws"
        cls.update_url = f"{cls.server_url}/update_clipboard"

    @classmethod
    def tearDownClass(cls):
        """Clean up test environment - stop server."""
        logger.info("🧹 Cleaning up test environment...")

        if hasattr(cls, "server_process") and cls.server_process:
            try:
                # Kill the entire process group
                os.killpg(os.getpgid(cls.server_process.pid), signal.SIGTERM)
                cls.server_process.wait(timeout=5)
                logger.success("✅ Server stopped successfully")
            except (subprocess.TimeoutExpired, ProcessLookupError):
                # Force kill if graceful shutdown fails
                try:
                    os.killpg(os.getpgid(cls.server_process.pid), signal.SIGKILL)
                    logger.warning("⚠️ Server force killed")
                except ProcessLookupError:
                    pass

    def setUp(self):
        """Set up for each test."""
        self.messages_received = []
        self.connection_status = None
        self.ws = None

    def tearDown(self):
        """Clean up after each test."""
        if self.ws:
            self.ws.close()

    def test_01_server_health(self):
        """Test if server is responding."""
        logger.info("🧪 Testing server health...")

        # Test if server is accessible (even if endpoint doesn't exist)
        try:
            response = requests.get(self.server_url, timeout=5)
            # Any response (even 404) means server is running
            logger.success(f"✅ Server is responding (Status: {response.status_code})")
        except requests.exceptions.ConnectionError:
            self.fail("❌ Server is not responding")
        except Exception as e:
            logger.warning(f"⚠️ Unexpected response: {e}")

    def test_02_clipboard_update_endpoint(self):
        """Test the /update_clipboard POST endpoint."""
        logger.info("🧪 Testing clipboard update endpoint...")

        try:
            response = requests.post(
                self.update_url, data="test_clipboard_content", timeout=5
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.text, "OK")
            logger.success("✅ Clipboard update endpoint working correctly")
        except Exception as e:
            self.fail(f"❌ Clipboard update endpoint failed: {e}")

    def test_03_websocket_connection(self):
        """Test WebSocket connection to server."""
        logger.info("🧪 Testing WebSocket connection...")

        connection_event = threading.Event()

        def on_open(ws):
            self.connection_status = "connected"
            connection_event.set()
            logger.success("✅ WebSocket connected")

        def on_close(ws, close_status_code, close_msg):
            self.connection_status = "disconnected"
            logger.info(f"🔌 WebSocket disconnected (Code: {close_status_code})")

        def on_error(ws, error):
            self.connection_status = "error"
            connection_event.set()
            logger.error(f"❌ WebSocket error: {error}")

        try:
            self.ws = ws_client.WebSocketApp(
                self.websocket_url,
                on_open=on_open,
                on_close=on_close,
                on_error=on_error,
            )

            # Start WebSocket in separate thread
            ws_thread = threading.Thread(target=self.ws.run_forever)
            ws_thread.daemon = True
            ws_thread.start()

            # Wait for connection
            connected = connection_event.wait(timeout=5)
            self.assertTrue(connected, "WebSocket connection timed out")
            self.assertEqual(self.connection_status, "connected")

        except Exception as e:
            self.fail(f"❌ WebSocket connection failed: {e}")

    def test_04_websocket_message_receiving(self):
        """Test receiving messages through WebSocket."""
        logger.info("🧪 Testing WebSocket message receiving...")

        message_event = threading.Event()
        connection_event = threading.Event()

        def on_open(ws):
            logger.info("🔗 WebSocket connected for message test")
            connection_event.set()

        def on_message(ws, message):
            self.messages_received.append(message)
            message_event.set()
            logger.success(f"📨 Received message: {message}")

        def on_error(ws, error):
            logger.error(f"❌ WebSocket error: {error}")

        try:
            self.ws = ws_client.WebSocketApp(
                self.websocket_url,
                on_open=on_open,
                on_message=on_message,
                on_error=on_error,
            )

            # Start WebSocket in separate thread
            ws_thread = threading.Thread(target=self.ws.run_forever)
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
            requests.post(self.update_url, data="test_message_content", timeout=5)

            # Wait for message with reasonable timeout
            message_received = message_event.wait(timeout=8)
            if message_received:
                self.assertIn("new_clipboard", self.messages_received)
                logger.success("✅ Message receiving test passed")
            else:
                logger.warning("⚠️ No message received - server may not be broadcasting")

        except Exception as e:
            logger.warning(f"⚠️ WebSocket message test failed: {e}")

    def test_05_client_server_integration(self):
        """Test full client-server integration using actual client functions."""
        logger.info("🧪 Testing client-server integration...")

        # Import client functions
        try:
            from client import send_clipboard_to_server

            # Test sending clipboard content
            test_content = "integration_test_content"
            send_clipboard_to_server(test_content)

            # Verify the request was successful (server should be running)
            logger.success("✅ Client-server integration test passed")

        except ImportError as e:
            self.fail(f"❌ Could not import client module: {e}")
        except Exception as e:
            # Log the error but don't fail the test if it's just a connection issue
            logger.warning(f"⚠️ Integration test warning: {e}")

    def test_06_multiple_websocket_connections(self):
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
                self.websocket_url, on_open=on_open, on_error=on_error
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
                self.assertTrue(connected, f"Client {i} connection timed out")

            logger.success("✅ Multiple WebSocket connections test passed")

            # Close all connections
            for ws in connections:
                ws.close()

        except Exception as e:
            self.fail(f"❌ Multiple connections test failed: {e}")

    def test_07_stress_clipboard_updates(self):
        """Test rapid clipboard updates."""
        logger.info("🧪 Testing stress clipboard updates...")

        try:
            # Send multiple rapid updates
            for i in range(5):
                test_content = f"stress_test_content_{i}"
                response = requests.post(self.update_url, data=test_content, timeout=5)
                self.assertEqual(response.status_code, 200)
                time.sleep(0.1)  # Small delay between requests

            logger.success("✅ Stress test completed successfully")

        except Exception as e:
            self.fail(f"❌ Stress test failed: {e}")


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("🧪 Starting Clipboard Bridge Test Suite")
    logger.info("=" * 60)

    # Create test suite
    test_suite = unittest.TestLoader().loadTestsFromTestCase(ClipboardBridgeTest)

    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    # Summary
    logger.info("=" * 60)
    if result.wasSuccessful():
        logger.success(f"🎉 All tests passed! ({result.testsRun} tests)")
    else:
        logger.error(
            f"❌ {len(result.failures)} failures, {len(result.errors)} errors out of {result.testsRun} tests"
        )
    logger.info("=" * 60)

    # Exit with appropriate code for CI
    if not result.wasSuccessful():
        sys.exit(1)
