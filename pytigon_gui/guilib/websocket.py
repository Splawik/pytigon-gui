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

        Starts a periodic message send loop. The loop is cancelled
        automatically when the connection closes.
        """
        self._keepalive = None
        self._closed = False

        def send_hello():
            """Send a text and binary keep-alive message."""
            if self._closed:
                return
            self.sendMessage("Hello, world!".encode("utf8"))
            self.sendMessage(b"\x00\x01\x03\x04", isBinary=True)
            self._keepalive = self.factory.reactor.callLater(1, send_hello)

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

        Stops the periodic keep-alive loop.

        Args:
            wasClean: True if the close was clean.
            code: Close status code.
            reason: Close reason string.
        """
        self._closed = True
        if getattr(self, "_keepalive", None) is not None:
            try:
                self._keepalive.cancel()
            except Exception:
                pass
            self._keepalive = None
        logger.info("WebSocket connection closed: %s", reason)
