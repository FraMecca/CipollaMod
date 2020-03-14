from twisted.application import service
from twisted.application.internet import TCPClient


class Service(service.MultiService):
    def __init__(self, interface, port, protocol_factory):
        service.MultiService.__init__(self)

        self._interface = interface
        self._port = port
        self._protocol_factory = protocol_factory

        self._tcp_client = None

    def startService(self):
        self._tcp_client = TCPClient(self._interface, self._port, factory=self._protocol_factory)
        self._tcp_client.setServiceParent(self)
        return service.MultiService.startService(self)

    def stopService(self):
        return service.MultiService.stopService(self)
    
    def request(self, message):
        return self._protocol_factory.request(message)
