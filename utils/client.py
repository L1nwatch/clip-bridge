# -*- coding: utf-8 -*-

import os
import sys

# Force UTF-8 encoding for all I/O operations - MUST be at the top
import locale

try:
    # Set locale to UTF-8
    locale.setlocale(locale.LC_ALL, "en_US.UTF-8")
except locale.Error:
    try:
        # Fallback for different systems
        locale.setlocale(locale.LC_ALL, "UTF-8")
    except locale.Error:
        pass  # Use system default if UTF-8 not available

# Force environment encoding
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.environ.setdefault("LANG", "en_US.UTF-8")
os.environ.setdefault("LC_ALL", "en_US.UTF-8")

# Force stdout/stderr to use UTF-8
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import websocket as ws_client
import os
import time
import threading
import sys
import pyperclip
from loguru import logger
from loguru import logger as base_logger

# Configure loguru - create separate loggers
logger.remove()  # Remove default handler

# Regular logger for beautiful terminal output (stdout only)
logger.add(
    sys.stdout,
    format=(
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | <cyan>CLIENT</cyan> - <level>{message}</level>"
    ),
    level=os.environ.get("LOG_LEVEL", "INFO"),
    colorize=True,
)

# Create a completely separate logger for React UI (stderr only)
ui_logger = base_logger.bind()
ui_logger.remove()  # Remove all handlers from ui_logger
ui_logger.add(
    sys.stderr,  # Send to stderr so it gets captured by Electron
    format="{level: <8} | CLIENT - {message}",  # No timestamp
    level=os.environ.get("LOG_LEVEL", "INFO"),
    colorize=False,
)

# Configuration from environment variables
SERVER_HOST = os.environ.get("SERVER_HOST", "localhost")
SERVER_PORT = os.environ.get("SERVER_PORT", "8000")  # Connect to port 8000
SERVER_URL = f"ws://{SERVER_HOST}:{SERVER_PORT}/ws"

# Global variables
ws_connection = None
last_windows_clipboard = ""
running = True
pending_clipboard_updates = []  # Buffer for failed clipboard updates


def monitor_windows_clipboard():
    """Monitor Windows clipboard for changes and send to Mac server."""
    global last_windows_clipboard
    logger.info("🔍 Starting Windows clipboard monitor...")

    try:
        # Initialize with current clipboard content
        last_windows_clipboard = pyperclip.paste()
        # Ensure clipboard content is UTF-8 string
        if isinstance(last_windows_clipboard, bytes):
            last_windows_clipboard = last_windows_clipboard.decode("utf-8")
        elif last_windows_clipboard is None:
            last_windows_clipboard = ""

        logger.info(f"📋 Initial Windows clipboard: {last_windows_clipboard[:50]}...")
    except Exception as e:
        # Handle case where clipboard is not available (CI environments, etc.)
        if "could not find a copy/paste mechanism" in str(e).lower():
            logger.warning(
                "🔕 Clipboard monitoring disabled - no system clipboard available (likely CI environment)"
            )
            return
        else:
            logger.error(f"❌ Failed to initialize clipboard monitoring: {e}")
            return

    while running:
        try:
            # Silently check clipboard content with UTF-8 handling
            current_clipboard = pyperclip.paste()
            # Ensure clipboard content is UTF-8 string
            if isinstance(current_clipboard, bytes):
                current_clipboard = current_clipboard.decode("utf-8")
            elif current_clipboard is None:
                current_clipboard = ""

            if (
                current_clipboard != last_windows_clipboard
                and current_clipboard.strip()
            ):
                logger.info(
                    f"📋 Windows clipboard changed to: " f"{current_clipboard[:50]}..."
                )
                last_windows_clipboard = current_clipboard

                # Send to Mac server
                send_clipboard_to_server(current_clipboard)

            time.sleep(1)  # Check every second
        except Exception as e:
            # Handle clipboard access errors gracefully
            if "could not find a copy/paste mechanism" in str(e).lower():
                logger.warning(
                    "🔕 Clipboard monitoring stopped - no system clipboard available"
                )
                break
            else:
                logger.error(f"Error monitoring Windows clipboard: {e}")
                time.sleep(5)  # Wait longer on error


def _handle_new_clipboard_request(ws):
    """Handle new_clipboard message type."""
    try:
        # Send UTF-8 encoded message
        message = "get_clipboard"
        ws.send(message.encode("utf-8") if isinstance(message, str) else message)
        logger.debug("📤 Requested clipboard content via WebSocket")
    except Exception as e:
        logger.error(f"❌ Failed to request clipboard content: {e}")


def _handle_clipboard_content(message):
    """Handle clipboard_content message type with UTF-8 encoding."""
    global last_windows_clipboard

    try:
        # Debug: log the raw message
        logger.debug(f"🔍 Raw message type: {type(message)}")
        logger.debug(f"🔍 Raw message repr: {repr(message)}")

        # Ensure message is UTF-8 string
        if isinstance(message, bytes):
            message = message.decode("utf-8")
            logger.debug(f"🔍 Decoded message: {repr(message)}")

        # Debug: log prefix removal
        prefix = "clipboard_content:"
        if not message.startswith(prefix):
            logger.error(
                f"❌ Message doesn't start with expected prefix: {repr(message[:20])}"
            )
            return

        mac_content = message[len(prefix) :]  # Use len() instead of hardcoded 18
        logger.debug(f"🔍 Extracted content: {repr(mac_content)}")

        if not mac_content or mac_content == last_windows_clipboard:
            logger.debug("🔍 No update needed - content is empty or unchanged")
            return  # No update needed

        # Update Windows clipboard with UTF-8 content
        try:
            logger.info(f"📋 Updating Windows clipboard with: {mac_content[:50]}...")
            pyperclip.copy(mac_content)
            last_windows_clipboard = mac_content
            logger.success(
                f"✅ Windows clipboard updated successfully: {mac_content[:50]}..."
            )

        except Exception as clipboard_error:
            if "could not find a copy/paste mechanism" in str(clipboard_error).lower():
                logger.warning(
                    "🔕 Cannot update clipboard - no system clipboard available (likely CI environment)"
                )
            else:
                raise clipboard_error
    except UnicodeDecodeError as e:
        logger.error(f"❌ Failed to decode Mac clipboard content as UTF-8: {e}")
        logger.error(
            f"❌ Problematic bytes: {repr(message) if isinstance(message, bytes) else 'N/A'}"
        )
    except Exception as e:
        logger.error(f"❌ Failed to handle Mac clipboard update: {e}")
        import traceback

        logger.error(f"❌ Traceback: {traceback.format_exc()}")


def on_message(ws, message):
    """Handle messages from Mac server with UTF-8 encoding."""
    # Ensure message is properly decoded as UTF-8
    if isinstance(message, bytes):
        try:
            message = message.decode("utf-8")
        except UnicodeDecodeError as e:
            logger.error(f"Failed to decode message as UTF-8: {e}")
            return

    logger.info(f"📨 Received message: {message}")

    if message == "new_clipboard":
        _handle_new_clipboard_request(ws)
    elif message.startswith("clipboard_content:"):
        _handle_clipboard_content(message)


def on_open(ws):
    global ws_connection, pending_clipboard_updates
    ws_connection = ws
    logger.success("🔗 Connected to Mac server successfully!")
    ui_logger.success("Connected to server successfully")  # Clean message for React UI

    # Send any pending clipboard updates
    if pending_clipboard_updates:
        logger.info(
            f"📤 Sending {len(pending_clipboard_updates)} pending clipboard updates..."
        )
        for content in pending_clipboard_updates:
            send_clipboard_to_server(content)
        pending_clipboard_updates = []  # Clear the pending updates

    # Start monitoring Windows clipboard in background
    monitor_thread = threading.Thread(target=monitor_windows_clipboard, daemon=True)
    monitor_thread.start()

    # Send a keepalive message every 30 seconds
    def send_keepalive():
        while running and ws.sock and ws.sock.connected:
            try:
                ws.ping()
                time.sleep(30)
            except Exception as e:
                logger.debug(f"Keepalive error: {e}")
                break

    keepalive_thread = threading.Thread(target=send_keepalive, daemon=True)
    keepalive_thread.start()


def on_close(ws, close_status_code, close_msg):
    global running
    running = False
    logger.warning(
        f"🔌 Disconnected from Mac server "
        f"(Code: {close_status_code}, Message: {close_msg})"
    )


def on_error(ws, error):
    logger.error(f"⚠️ WebSocket error: {error}")


def test_server_connectivity():
    """Test if the server is reachable via WebSocket."""
    try:
        logger.info("🔍 Testing server connectivity...")
        logger.info(f"🔗 Will attempt WebSocket connection to: {SERVER_URL}")

        # We'll test the actual WebSocket connection in the main connection logic
        # For now, just validate that we have the required configuration
        if not SERVER_HOST or not SERVER_PORT:
            logger.error("❌ Missing server configuration")
            return False

        logger.info("✅ Server configuration looks valid")
        return True

    except Exception as e:
        logger.error(f"❌ Connectivity test failed: {e}")
        return False


def _add_to_pending_queue(content):
    """Helper function to add content to pending queue."""
    global pending_clipboard_updates
    pending_clipboard_updates.append(content)
    if len(pending_clipboard_updates) > 10:
        pending_clipboard_updates = pending_clipboard_updates[1:]  # Remove oldest
    logger.info(f"📦 Pending clipboard updates: {len(pending_clipboard_updates)}")


def _is_connection_valid():
    """Check if WebSocket connection is valid and ready to use."""
    if not ws_connection:
        logger.debug("⚠️ No WebSocket connection available")
        return False

    if not hasattr(ws_connection, "sock") or not ws_connection.sock:
        logger.debug("⚠️ WebSocket connection not established")
        return False

    # Try to check connection state more safely
    try:
        if (
            hasattr(ws_connection.sock, "connected")
            and not ws_connection.sock.connected
        ):
            logger.debug("⚠️ WebSocket connection lost (sock.connected = False)")
            return False
    except (AttributeError, TypeError):
        # If we can't check the connection state, assume it's ok and
        # let the send() call handle it
        logger.debug("Connection state check failed, will attempt to send")

    return True


def _handle_send_error(e, content):
    """Handle errors that occur during clipboard sending."""
    error_msg = str(e)
    if "mock" in error_msg.lower() or "test" in error_msg.lower():
        # During testing, log at debug level to avoid confusing error messages
        logger.debug(f"🧪 Test WebSocket error (expected): {e}")
    else:
        # Real connection errors should be logged as warnings, not errors
        logger.warning(f"⚠️ WebSocket connection issue: {e}")

    logger.info(f"💡 Error type: {type(e).__name__}")
    logger.info("💡 Adding to pending queue for retry when connection is restored")
    _add_to_pending_queue(content)


def send_clipboard_to_server(content):
    """Send Windows clipboard content to Mac server via WebSocket with UTF-8 encoding."""
    try:
        # Ensure content is UTF-8 string
        if isinstance(content, bytes):
            content = content.decode("utf-8")
        elif not isinstance(content, str):
            content = str(content)

        if not _is_connection_valid():
            logger.debug("💡 Adding clipboard update to pending queue...")
            _add_to_pending_queue(content)
            return False

        logger.info(f"📤 Sending clipboard via WebSocket: {content[:50]}...")

        # Create a message with clipboard content and ensure UTF-8 encoding
        message = f"clipboard_update:{content}"
        # Send as UTF-8 encoded bytes
        ws_connection.send(message.encode("utf-8"))
        logger.success("✅ Clipboard sent to Mac successfully via WebSocket!")
        return True

    except UnicodeDecodeError as e:
        logger.error(f"❌ Failed to encode clipboard content as UTF-8: {e}")
        return False
    except Exception as e:
        _handle_send_error(e, content)
        return False


if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("🚀 Starting Clipboard Bridge Client")
    logger.info("=" * 50)
    logger.info(f"Mac Server WebSocket URL: {SERVER_URL}")
    logger.info("=" * 50)

    # Test server connectivity first
    if not test_server_connectivity():
        logger.error("🚫 Cannot proceed - server is not reachable")
        logger.info("💡 Please make sure:")
        logger.info("   1. The server is running on the Mac")
        logger.info("   2. The port 8000 is not blocked by firewall")
        logger.info("   3. Both devices are on the same network")
        exit(1)

    try:
        # Enable debug for websocket (set to True for debugging)
        ws_client.enableTrace(False)  # Disable trace for cleaner output

        # Add proper WebSocket headers with UTF-8 encoding
        headers = {
            "User-Agent": "ClipboardBridge-Client/1.0",
            "Accept-Charset": "utf-8",
        }

        ws = ws_client.WebSocketApp(
            SERVER_URL,
            header=headers,
            on_message=on_message,
            on_open=on_open,
            on_close=on_close,
            on_error=on_error,
        )
        logger.info("🔄 Attempting to connect to Mac server...")
        ws.run_forever(ping_interval=30, ping_timeout=10)
    except KeyboardInterrupt:
        running = False
        logger.warning("\n🛑 Client stopped by user")
    except Exception as e:
        running = False
        logger.error(f"❌ Client error: {e}")
    finally:
        running = False
        logger.info("👋 Clipboard Bridge Client shutdown complete")
