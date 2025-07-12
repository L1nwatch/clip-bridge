#!/usr/bin/env python3
"""
Demo script to connect a WebSocket client to the Clipboard Bridge server
and trigger client connection events for UI testing.

This is NOT a pytest test file - it's a utility script for manual testing
of the Connected Clients UI functionality.

Usage:
    python demo_client_connection.py [duration_seconds] [port]
"""

import websocket
import time
import threading
import sys


def on_message(ws, message):
    print(f"📨 Received: {message}")


def on_error(ws, error):
    print(f"❌ Error: {error}")


def on_close(ws, close_status_code, close_msg):
    print("🔌 Connection closed")


def on_open(ws):
    print("✅ Connected to Clipboard Bridge server")
    print("⏳ Staying connected for 10 seconds...")

    # Keep connection alive for 10 seconds
    def close_later():
        time.sleep(10)
        print("⏰ Closing connection...")
        ws.close()

    threading.Thread(target=close_later).start()


def main():
    server_url = "ws://localhost:8000/ws"
    print(f"🔌 Connecting to {server_url}...")

    # Connect to the WebSocket server
    ws = websocket.WebSocketApp(
        server_url,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
    )

    try:
        ws.run_forever()
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
        ws.close()
    except Exception as e:
        print(f"💥 Connection failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
