from twisted.internet.protocol import ReconnectingClientFactory
from twisted.internet import defer


class QueuedRequest(object):
    def __init__(self, d, message):
        self.d = d
        self.message = message

class RequestQueue(object):
    def __init__(self):
        self._queued_requests = []
        self._consumer = None

    def request(self, message):
        d = defer.Deferred()
        if self._consumer is None:
            self._queued_requests.append(QueuedRequest(d, message))
        else:
            self._consumer.request(message, d)
        return d

    def attach(self, consumer):
        self._consumer = consumer
        while len(self._queued_requests) > 0:
            qr = self._queued_requests.pop(0)
            self._consumer.request(qr.message, qr.d)

    def detach(self):
        self._consumer = None

class ProtocolFactory(ReconnectingClientFactory):
    def __init__(self, TransportProtocol, packing, client_controller_factory, authentication_controller_factory):
        self._TransportProtocol = TransportProtocol
        self._packing = packing
        self._client_controller_factory = client_controller_factory
        self._request_queue = RequestQueue()
        self._authentication_controller_factory = authentication_controller_factory

    def buildProtocol(self, addr):
        self.resetDelay()
        protocol = self._TransportProtocol(self._packing)
        authentication_controller = self._authentication_controller_factory.build_authentication_controller(protocol)
        self._controller_instance = self._client_controller_factory.build(addr, protocol, authentication_controller, self._request_queue)

        protocol.controller = self._controller_instance
        protocol.factory = self

        return protocol

    def clientConnectionLost(self, connector, unused_reason):
        self._controller_instance = None
        ReconnectingClientFactory.clientConnectionLost(self, connector, unused_reason)

    def request(self, message):
        return self._request_queue.request(message)
