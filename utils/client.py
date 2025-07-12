import websocket as ws_client
import requests
import os
import time
import threading
import sys
import pyperclip
from loguru import logger

# Configure loguru - create separate loggers
logger.remove()  # Remove default handler

# Regular logger for beautiful terminal output (stdout only)
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>CLIENT</cyan> - <level>{message}</level>",
    level=os.environ.get("LOG_LEVEL", "INFO"),
    colorize=True,
)

# Create a completely separate logger for React UI (stderr only)
from loguru import logger as base_logger

ui_logger = base_logger.bind()
ui_logger.remove()  # Remove all handlers from ui_logger
ui_logger.add(
    sys.stderr,  # Send to stderr so it gets captured by Electron
    format="{level: <8} | CLIENT - {message}",  # No timestamp since Electron adds its own
    level=os.environ.get("LOG_LEVEL", "INFO"),
    colorize=False,
)

# Configuration from environment variables
SERVER_HOST = os.environ.get("SERVER_HOST", "localhost")
SERVER_PORT = os.environ.get("SERVER_PORT", "8000")  # Connect to server on port 8000
SERVER_URL = f"ws://{SERVER_HOST}:{SERVER_PORT}/ws"
UPDATE_URL = f"http://{SERVER_HOST}:{SERVER_PORT}/update_clipboard"
GET_CLIPBOARD_URL = f"http://{SERVER_HOST}:{SERVER_PORT}/get_clipboard"

# Global variables
ws_connection = None
last_windows_clipboard = ""
running = True
pending_clipboard_updates = []  # Buffer for failed clipboard updates


def monitor_windows_clipboard():
    """Monitor Windows clipboard for changes and send to Mac server."""
    global last_windows_clipboard
    logger.info("🔍 Starting Windows clipboard monitor...")

    # Initialize with current clipboard content
    last_windows_clipboard = pyperclip.paste()
    logger.info(f"📋 Initial Windows clipboard: {last_windows_clipboard[:50]}...")

    while running:
        try:
            # Silently check clipboard content
            current_clipboard = pyperclip.paste()
            if (
                current_clipboard != last_windows_clipboard
                and current_clipboard.strip()
            ):
                logger.info(
                    f"📋 Windows clipboard changed to: {current_clipboard[:50]}..."
                )
                last_windows_clipboard = current_clipboard

                # Send to Mac server
                send_clipboard_to_server(current_clipboard)

            time.sleep(1)  # Check every second
        except Exception as e:
            logger.error(f"Error monitoring Windows clipboard: {e}")
            time.sleep(5)  # Wait longer on error


def get_mac_clipboard():
    """Fetch clipboard content from Mac server."""
    try:
        response = requests.get(GET_CLIPBOARD_URL, timeout=5)
        if response.status_code == 200:
            content = response.text
            logger.info(f"📥 Retrieved Mac clipboard: {content[:50]}...")
            return content
        else:
            logger.error(
                f"Failed to get Mac clipboard (Status: {response.status_code})"
            )
            return None
    except Exception as e:
        logger.error(f"❌ Failed to fetch Mac clipboard: {e}")
        return None


def on_message(ws, message):
    """Handle messages from Mac server."""
    global last_windows_clipboard
    logger.info(f"📨 Received message: {message}")

    if message == "new_clipboard":
        try:
            # Fetch new clipboard content from Mac server
            mac_content = get_mac_clipboard()
            if mac_content and mac_content != last_windows_clipboard:
                # Update Windows clipboard
                pyperclip.copy(mac_content)
                last_windows_clipboard = mac_content
                logger.success(f"📋 Updated Windows clipboard: {mac_content[:50]}...")

        except Exception as e:
            logger.error(f"❌ Failed to handle Mac clipboard update: {e}")


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
        pending_clipboard_updates.clear()

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
        f"🔌 Disconnected from Mac server (Code: {close_status_code}, Message: {close_msg})"
    )


def on_error(ws, error):
    logger.error(f"⚠️ WebSocket error: {error}")


def test_server_connectivity():
    """Test if the server is reachable."""
    try:
        logger.info("🔍 Testing server connectivity...")
        logger.info(f"🔗 Testing URL: {UPDATE_URL}")

        # Try a simple GET request first
        response = requests.get(
            f"http://{SERVER_HOST}:{SERVER_PORT}/",
            timeout=5,
            proxies={"http": None, "https": None},
        )
        logger.info(f"✅ Server reachable (Status: {response.status_code})")
        return True

    except requests.exceptions.ConnectionError:
        logger.error("❌ Cannot connect to server")
        logger.info(
            f"💡 Make sure the server is running on {SERVER_HOST}:{SERVER_PORT}"
        )
        return False
    except Exception as e:
        logger.error(f"❌ Connectivity test failed: {e}")
        return False


def send_clipboard_to_server(content):
    """Send Windows clipboard content to Mac server via WebSocket."""
    global ws_connection, pending_clipboard_updates

    def add_to_pending_queue():
        """Helper function to add content to pending queue."""
        pending_clipboard_updates.append(content)
        if len(pending_clipboard_updates) > 10:
            pending_clipboard_updates.pop(0)  # Remove oldest
        logger.info(f"📦 Pending clipboard updates: {len(pending_clipboard_updates)}")

    try:
        # Safer connection checking - avoid accessing .sock.connected directly as it can be unreliable
        connection_ok = True

        if not ws_connection:
            connection_ok = False
            logger.debug("⚠️ No WebSocket connection available")
        elif not hasattr(ws_connection, "sock") or not ws_connection.sock:
            connection_ok = False
            logger.debug("⚠️ WebSocket connection not established")
        else:
            # Try to check connection state more safely
            try:
                if (
                    hasattr(ws_connection.sock, "connected")
                    and not ws_connection.sock.connected
                ):
                    connection_ok = False
                    logger.debug("⚠️ WebSocket connection lost (sock.connected = False)")
            except (AttributeError, TypeError):
                # If we can't check the connection state, assume it's ok and let the send() call handle it
                logger.debug("Connection state check failed, will attempt to send")

        if not connection_ok:
            logger.debug("💡 Adding clipboard update to pending queue...")
            add_to_pending_queue()
            return False

        logger.info(f"📤 Sending clipboard via WebSocket: {content[:50]}...")

        # Create a message with clipboard content
        # Using a simple format: "clipboard_update:<content>"
        message = f"clipboard_update:{content}"

        # Send via WebSocket - this will raise an exception if connection is truly broken
        ws_connection.send(message)
        logger.success("✅ Clipboard sent to Mac successfully via WebSocket!")
        return True

    except Exception as e:
        # Check if this is a test environment or expected connection issue
        error_msg = str(e)
        if "mock" in error_msg.lower() or "test" in error_msg.lower():
            # During testing, log at debug level to avoid confusing error messages
            logger.debug(f"🧪 Test WebSocket error (expected): {e}")
        else:
            # Real connection errors should be logged as warnings, not errors
            logger.warning(f"⚠️ WebSocket connection issue: {e}")

        logger.info(f"💡 Error type: {type(e).__name__}")
        logger.info("💡 Adding to pending queue for retry when connection is restored")

        # Add to pending updates for retry
        add_to_pending_queue()
        return False


if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("🚀 Starting Clipboard Bridge Client")
    logger.info("=" * 50)
    logger.info(f"Mac Server URL: {SERVER_URL}")
    logger.info(f"Update URL: {UPDATE_URL}")
    logger.info(f"Get Clipboard URL: {GET_CLIPBOARD_URL}")
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

        # Add proper WebSocket headers
        headers = {
            "User-Agent": "ClipboardBridge-Client/1.0",
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
