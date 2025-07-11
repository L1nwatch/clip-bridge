#!/usr/bin/env python3
# clipboard_server.py

from flask import Flask
from flask_sockets import Sockets
import subprocess
import threading
import os
from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler
from loguru import logger

# Configuration from environment variables
PORT = int(os.environ.get("PORT", "8000"))
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

# Configure loguru
logger.remove()  # Remove default handler
logger.add(
    lambda msg: print(msg, end=""),
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level=LOG_LEVEL,
    colorize=True,
)

app = Flask(__name__)
sockets = Sockets(app)

windows_clip = ""
clients = set()
lock = threading.Lock()


@sockets.route("/ws")
def websocket_connection(ws):
    """
    WebSocket connection handler for real-time communication with clients.
    """
    client_addr = ws.environ.get("REMOTE_ADDR", "unknown")
    logger.info(f"New WebSocket connection from {client_addr}")

    with lock:
        clients.add(ws)
        logger.info(f"Client added. Total clients: {len(clients)}")

    try:
        while not ws.closed:
            message = ws.receive()
            if message:
                logger.info(f"Received message from {client_addr}: {message[:50]}...")
                set_mac_clipboard(message)
    except Exception as e:
        logger.error(f"Error in WebSocket connection: {e}")
    finally:
        with lock:
            clients.remove(ws)
            logger.info(
                f"Client {client_addr} disconnected. Total clients: {len(clients)}"
            )


def notify_clients():
    """
    Notify all connected clients about new clipboard content.
    """
    logger.info(f"Notifying {len(clients)} clients about clipboard update")

    with lock:
        disconnected_clients = []
        for client in list(clients):
            try:
                client.send("new_clipboard")
                logger.debug("Successfully notified client")
            except Exception as e:
                logger.warning(f"Failed to notify client: {e}")
                disconnected_clients.append(client)

        # Remove disconnected clients
        for client in disconnected_clients:
            clients.remove(client)
            logger.info(f"Removed disconnected client. Total clients: {len(clients)}")


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
        # Run the server with WebSocket support
        server = pywsgi.WSGIServer(
            ("0.0.0.0", PORT), app, handler_class=WebSocketHandler
        )
        logger.success("✅ Server started successfully!")
        print(
            "Server started successfully", flush=True
        )  # For IPC detection with forced flush
        logger.info("Press Ctrl+C to stop the server")
        server.serve_forever()
    except KeyboardInterrupt:
        logger.warning("\n🛑 Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Server error: {e}")
    finally:
        logger.info("👋 Clipboard Bridge Server shutdown complete")
