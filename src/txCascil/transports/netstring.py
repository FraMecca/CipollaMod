from twisted.internet.protocol import connectionDone
from twisted.protocols.basic import NetstringReceiver

from txCascil.registry_manager import register


@register('transport', 'netstring')
class NetstringProtocol(NetstringReceiver):
    def __init__(self, packing):
        self._packing = packing

    def stringReceived(self, data):
        message = self._packing.unpack(data)
        self.controller.receive(message)

    def send(self, message):
        data = self._packing.pack(message)
        self.sendString(data)

    def disconnect(self):
        self.transport.loseConnection()

    def connectionMade(self):
        NetstringReceiver.connectionMade(self)
        self.controller.connection_established()

    def connectionLost(self, reason=connectionDone):
        self.controller.disconnected()
        NetstringReceiver.connectionLost(self, reason=reason)
