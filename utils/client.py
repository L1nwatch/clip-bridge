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
import json
import signal
import atexit
from loguru import logger
from loguru import logger as base_logger

# Import clipboard utilities with fallback
try:
    from clipboard_utils import get_clipboard, set_clipboard, ClipboardData

    logger.info("✨ Enhanced clipboard support (text + images) enabled")
except ImportError as e:
    logger.warning(f"Enhanced clipboard not available: {e}")
    logger.info("📋 Using fallback text-only clipboard support")
    # Create fallback implementations
    import pyperclip

    class ClipboardData:
        def __init__(self, content, data_type="text", metadata=None):
            self.content = content
            self.data_type = data_type
            self.metadata = metadata or {}

        def to_json(self):
            return json.dumps(
                {
                    "content": str(self.content),
                    "data_type": self.data_type,
                    "metadata": self.metadata,
                }
            )

        @classmethod
        def from_json(cls, json_str):
            data = json.loads(json_str)
            return cls(data["content"], data["data_type"], data["metadata"])

    def get_clipboard():
        try:
            content = pyperclip.paste()
            if isinstance(content, bytes):
                content = content.decode("utf-8")
            elif content is None:
                content = ""
            return ClipboardData(content, "text") if content else None
        except Exception:
            return None

    def set_clipboard(clipboard_data):
        try:
            if clipboard_data.data_type == "image":
                logger.warning("Image clipboard not supported in fallback mode")
                return False
            content = str(clipboard_data.content)
            pyperclip.copy(content)
            return True
        except Exception:
            return False


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

# Global WebSocket connection reference for signal handling
ws_connection_global = None


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    global running, ws_connection_global
    logger.info(f"📡 Received signal {signum}, initiating graceful shutdown...")
    running = False

    # Close WebSocket connection if it exists
    if ws_connection_global:
        try:
            ws_connection_global.close()
            logger.info("🔌 WebSocket connection closed")
        except Exception as e:
            logger.debug(f"Error closing WebSocket: {e}")

    # Give threads time to clean up
    time.sleep(1)
    logger.info("👋 Client shutdown complete")
    sys.exit(0)


def cleanup_on_exit():
    """Cleanup function called on normal exit."""
    global running
    running = False
    logger.debug("🧹 Cleanup function called")


# Register signal handlers for graceful shutdown
signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
signal.signal(signal.SIGTERM, signal_handler)  # Termination signal
if hasattr(signal, "SIGHUP"):  # Unix systems only
    signal.signal(signal.SIGHUP, signal_handler)  # Hangup signal

# Register cleanup function
atexit.register(cleanup_on_exit)


def monitor_windows_clipboard():
    """Monitor Windows clipboard for changes and send to Mac server."""
    global last_windows_clipboard
    logger.info("🔍 Starting Windows clipboard monitor...")

    try:
        # Initialize with current clipboard content
        last_clipboard_data = get_clipboard()
        last_windows_clipboard = (
            last_clipboard_data.to_json() if last_clipboard_data else ""
        )
        if last_clipboard_data:
            if last_clipboard_data.data_type == "text":
                content_preview = f"text: {str(last_clipboard_data.content)[:50]}..."
            else:
                size_info = last_clipboard_data.metadata.get("size", "unknown size")
                content_preview = f"image: {size_info}..."
            logger.info(f"📋 Initial Windows clipboard: {content_preview}")
    except Exception as e:
        # Handle case where clipboard is not available (CI environments, etc.)
        if "could not find a copy/paste mechanism" in str(e).lower():
            logger.warning(
                "🔕 Clipboard monitoring disabled - no system clipboard available "
                "(likely CI environment)"
            )
            return
        else:
            logger.error(f"❌ Failed to initialize clipboard monitoring: {e}")
            return

    while running:
        try:
            # Check clipboard content
            current_clipboard_data = get_clipboard()
            current_clipboard = (
                current_clipboard_data.to_json() if current_clipboard_data else ""
            )

            if current_clipboard != last_windows_clipboard and current_clipboard_data:
                if current_clipboard_data.data_type == "text":
                    content_preview = (
                        f"text: {str(current_clipboard_data.content)[:50]}..."
                    )
                else:
                    size_info = current_clipboard_data.metadata.get(
                        "size", "unknown size"
                    )
                    content_preview = f"image: {size_info}..."
                logger.info(f"📋 Windows clipboard changed to: {content_preview}")

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
    """Handle clipboard_content message type with enhanced clipboard support."""
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

        # Update Windows clipboard with enhanced support
        try:
            try:
                # Try to parse as enhanced clipboard data (JSON)
                clipboard_data = ClipboardData.from_json(mac_content)
                if clipboard_data.data_type == "text":
                    content_preview = f"text: {str(clipboard_data.content)[:50]}..."
                else:
                    size_info = clipboard_data.metadata.get("size", "unknown size")
                    content_preview = f"image: {size_info}..."

                logger.info(f"📋 Updating Windows clipboard with: {content_preview}")
                success = set_clipboard(clipboard_data)

                if success:
                    last_windows_clipboard = mac_content
                    logger.success(
                        f"✅ Windows clipboard updated successfully: {content_preview}"
                    )
                else:
                    logger.error("❌ Failed to update Windows clipboard")
            except (json.JSONDecodeError, ValueError):
                # Fallback to text if JSON parsing fails
                logger.info(
                    f"📋 Updating Windows clipboard with text (fallback): {mac_content[:50]}..."
                )
                text_data = ClipboardData(mac_content, "text")
                success = set_clipboard(text_data)
                if success:
                    last_windows_clipboard = mac_content
                    logger.success(
                        f"✅ Windows clipboard updated successfully (text fallback): "
                        f"{mac_content[:50]}..."
                    )

        except Exception as clipboard_error:
            if "could not find a copy/paste mechanism" in str(clipboard_error).lower():
                logger.warning(
                    "🔕 Cannot update clipboard - no system clipboard available "
                    "(likely CI environment)"
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
    global ws_connection, ws_connection_global, pending_clipboard_updates
    ws_connection = ws
    ws_connection_global = ws  # Set global reference for signal handling
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
    global running, ws_connection_global
    running = False
    ws_connection_global = None  # Clear global reference
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
    """Send Windows clipboard content to Mac server via WebSocket with enhanced support."""
    try:
        # Handle enhanced clipboard content with automatic fallback
        if content and content.startswith('{"content":'):
            # Enhanced clipboard data (JSON format)
            try:
                clipboard_data = ClipboardData.from_json(content)
                if clipboard_data.data_type == "text":
                    content_preview = f"text: {str(clipboard_data.content)[:50]}..."
                else:
                    size_info = clipboard_data.metadata.get("size", "unknown size")
                    content_preview = f"image: {size_info}..."
                message_content = content
                logger.info(
                    f"📤 Sending enhanced clipboard via WebSocket: {content_preview}"
                )
            except (json.JSONDecodeError, ValueError):
                # Fallback to text
                content_preview = f"text: {content[:50]}..."
                message_content = content
                logger.info(
                    f"📤 Sending text clipboard via WebSocket: {content_preview}"
                )
        else:
            # Text content or unknown format
            if isinstance(content, bytes):
                content = content.decode("utf-8")
            elif not isinstance(content, str):
                content = str(content)
            content_preview = f"text: {content[:50]}..."
            message_content = content
            logger.info(f"📤 Sending clipboard via WebSocket: {content_preview}")

        if not _is_connection_valid():
            logger.debug("💡 Adding clipboard update to pending queue...")
            _add_to_pending_queue(message_content)
            return False

        # Create a message with clipboard content and ensure UTF-8 encoding
        message = f"clipboard_update:{message_content}"
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

        # Set global reference for signal handling
        ws_connection_global = ws

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
        # Ensure WebSocket is closed
        if ws_connection_global:
            try:
                ws_connection_global.close()
            except Exception as e:
                logger.debug(f"Error closing WebSocket in finally: {e}")
        logger.info("👋 Clipboard Bridge Client shutdown complete")
