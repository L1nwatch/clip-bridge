# -*- coding: utf-8 -*-
"""
Tests for UTF-8 encoding support in clipboard bridge server and client.
"""

import unittest
from unittest.mock import Mock, MagicMock, patch, call
import sys
import os

# Add the parent directory to sys.path to import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import server
import client


class TestUTF8Encoding(unittest.TestCase):
    """Test UTF-8 encoding throughout the clipboard bridge system."""

    def setUp(self):
        """Set up test fixtures."""
        # Reset client state
        client.ws_connection = None
        client.last_windows_clipboard = ""
        client.running = True
        client.pending_clipboard_updates = []
        
        # Reset server state
        server.websocket_clients.clear()
        server.last_mac_clipboard = ""
        server.windows_clip = ""

    def test_utf8_encoding_declaration(self):
        """Test that both server and client files have UTF-8 encoding declarations."""
        # Read the actual files to check for encoding declarations
        with open(os.path.join(os.path.dirname(__file__), '..', 'server.py'), 'r', encoding='utf-8') as f:
            server_content = f.read()
        
        with open(os.path.join(os.path.dirname(__file__), '..', 'client.py'), 'r', encoding='utf-8') as f:
            client_content = f.read()
        
        # Check for UTF-8 encoding declarations
        self.assertIn('# -*- coding: utf-8 -*-', server_content)
        self.assertIn('# -*- coding: utf-8 -*-', client_content)

    @patch('server.pyperclip.copy')
    def test_server_set_clipboard_with_utf8_string(self, mock_copy):
        """Test server set_clipboard with UTF-8 string content."""
        # Test with various UTF-8 content
        test_cases = [
            "Hello World",  # ASCII
            "café résumé naïve",  # Accented characters
            "你好世界",  # Chinese
            "مرحبا بالعالم",  # Arabic
            "🎉 🚀 📋 🌍",  # Emojis
            "Здравствуй мир",  # Cyrillic
            "こんにちは世界",  # Japanese
        ]
        
        for test_content in test_cases:
            with self.subTest(content=test_content):
                server.set_clipboard(test_content)
                mock_copy.assert_called_with(test_content)

    @patch('server.pyperclip.copy')
    def test_server_set_clipboard_with_utf8_bytes(self, mock_copy):
        """Test server set_clipboard with UTF-8 byte content."""
        # Test with UTF-8 encoded bytes
        test_cases = [
            ("Hello World", b"Hello World"),
            ("café résumé", "café résumé".encode('utf-8')),
            ("你好世界", "你好世界".encode('utf-8')),
            ("🎉 🚀 📋", "🎉 🚀 📋".encode('utf-8')),
        ]
        
        for expected_str, test_bytes in test_cases:
            with self.subTest(content=expected_str):
                server.set_clipboard(test_bytes)
                mock_copy.assert_called_with(expected_str)

    @patch('server.pyperclip.copy')
    def test_server_set_clipboard_with_none_and_other_types(self, mock_copy):
        """Test server set_clipboard with None and other data types."""
        # Test with None
        server.set_clipboard(None)
        mock_copy.assert_called_with('None')
        
        # Test with integer
        server.set_clipboard(42)
        mock_copy.assert_called_with('42')
        
        # Test with list (converted to string)
        server.set_clipboard(['a', 'b', 'c'])
        mock_copy.assert_called_with("['a', 'b', 'c']")

    @patch('server.pyperclip.paste')
    def test_server_get_clipboard_with_utf8_content(self, mock_paste):
        """Test server get_clipboard with UTF-8 content."""
        test_cases = [
            "Hello World",
            "café résumé naïve",
            "你好世界",
            "🎉 🚀 📋 🌍",
        ]
        
        for test_content in test_cases:
            with self.subTest(content=test_content):
                mock_paste.return_value = test_content
                result = server.get_clipboard()
                self.assertEqual(result, test_content)

    @patch('server.pyperclip.paste')
    def test_server_get_clipboard_with_utf8_bytes(self, mock_paste):
        """Test server get_clipboard when pyperclip returns bytes."""
        test_cases = [
            ("Hello World", b"Hello World"),
            ("café résumé", "café résumé".encode('utf-8')),
            ("你好世界", "你好世界".encode('utf-8')),
        ]
        
        for expected_str, test_bytes in test_cases:
            with self.subTest(content=expected_str):
                mock_paste.return_value = test_bytes
                result = server.get_clipboard()
                self.assertEqual(result, expected_str)

    def test_server_websocket_message_utf8_encoding(self):
        """Test server WebSocket message handling with UTF-8 encoding."""
        # Mock WebSocket
        mock_ws = MagicMock()
        
        # Test with UTF-8 string message
        with patch('server.set_clipboard') as mock_set_clipboard:
            test_content = "你好世界 🌍"
            message = f"clipboard_update:{test_content}"
            
            server._handle_websocket_message(mock_ws, message, "test_client")
            mock_set_clipboard.assert_called_with(test_content)

    def test_server_websocket_message_utf8_bytes_decoding(self):
        """Test server WebSocket message handling with UTF-8 bytes."""
        # Mock WebSocket
        mock_ws = MagicMock()
        
        # Test with UTF-8 bytes message
        with patch('server.set_clipboard') as mock_set_clipboard:
            test_content = "café résumé 🎉"
            message_bytes = f"clipboard_update:{test_content}".encode('utf-8')
            
            server._handle_websocket_message(mock_ws, message_bytes, "test_client")
            mock_set_clipboard.assert_called_with(test_content)

    def test_server_websocket_get_clipboard_response_encoding(self):
        """Test server WebSocket get_clipboard response is UTF-8 encoded."""
        # Mock WebSocket
        mock_ws = MagicMock()
        
        with patch('server.get_clipboard') as mock_get_clipboard:
            test_content = "Hello 世界 🚀"
            mock_get_clipboard.return_value = test_content
            
            server._handle_websocket_message(mock_ws, "get_clipboard", "test_client")
            
            # Verify response is sent as UTF-8 bytes
            expected_response = f"clipboard_content:{test_content}".encode('utf-8')
            mock_ws.send.assert_called_with(expected_response)

    def test_server_notify_clients_utf8_encoding(self):
        """Test server notify_clients sends UTF-8 encoded messages."""
        # Mock clients
        mock_client1 = MagicMock()
        mock_client2 = MagicMock()
        
        server.websocket_clients.add(mock_client1)
        server.websocket_clients.add(mock_client2)
        
        server.notify_clients()
        
        # Verify all clients receive UTF-8 encoded message
        expected_message = "new_clipboard".encode('utf-8')
        mock_client1.send.assert_called_with(expected_message)
        mock_client2.send.assert_called_with(expected_message)

    def test_client_send_clipboard_utf8_encoding(self):
        """Test client send_clipboard_to_server with UTF-8 encoding."""
        # Mock WebSocket connection
        mock_ws = MagicMock()
        mock_ws.sock = MagicMock()
        mock_ws.sock.connected = True
        client.ws_connection = mock_ws
        client.pending_clipboard_updates = []
        
        test_cases = [
            "Hello World",
            "café résumé naïve",
            "你好世界",
            "🎉 🚀 📋 🌍",
        ]
        
        for test_content in test_cases:
            with self.subTest(content=test_content):
                mock_ws.reset_mock()
                
                result = client.send_clipboard_to_server(test_content)
                
                self.assertTrue(result)
                expected_message = f"clipboard_update:{test_content}".encode('utf-8')
                mock_ws.send.assert_called_with(expected_message)

    def test_client_send_clipboard_utf8_bytes_input(self):
        """Test client send_clipboard_to_server with UTF-8 bytes input."""
        # Mock WebSocket connection
        mock_ws = MagicMock()
        mock_ws.sock = MagicMock()
        mock_ws.sock.connected = True
        client.ws_connection = mock_ws
        client.pending_clipboard_updates = []
        
        # Test with UTF-8 bytes input
        test_content_str = "Hello 世界 🚀"
        test_content_bytes = test_content_str.encode('utf-8')
        
        result = client.send_clipboard_to_server(test_content_bytes)
        
        self.assertTrue(result)
        expected_message = f"clipboard_update:{test_content_str}".encode('utf-8')
        mock_ws.send.assert_called_with(expected_message)

    def test_client_handle_new_clipboard_request_utf8(self):
        """Test client _handle_new_clipboard_request sends UTF-8 encoded message."""
        mock_ws = MagicMock()
        
        client._handle_new_clipboard_request(mock_ws)
        
        expected_message = "get_clipboard".encode('utf-8')
        mock_ws.send.assert_called_with(expected_message)

    @patch('client.pyperclip.copy')
    def test_client_handle_clipboard_content_utf8(self, mock_copy):
        """Test client _handle_clipboard_content with UTF-8 content."""
        test_cases = [
            "Hello World",
            "café résumé naïve",
            "你好世界",
            "🎉 🚀 📋 🌍",
        ]
        
        for test_content in test_cases:
            with self.subTest(content=test_content):
                mock_copy.reset_mock()
                client.last_windows_clipboard = ""  # Reset state
                
                message = f"clipboard_content:{test_content}"
                client._handle_clipboard_content(message)
                
                mock_copy.assert_called_with(test_content)
                self.assertEqual(client.last_windows_clipboard, test_content)

    @patch('client.pyperclip.copy')
    def test_client_handle_clipboard_content_utf8_bytes(self, mock_copy):
        """Test client _handle_clipboard_content with UTF-8 bytes message."""
        test_content = "Hello 世界 🚀"
        message_bytes = f"clipboard_content:{test_content}".encode('utf-8')
        client.last_windows_clipboard = ""  # Reset state
        
        client._handle_clipboard_content(message_bytes)
        
        mock_copy.assert_called_with(test_content)
        self.assertEqual(client.last_windows_clipboard, test_content)

    def test_client_on_message_utf8_bytes_decoding(self):
        """Test client on_message with UTF-8 bytes message."""
        mock_ws = MagicMock()
        
        with patch('client._handle_new_clipboard_request') as mock_handle:
            message_bytes = "new_clipboard".encode('utf-8')
            client.on_message(mock_ws, message_bytes)
            mock_handle.assert_called_with(mock_ws)

    def test_server_invalid_utf8_handling(self):
        """Test server handles invalid UTF-8 gracefully."""
        mock_ws = MagicMock()
        
        # Create invalid UTF-8 bytes
        invalid_utf8 = b'\xff\xfe'
        
        # Should not raise exception, should log error and return early
        server._handle_websocket_message(mock_ws, invalid_utf8, "test_client")
        
        # WebSocket should not be called since invalid UTF-8 causes early return
        mock_ws.send.assert_not_called()

    def test_client_invalid_utf8_handling(self):
        """Test client handles invalid UTF-8 gracefully."""
        mock_ws = MagicMock()
        
        # Create invalid UTF-8 bytes
        invalid_utf8 = b'\xff\xfe'
        
        # Should not raise exception, should log error and return early
        client.on_message(mock_ws, invalid_utf8)
        
        # No further processing should happen
        mock_ws.send.assert_not_called()

    def test_server_flask_endpoints_utf8_responses(self):
        """Test Flask endpoints return proper UTF-8 responses."""
        with server.app.test_client() as test_client:
            # Test health endpoint
            response = test_client.get('/')
            self.assertEqual(response.status_code, 200)
            self.assertIn('charset=utf-8', response.content_type)
            
            # Test health endpoint
            response = test_client.get('/health')
            self.assertEqual(response.status_code, 200)
            self.assertIn('charset=utf-8', response.content_type)

    @patch('server.pyperclip.paste')
    def test_server_get_clipboard_endpoint_utf8(self, mock_paste):
        """Test /get_clipboard endpoint with UTF-8 content."""
        test_content = "Hello 世界 🚀"
        mock_paste.return_value = test_content
        
        with server.app.test_client() as test_client:
            response = test_client.get('/get_clipboard')
            self.assertEqual(response.status_code, 200)
            self.assertIn('charset=utf-8', response.content_type)
            self.assertEqual(response.get_data(as_text=True), test_content)

    @patch('server.set_clipboard')
    @patch('server.notify_clients')
    def test_server_update_clipboard_endpoint_utf8(self, mock_notify, mock_set_clipboard):
        """Test /update_clipboard endpoint with UTF-8 content."""
        test_content = "Hello 世界 🚀"
        
        with server.app.test_client() as test_client:
            response = test_client.post(
                '/update_clipboard',
                data=test_content.encode('utf-8'),
                content_type='text/plain; charset=utf-8'
            )
            
            self.assertEqual(response.status_code, 200)
            mock_set_clipboard.assert_called_with(test_content)
            mock_notify.assert_called_once()

    def test_comprehensive_utf8_roundtrip(self):
        """Test complete UTF-8 roundtrip: client -> server -> client."""
        # Mock WebSocket connections
        mock_client_ws = MagicMock()
        mock_client_ws.sock = MagicMock()
        mock_client_ws.sock.connected = True
        
        mock_server_ws = MagicMock()
        
        # Test content with various UTF-8 characters
        test_content = "Hello 世界! café résumé 🎉🚀📋"
        
        # Step 1: Client sends clipboard to server
        client.ws_connection = mock_client_ws
        client.pending_clipboard_updates = []
        
        with patch('server.set_clipboard') as mock_server_set:
            # Client sends UTF-8 content
            result = client.send_clipboard_to_server(test_content)
            self.assertTrue(result)
            
            # Verify message is UTF-8 encoded
            expected_message = f"clipboard_update:{test_content}".encode('utf-8')
            mock_client_ws.send.assert_called_with(expected_message)
            
            # Step 2: Server processes the message
            received_message = f"clipboard_update:{test_content}"
            server._handle_websocket_message(mock_server_ws, received_message, "test_client")
            mock_server_set.assert_called_with(test_content)
        
        # Step 3: Server sends content back to client
        with patch('server.get_clipboard') as mock_server_get, \
             patch('client.pyperclip.copy') as mock_client_copy:
            
            mock_server_get.return_value = test_content
            
            # Server handles get_clipboard request
            server._handle_websocket_message(mock_server_ws, "get_clipboard", "test_client")
            
            # Verify server sends UTF-8 encoded response
            expected_response = f"clipboard_content:{test_content}".encode('utf-8')
            mock_server_ws.send.assert_called_with(expected_response)
            
            # Step 4: Client processes the response
            response_message = f"clipboard_content:{test_content}"
            client.last_windows_clipboard = ""  # Reset state
            client._handle_clipboard_content(response_message)
            
            # Verify client sets clipboard with UTF-8 content
            mock_client_copy.assert_called_with(test_content)
            self.assertEqual(client.last_windows_clipboard, test_content)


if __name__ == '__main__':
    unittest.main()
