"""Tests for pytigon_gui.guilib.websocket - WebSocket client protocol."""

import logging
from unittest.mock import MagicMock

LOGGER_NAME = "pytigon_gui.guilib.websocket"


def _protocol():
    """Create a MyClientProtocol with a mock factory/reactor."""
    from pytigon_gui.guilib.websocket import MyClientProtocol

    proto = MyClientProtocol()
    proto.factory = MagicMock()
    proto.factory.reactor = MagicMock()
    return proto


class TestMyClientProtocol:
    """Tests for MyClientProtocol WebSocket client."""

    def test_inheritance(self):
        """MyClientProtocol extends WebSocketClientProtocol."""
        from autobahn.twisted.websocket import WebSocketClientProtocol

        from pytigon_gui.guilib.websocket import MyClientProtocol

        assert issubclass(MyClientProtocol, WebSocketClientProtocol)

    def test_on_connect_logs_peer(self, caplog):
        """onConnect logs the peer address."""
        proto = _protocol()
        response = MagicMock()
        response.peer = "tcp4:127.0.0.1:9000"

        with caplog.at_level(logging.INFO, logger=LOGGER_NAME):
            proto.onConnect(response)

        assert "tcp4:127.0.0.1:9000" in caplog.text

    def test_on_open_starts_keepalive_loop(self):
        """onOpen sends one text and one binary message and schedules the loop."""
        proto = _protocol()
        proto.sendMessage = MagicMock()

        proto.onOpen()

        assert proto.sendMessage.call_count == 2
        proto.factory.reactor.callLater.assert_called_once()

    def test_on_message_text_logs_payload(self, caplog):
        """onMessage decodes and logs a text message."""
        proto = _protocol()

        with caplog.at_level(logging.INFO, logger=LOGGER_NAME):
            proto.onMessage(b"hello", isBinary=False)

        assert "hello" in caplog.text

    def test_on_message_binary_logs_length(self, caplog):
        """onMessage logs the byte length of a binary message."""
        proto = _protocol()

        with caplog.at_level(logging.INFO, logger=LOGGER_NAME):
            proto.onMessage(b"\x00\x01\x02", isBinary=True)

        assert "3 bytes" in caplog.text

    def test_on_close_cancels_keepalive_and_logs(self, caplog):
        """onClose stops the keepalive loop and logs the reason."""
        proto = _protocol()
        keepalive = MagicMock()
        proto._keepalive = keepalive

        with caplog.at_level(logging.INFO, logger=LOGGER_NAME):
            proto.onClose(wasClean=True, code=1000, reason="Normal closure")

        keepalive.cancel.assert_called_once()
        assert proto._keepalive is None
        assert "Normal closure" in caplog.text
