"""Tests for pytigon_gui.guilib.websocket - WebSocket client protocol."""

import pytest
from unittest.mock import MagicMock, patch


class TestMyClientProtocol:
    """Tests for MyClientProtocol WebSocket client."""

    def test_class_imports(self):
        """MyClientProtocol can be imported."""
        from pytigon_gui.guilib.websocket import MyClientProtocol

        assert MyClientProtocol is not None

    def test_inheritance(self):
        """MyClientProtocol extends WebSocketClientProtocol."""
        from pytigon_gui.guilib.websocket import MyClientProtocol
        from autobahn.twisted.websocket import WebSocketClientProtocol

        assert issubclass(MyClientProtocol, WebSocketClientProtocol)

    @patch("pytigon_gui.guilib.websocket.WebSocketClientProtocol")
    def test_on_connect(self, mock_base):
        """onConnect logs the connection."""
        from pytigon_gui.guilib.websocket import MyClientProtocol

        proto = MyClientProtocol()
        proto.factory = MagicMock()
        proto.factory.reactor = MagicMock()

        mock_response = MagicMock()
        mock_response.peer = "tcp4:127.0.0.1:9000"

        proto.onConnect(mock_response)
        # Should not raise

    @patch("pytigon_gui.guilib.websocket.WebSocketClientProtocol")
    def test_on_open_starts_loop(self, mock_base):
        """onOpen starts a periodic message send loop."""
        from pytigon_gui.guilib.websocket import MyClientProtocol

        proto = MyClientProtocol()
        proto.factory = MagicMock()
        proto.factory.reactor = MagicMock()
        proto.sendMessage = MagicMock()

        proto.onOpen()

        # Verify sendMessage was called
        assert proto.sendMessage.call_count == 2
        # Verify callLater was scheduled
        proto.factory.reactor.callLater.assert_called_once()

    @patch("pytigon_gui.guilib.websocket.WebSocketClientProtocol")
    def test_on_message_text(self, mock_base):
        """onMessage handles text messages."""
        from pytigon_gui.guilib.websocket import MyClientProtocol

        proto = MyClientProtocol()
        proto.factory = MagicMock()

        proto.onMessage(b"hello", isBinary=False)
        # Should not raise

    @patch("pytigon_gui.guilib.websocket.WebSocketClientProtocol")
    def test_on_message_binary(self, mock_base):
        """onMessage handles binary messages."""
        from pytigon_gui.guilib.websocket import MyClientProtocol

        proto = MyClientProtocol()
        proto.factory = MagicMock()

        proto.onMessage(b"\x00\x01\x02", isBinary=True)
        # Should not raise

    @patch("pytigon_gui.guilib.websocket.WebSocketClientProtocol")
    def test_on_close(self, mock_base):
        """onClose logs the close reason."""
        from pytigon_gui.guilib.websocket import MyClientProtocol

        proto = MyClientProtocol()
        proto.factory = MagicMock()

        proto.onClose(wasClean=True, code=1000, reason="Normal closure")
        # Should not raise


class TestMyClientFactory:
    """Tests for WebSocketClientFactory usage."""

    def test_factory_imports(self):
        """WebSocketClientFactory can be imported."""
        from pytigon_gui.guilib.websocket import WebSocketClientFactory

        assert WebSocketClientFactory is not None
