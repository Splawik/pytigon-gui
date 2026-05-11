"""WebSocket client protocol module.

Provides a WebSocket client protocol implementation based on
autobahn.twisted.websocket for use in Pytigon applications.
"""

import logging

from autobahn.twisted.websocket import WebSocketClientProtocol, WebSocketClientFactory

logger = logging.getLogger(__name__)


class MyClientProtocol(WebSocketClientProtocol):
    """WebSocket client protocol with automatic keep-alive messaging.

    On connection open, starts sending a message every second.
    Handles text and binary messages and logs connection lifecycle events.

    Usage::

        from autobahn.twisted.websocket import WebSocketClientFactory
        from twisted.internet import reactor

        factory = WebSocketClientFactory("ws://localhost:9000")
        factory.protocol = MyClientProtocol
        reactor.connectTCP("localhost", 9000, factory)
        reactor.run()
    """

    def onConnect(self, response):
        """Called when the client connects to the server.

        Args:
            response: Connection response object.
        """
        logger.info("Server connected: %s", response.peer)

    def onOpen(self):
        """Called when the WebSocket connection is fully open.

        Starts a periodic message send loop.
        """

        def send_hello():
            """Send a text and binary keep-alive message."""
            self.sendMessage("Hello, world!".encode("utf8"))
            self.sendMessage(b"\x00\x01\x03\x04", isBinary=True)
            self.factory.reactor.callLater(1, send_hello)

        logger.info("WebSocket connection open.")
        send_hello()

    def onMessage(self, payload, isBinary):
        """Called when a message is received from the server.

        Args:
            payload: Message data (bytes).
            isBinary: True if the message is binary, False if text.
        """
        if isBinary:
            logger.info("Binary message received: %d bytes", len(payload))
        else:
            logger.info("Text message received: %s", payload.decode("utf8"))

    def onClose(self, wasClean, code, reason):
        """Called when the WebSocket connection is closed.

        Args:
            wasClean: True if the close was clean.
            code: Close status code.
            reason: Close reason string.
        """
        logger.info("WebSocket connection closed: %s", reason)
