from autobahn.twisted.websocket import WebSocketClientProtocol, WebSocketClientFactory


class MyClientProtocol(WebSocketClientProtocol):
    def onConnect(self, response):
        print("Server connected: {0}".format(response.peer))

    def onOpen(self):
        print("WebSocket connection open.")

        def hello():
            self.sendMessage("Hello, world!".encode("utf8"))
            self.sendMessage(b"\x00\x01\x03\x04", isBinary=True)
            self.factory.reactor.callLater(1, hello)

        # start sending messages every second ..
        hello()

    def onMessage(self, payload, isBinary):
        if isBinary:
            print("Binary message received: {0} bytes".format(len(payload)))
        else:
            print("Text message received: {0}".format(payload.decode("utf8")))

    def onClose(self, wasClean, code, reason):
        print("WebSocket connection closed: {0}".format(reason))
