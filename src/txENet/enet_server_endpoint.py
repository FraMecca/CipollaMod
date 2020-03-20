import enet
from twisted.internet.interfaces import IStreamServerEndpoint
from zope.interface import implementer

from txENet.enet_host import ENetHost
from twisted.python import log


class ENetServerEndpoint(object):
    implementer(IStreamServerEndpoint)

    def __init__(self, reactor, interface, port, maxclients, channels, maxdown=0, maxup=0, max_duplicate_peers=None):
        self._reactor = reactor
        self._interface = interface
        self._port = port
        self._maxclients = maxclients
        self._channels = channels
        self._maxdown = maxdown
        self._maxup = maxup
        self._max_duplicate_peers = max_duplicate_peers or 0xFFF

        self._factory = None
        self._address = None
        self._enet_host = None

    def listen(self, factory):
        self._factory = factory

        self._address = enet.Address(self._interface, self._port)
        enet_host = enet.Host(self._address, self._maxclients, self._channels, self._maxdown, self._maxup)

        self._enet_host = ENetHost(enet_host, factory)

        self._enet_host.duplicate_peers = self._max_duplicate_peers

        log.msg("%s starting on %s" % (self._getLogPrefix(), self._port))

        self._reactor.addReader(self._enet_host)

    def flush(self):
        return self._enet_host.flush()
    
    def _getLogPrefix(self):
        pass
