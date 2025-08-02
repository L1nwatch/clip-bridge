#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# clipboard_server.py

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

from flask import Flask, request
import threading
import os
import time
import sys
import json
import signal
import atexit
from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler
from geventwebsocket import WebSocketError
from loguru import logger
import loguru

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


# Configuration from environment variables
PORT = int(os.environ.get("PORT", "8000"))  # Server default port
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

# Configure loguru - create separate loggers
logger.remove()  # Remove default handler

# Regular logger for beautiful terminal output (stdout only)
logger.add(
    sys.stdout,
    format=(
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    ),
    level=LOG_LEVEL,
    colorize=True,
)

# Create a completely separate logger instance for React UI
ui_logger = loguru.logger
ui_logger.remove()  # Remove all default handlers
ui_logger.add(
    sys.stderr,  # Send to stderr so it gets captured by Electron
    format="{level: <8} | {message}",  # No timestamp since Electron adds its own
    level=LOG_LEVEL,
    colorize=False,
)

app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False  # Enable UTF-8 for JSON responses


# Add CORS support
@app.after_request
def after_request(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
    response.headers.add("Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS")
    return response


windows_clip = ""
websocket_clients = set()
lock = threading.Lock()
last_mac_clipboard = ""
running = True  # Global flag to control server running state


def signal_handler(sig, frame):
    """Handle termination signals gracefully."""
    global running
    logger.info(f"📡 Received signal {sig}, initiating graceful shutdown...")
    running = False

    # Close all WebSocket connections
    try:
        for client in list(websocket_clients):
            try:
                client.close()
                logger.debug("Closed WebSocket client connection")
            except Exception as e:
                logger.debug(f"Error closing WebSocket client: {e}")
        websocket_clients.clear()
    except Exception as e:
        logger.debug(f"Error during WebSocket cleanup: {e}")

    # Give threads time to cleanup
    time.sleep(1)
    logger.info("👋 Server signal handler complete")
    sys.exit(0)


def cleanup_on_exit():
    """Cleanup function called on normal exit."""
    global running
    running = False
    # Don't log here to avoid loguru cleanup issues during testing


# Register signal handlers and cleanup
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)
if hasattr(signal, "SIGHUP"):
    signal.signal(signal.SIGHUP, signal_handler)
atexit.register(cleanup_on_exit)


def monitor_mac_clipboard():
    """Monitor Mac clipboard for changes and notify clients."""
    global last_mac_clipboard, running
    logger.info("🔍 Starting Mac clipboard monitor...")

    # Initialize with current clipboard content
    last_clipboard_data = get_clipboard()
    last_mac_clipboard = last_clipboard_data.to_json() if last_clipboard_data else ""
    if last_clipboard_data:
        if last_clipboard_data.data_type == "text":
            content_preview = f"text: {str(last_clipboard_data.content)[:50]}..."
        else:
            size_info = last_clipboard_data.metadata.get("size", "unknown size")
            content_preview = f"image: {size_info}..."
        logger.info(f"📋 Initial Mac clipboard: {content_preview}")

    while running:
        try:
            # Check clipboard content
            current_clipboard_data = get_clipboard()
            current_clipboard = (
                current_clipboard_data.to_json() if current_clipboard_data else ""
            )

            # Only process if clipboard actually changed and has content
            if current_clipboard != last_mac_clipboard and current_clipboard_data:
                if current_clipboard_data.data_type == "text":
                    content_preview = (
                        f"text: {str(current_clipboard_data.content)[:30]}..."
                    )
                else:
                    size_info = current_clipboard_data.metadata.get(
                        "size", "unknown size"
                    )
                    content_preview = f"image: {size_info}..."
                logger.info(
                    f"📋 Mac clipboard changed from: {last_mac_clipboard[:30]}..."
                )
                logger.info(f"📋 Mac clipboard changed to: {content_preview}")

                last_mac_clipboard = current_clipboard

                # Notify all connected Windows clients
                notify_clients()

            time.sleep(1)  # Check every second
        except Exception as e:
            logger.error(f"Error monitoring Mac clipboard: {e}")
            time.sleep(5)  # Wait longer on error

    logger.info("🔍 Mac clipboard monitor stopped")


def set_clipboard_compat(data):
    """
    Set the clipboard content with enhanced support.
    """
    if isinstance(data, str):
        # Try to parse as JSON first (enhanced data)
        try:
            clipboard_data = ClipboardData.from_json(data)
            success = set_clipboard(clipboard_data)
            if clipboard_data.data_type == "text":
                logger.info(
                    f"Clipboard updated with text: {str(clipboard_data.content)[:50]}..."
                )
            else:
                size_info = clipboard_data.metadata.get("size", "unknown size")
                logger.info(f"Clipboard updated with image: {size_info}...")
            return success
        except (json.JSONDecodeError, ValueError):
            # Fallback to text
            text_data = ClipboardData(data, "text")
            success = set_clipboard(text_data)
            logger.info(f"Clipboard updated with text (fallback): {data[:50]}...")
            return success
    else:
        # Convert non-string data to text
        text_data = ClipboardData(str(data), "text")
        success = set_clipboard(text_data)
        logger.info(f"Clipboard updated with converted text: {str(data)[:50]}...")
        return success


def get_clipboard_compat(log_retrieval=True):
    """
    Get the current clipboard content with enhanced support.
    """
    clipboard_data = get_clipboard()
    if clipboard_data:
        if log_retrieval:
            if clipboard_data.data_type == "text":
                logger.info(
                    f"Retrieved clipboard text: {str(clipboard_data.content)[:50]}..."
                )
            else:
                size_info = clipboard_data.metadata.get("size", "unknown size")
                logger.info(f"Retrieved clipboard image: {size_info}...")
        return clipboard_data.to_json()
    return ""


def _handle_websocket_message(ws, message, client_addr):
    """Handle individual WebSocket messages."""
    # Ensure message is properly decoded as UTF-8 string
    if isinstance(message, bytes):
        try:
            message = message.decode("utf-8")
        except UnicodeDecodeError as e:
            logger.error(f"Failed to decode WebSocket message as UTF-8: {e}")
            return

    if message == "ping":
        ws.send("pong")
        logger.debug("Sent pong response")
    elif message == "get_clipboard":
        # Client is requesting current clipboard content
        current_clipboard_data = get_clipboard()
        if current_clipboard_data:
            response = f"clipboard_content:{current_clipboard_data.to_json()}"
        else:
            response = "clipboard_content:"

        # Debug: log the response before encoding
        logger.debug(f"🔍 Response before encoding: {repr(response)}")
        logger.debug(f"🔍 Response type: {type(response)}")

        # Ensure response is sent as UTF-8
        if isinstance(response, str):
            encoded_response = response.encode("utf-8")
            logger.debug(f"🔍 Encoded response: {repr(encoded_response)}")
            ws.send(encoded_response)
        else:
            ws.send(response)

        if current_clipboard_data:
            if current_clipboard_data.data_type == "text":
                content_preview = f"text: {str(current_clipboard_data.content)[:50]}..."
            else:
                size_info = current_clipboard_data.metadata.get("size", "unknown size")
                content_preview = f"image: {size_info}..."
            logger.info(f"📋 Sent clipboard content to client: {content_preview}")
        else:
            logger.info("📋 Sent empty clipboard content to client")
    elif message.startswith("clipboard_update:"):
        # Extract clipboard content from the message
        clipboard_content_str = message[len("clipboard_update:") :]
        logger.info(
            f"📋 Received clipboard update via WebSocket: {clipboard_content_str[:50]}..."
        )

        try:
            # Try to parse as enhanced clipboard data (JSON)
            clipboard_data = ClipboardData.from_json(clipboard_content_str)
            set_clipboard(clipboard_data)
            if clipboard_data.data_type == "text":
                content_preview = f"text: {str(clipboard_data.content)[:50]}..."
            else:
                size_info = clipboard_data.metadata.get("size", "unknown size")
                content_preview = f"image: {size_info}..."
            logger.info(f"📋 Set clipboard: {content_preview}")
        except (json.JSONDecodeError, ValueError):
            # Fallback to text-only if JSON parsing fails
            text_data = ClipboardData(clipboard_content_str, "text")
            set_clipboard(text_data)
            logger.info(
                f"📋 Set text clipboard (fallback): {clipboard_content_str[:50]}..."
            )
    else:
        # Legacy format - treat entire message as clipboard content
        if not message.startswith(("pong", "ping")):
            logger.info(f"📋 Received legacy clipboard message: {message[:50]}...")
            text_data = ClipboardData(message, "text")
            set_clipboard(text_data)


def _process_websocket_messages(ws, client_addr):
    """Process messages in the WebSocket message loop."""
    while not ws.closed:
        try:
            logger.debug("Waiting for message...")
            message = ws.receive()
            logger.debug(f"Received message: {message}")

            if message is None:
                # No message received, but connection is still alive
                logger.debug("No message received, continuing...")
                time.sleep(0.1)  # Small delay to prevent busy waiting
                continue

            if message:  # Only process non-empty messages
                logger.info(f"Processing message from {client_addr}: {message[:50]}...")
                _handle_websocket_message(ws, message, client_addr)

        except WebSocketError as e:
            logger.error(f"WebSocket error: {e}")
            break
        except Exception as e:
            # Handle specific WebSocket errors but don't break for timeout
            logger.error(f"Exception in receive loop: {e}")
            if "timed out" in str(e).lower():
                logger.debug("Timeout in receive, continuing...")
                continue
            else:
                logger.error(f"WebSocket receive error: {e}")
                break


def websocket_app(environ, start_response):
    """Handle WebSocket connections at WSGI level"""
    logger.info("WSGI WebSocket handler called")

    wsgi_websocket = environ.get("wsgi.websocket")
    if wsgi_websocket:
        logger.info("WebSocket upgrade detected")
        ws = wsgi_websocket
        client_addr = environ.get("REMOTE_ADDR", "unknown")
        logger.info(f"New WebSocket connection from {client_addr}")

        with lock:
            websocket_clients.add(ws)
            logger.info(f"Client added. Total clients: {len(websocket_clients)}")

        try:
            logger.info("Starting WebSocket message loop")
            _process_websocket_messages(ws, client_addr)
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            with lock:
                websocket_clients.discard(ws)
                logger.info(
                    f"Client {client_addr} disconnected. Total clients: {len(websocket_clients)}"
                )

        return []
    else:
        # Not a WebSocket upgrade, pass to Flask
        return app(environ, start_response)


def combined_app(environ, start_response):
    """Combined WSGI app that handles both HTTP and WebSocket"""
    path = environ.get("PATH_INFO", "")

    if path == "/ws":
        # Handle WebSocket connections
        return websocket_app(environ, start_response)
    else:
        # Handle regular HTTP requests with Flask
        return app(environ, start_response)


def notify_clients():
    """
    Notify all connected clients about new clipboard content.
    """
    logger.info(f"Notifying {len(websocket_clients)} clients about clipboard update")

    with lock:
        disconnected_clients = []
        for client in list(websocket_clients):
            try:
                # Ensure notification is sent as UTF-8
                message = "new_clipboard"
                client.send(
                    message.encode("utf-8") if isinstance(message, str) else message
                )
                logger.debug("Successfully notified client")
            except Exception as e:
                logger.warning(f"Failed to notify client: {e}")
                disconnected_clients.append(client)

        # Remove disconnected clients
        for client in disconnected_clients:
            websocket_clients.remove(client)
            logger.info(
                f"Removed disconnected client. Total clients: {len(websocket_clients)}"
            )


@app.route("/")
def health_check():
    """Health check endpoint."""
    response_data = {"status": "ok", "service": "ClipBridge Server", "version": "1.0"}
    response = app.response_class(
        response=app.json.dumps(response_data, ensure_ascii=False),
        status=200,
        mimetype="application/json; charset=utf-8",
    )
    return response


@app.route("/health")
def health_endpoint():
    """Dedicated health check endpoint."""
    response_data = {
        "status": "healthy",
        "service": "ClipBridge Server",
        "version": "1.0",
    }
    response = app.response_class(
        response=app.json.dumps(response_data, ensure_ascii=False),
        status=200,
        mimetype="application/json; charset=utf-8",
    )
    return response


@app.route("/get_clipboard", methods=["GET"])
def get_clipboard_content():
    """Get current clipboard content with enhanced support."""
    try:
        content = get_clipboard_compat(
            log_retrieval=True
        )  # Log when explicitly requested
        logger.info(f"Sending clipboard content: {content[:50]}...")
        # Ensure response is UTF-8 encoded
        response = app.response_class(content, mimetype="text/plain; charset=utf-8")
        return response, 200
    except Exception as e:
        logger.error(f"Failed to get clipboard: {e}")
        return "Error getting clipboard", 500


@app.route("/update_clipboard", methods=["POST"])
def update_clipboard():
    """
    Update the server clipboard and notify clients.
    """
    global windows_clip

    # Log request details for debugging
    logger.info("=" * 50)
    logger.info("📥 Received POST request to update clipboard")
    logger.info(f"🔗 Request URL: {request.url}")
    logger.info(f"📄 Request headers: {dict(request.headers)}")
    logger.info(f"🌐 Client IP: {request.remote_addr}")
    logger.info(f"📊 Content length: {request.content_length}")

    try:
        # Get the content from the request with explicit UTF-8 decoding
        content = request.get_data(as_text=True)

        # Ensure content is properly decoded as UTF-8
        if isinstance(content, bytes):
            try:
                content = content.decode("utf-8")
            except UnicodeDecodeError as e:
                logger.error(f"Failed to decode request content as UTF-8: {e}")
                return "Invalid UTF-8 encoding", 400

        logger.info(f"📝 Received content length: {len(content) if content else 0}")

        if content:
            # Update Mac clipboard with content from Windows
            set_clipboard_compat(content)
            windows_clip = content
            logger.info(f"✅ Updated Mac clipboard with: {content[:50]}...")

            # Notify other clients (if any)
            notify_clients()

            logger.info("🎉 Clipboard update completed successfully")
            return "OK", 200
        else:
            logger.warning("⚠️ No content received in request")
            return "No content", 400

    except Exception as e:
        logger.error(f"❌ Error processing clipboard update: {e}")
        logger.error(f"🔍 Error type: {type(e).__name__}")
        return f"Server error: {str(e)}", 500
    finally:
        logger.info("=" * 50)


if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("🚀 Starting Clipboard Bridge Server")
    logger.info("=" * 50)
    logger.info("Server configuration:")
    logger.info("  - Host: 0.0.0.0")
    logger.info(f"  - Port: {PORT}")
    logger.info(f"  - WebSocket endpoint: ws://localhost:{PORT}/ws")
    logger.info(f"  - HTTP endpoint: http://localhost:{PORT}/update_clipboard")
    logger.info("=" * 50)

    try:
        # Start Mac clipboard monitoring in background
        monitor_thread = threading.Thread(target=monitor_mac_clipboard, daemon=True)
        monitor_thread.start()

        # Run the server with WebSocket support using combined WSGI app
        server = pywsgi.WSGIServer(
            ("0.0.0.0", PORT), combined_app, handler_class=WebSocketHandler
        )
        logger.success("✅ Server started successfully!")
        ui_logger.success("Server started successfully")  # Clean message for React UI
        logger.info("Press Ctrl+C to stop the server")
        server.serve_forever()
    except KeyboardInterrupt:
        logger.warning("\n🛑 Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Server error: {e}")
    finally:
        logger.info("👋 Clipboard Bridge Server shutdown complete")
