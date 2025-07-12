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
    global ws_connection
    ws_connection = ws
    logger.success("🔗 Connected to Mac server successfully!")
    ui_logger.success("Connected to server successfully")  # Clean message for React UI

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


def send_clipboard_to_server(content):
    """Send Windows clipboard content to Mac server."""
    try:
        logger.info(f"📤 Sending clipboard to Mac server: {content[:50]}...")
        response = requests.post(UPDATE_URL, data=content, timeout=5)
        if response.status_code == 200:
            logger.success("✅ Clipboard sent to Mac successfully!")
        else:
            logger.error(
                f"❌ Failed to send clipboard to Mac (Status: {response.status_code})"
            )
    except Exception as e:
        logger.error(f"❌ Error sending clipboard to Mac: {e}")


if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("🚀 Starting Clipboard Bridge Client")
    logger.info("=" * 50)
    logger.info(f"Mac Server URL: {SERVER_URL}")
    logger.info(f"Update URL: {UPDATE_URL}")
    logger.info(f"Get Clipboard URL: {GET_CLIPBOARD_URL}")
    logger.info("=" * 50)

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
