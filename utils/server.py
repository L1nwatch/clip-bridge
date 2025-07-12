#!/usr/bin/env python3
# clipboard_server.py

from flask import Flask, request, jsonify
import subprocess
import threading
import os
import json
import time
import sys
import pyperclip
from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler
from geventwebsocket import WebSocketError
from loguru import logger

# Configuration from environment variables
PORT = int(os.environ.get("PORT", "8000"))  # Server default port
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

# Configure loguru - create separate loggers
logger.remove()  # Remove default handler

# Regular logger for beautiful terminal output (stdout only)
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level=LOG_LEVEL,
    colorize=True,
)

# Create a completely separate logger instance for React UI
import loguru

ui_logger = loguru.logger
ui_logger.remove()  # Remove all default handlers
ui_logger.add(
    sys.stderr,  # Send to stderr so it gets captured by Electron
    format="{level: <8} | {message}",  # No timestamp since Electron adds its own
    level=LOG_LEVEL,
    colorize=False,
)

app = Flask(__name__)


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


def monitor_mac_clipboard():
    """Monitor Mac clipboard for changes and notify clients."""
    global last_mac_clipboard
    logger.info("🔍 Starting Mac clipboard monitor...")

    # Initialize with current clipboard content
    last_mac_clipboard = get_clipboard(log_retrieval=False)
    logger.info(f"📋 Initial Mac clipboard: {last_mac_clipboard[:50]}...")

    while True:
        try:
            # Silently check clipboard content
            current_clipboard = get_clipboard(log_retrieval=False)

            # Only process if clipboard actually changed and has content
            if current_clipboard != last_mac_clipboard and current_clipboard.strip():
                logger.info(
                    f"📋 Mac clipboard changed from: {last_mac_clipboard[:30]}..."
                )
                logger.info(f"📋 Mac clipboard changed to: {current_clipboard[:50]}...")
                last_mac_clipboard = current_clipboard

                # Notify all connected Windows clients
                notify_clients()

            time.sleep(1)  # Check every second
        except Exception as e:
            logger.error(f"Error monitoring Mac clipboard: {e}")
            time.sleep(5)  # Wait longer on error


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
            # Keep connection alive and wait for messages
            while not ws.closed:
                try:
                    logger.debug("Waiting for message...")
                    # Use a timeout to prevent blocking indefinitely
                    message = ws.receive()
                    logger.debug(f"Received message: {message}")

                    if message is None:
                        # No message received, but connection is still alive
                        logger.debug("No message received, continuing...")
                        time.sleep(0.1)  # Small delay to prevent busy waiting
                        continue

                    if message:  # Only process non-empty messages
                        logger.info(
                            f"Processing message from {client_addr}: {message[:50]}..."
                        )
                        set_clipboard(message)

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
                client.send("new_clipboard")
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


def set_clipboard(data):
    """
    Set the clipboard content (cross-platform).
    """
    try:
        pyperclip.copy(data)
        logger.info(f"Clipboard updated with: {data[:50]}...")
    except Exception as e:
        logger.error(f"Failed to set clipboard: {e}")


def get_clipboard(log_retrieval=True):
    """
    Get the current clipboard content (cross-platform).
    """
    try:
        content = pyperclip.paste()
        if log_retrieval:
            logger.info(f"Retrieved clipboard content: {content[:50]}...")
        return content
    except Exception as e:
        logger.error(f"Failed to get clipboard: {e}")
        return ""


@app.route("/")
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "ClipBridge Server", "version": "1.0"}, 200


@app.route("/health")
def health_endpoint():
    """Dedicated health check endpoint."""
    return {"status": "healthy", "service": "ClipBridge Server", "version": "1.0"}, 200


@app.route("/get_clipboard", methods=["GET"])
def get_clipboard_content():
    """Get current clipboard content."""
    try:
        content = get_clipboard(log_retrieval=True)  # Log when explicitly requested
        logger.info(f"Sending clipboard content: {content[:50]}...")
        return content, 200
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
        # Get the content from the request
        content = request.get_data(as_text=True)
        logger.info(f"📝 Received content length: {len(content) if content else 0}")

        if content:
            # Update Mac clipboard with content from Windows
            set_clipboard(content)
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
