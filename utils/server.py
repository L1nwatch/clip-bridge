#!/usr/bin/env python3
# clipboard_server.py

from flask import Flask, request, jsonify
import subprocess
import threading
import os
import json
import time
import sys
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
                        set_mac_clipboard(message)

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


def set_mac_clipboard(data):
    """
    Set the Mac clipboard content.
    """
    try:
        p = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
        p.communicate(data.encode())
        logger.info(f"Clipboard updated with: {data[:50]}...")
    except Exception as e:
        logger.error(f"Failed to set clipboard: {e}")


def get_mac_clipboard():
    """
    Get the current Mac clipboard content.
    """
    try:
        p = subprocess.Popen(["pbpaste"], stdout=subprocess.PIPE)
        data, _ = p.communicate()
        content = data.decode()
        logger.info(f"Retrieved clipboard content: {content[:50]}...")
        return content
    except Exception as e:
        logger.error(f"Failed to get clipboard: {e}")
        return ""


@app.route("/")
def health_check():
    """Health check endpoint."""
    return "Clipboard Bridge Server is running", 200


@app.route("/update_clipboard", methods=["POST"])
def update_clipboard():
    """
    Update the server clipboard and notify clients.
    """
    global windows_clip
    logger.info("Received POST request to update clipboard")

    windows_clip = get_mac_clipboard()
    notify_clients()

    logger.info("Clipboard update completed successfully")
    return "OK", 200


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
