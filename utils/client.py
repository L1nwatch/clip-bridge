import websocket as ws_client
import requests
import os
from loguru import logger

# Configure loguru
logger.remove()  # Remove default handler
logger.add(
    lambda msg: print(msg, end=""),
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>CLIENT</cyan> - <level>{message}</level>",
    level=os.environ.get("LOG_LEVEL", "INFO"),
    colorize=True,
)

# Configuration from environment variables
SERVER_HOST = os.environ.get("SERVER_HOST", "localhost")
SERVER_PORT = os.environ.get("SERVER_PORT", "8000")
SERVER_URL = f"ws://{SERVER_HOST}:{SERVER_PORT}/ws"
UPDATE_URL = f"http://{SERVER_HOST}:{SERVER_PORT}/update_clipboard"


def on_message(ws, message):
    logger.info(f"📨 Received message: {message}")
    if message == "new_clipboard":
        try:
            # Fetch new clipboard content from the server
            response = requests.get(UPDATE_URL)
            logger.success(f"📋 New clipboard content: {response.text[:50]}...")
        except Exception as e:
            logger.error(f"❌ Failed to fetch clipboard: {e}")


def on_open(ws):
    logger.success("🔗 Connected to server successfully!")


def on_close(ws, close_status_code, close_msg):
    logger.warning(
        f"🔌 Disconnected from server (Code: {close_status_code}, Message: {close_msg})"
    )


def on_error(ws, error):
    logger.error(f"⚠️ WebSocket error: {error}")


def send_clipboard_to_server(content):
    try:
        logger.info(f"📤 Sending clipboard content to server: {content[:50]}...")
        response = requests.post(UPDATE_URL, data=content)
        if response.status_code == 200:
            logger.success("✅ Clipboard sent successfully!")
        else:
            logger.error(
                f"❌ Failed to send clipboard (Status: {response.status_code})"
            )
    except Exception as e:
        logger.error(f"❌ Error sending clipboard: {e}")


if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("🚀 Starting Clipboard Bridge Client")
    logger.info("=" * 50)
    logger.info(f"Server URL: {SERVER_URL}")
    logger.info(f"Update URL: {UPDATE_URL}")
    logger.info("=" * 50)

    try:
        ws = ws_client.WebSocketApp(
            SERVER_URL,
            on_message=on_message,
            on_open=on_open,
            on_close=on_close,
            on_error=on_error,
        )
        logger.info("🔄 Attempting to connect to server...")
        ws.run_forever()
    except KeyboardInterrupt:
        logger.warning("\n🛑 Client stopped by user")
    except Exception as e:
        logger.error(f"❌ Client error: {e}")
    finally:
        logger.info("👋 Clipboard Bridge Client shutdown complete")
