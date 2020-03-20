from txENet.enet_server_endpoint import ENetServerEndpoint


class Binding(ENetServerEndpoint):
    def __init__(self, reactor, interface, port, maxclients, channels, maxdown=0, maxup=0, max_duplicate_peers=None):

        ENetServerEndpoint.__init__(self, reactor, interface, port, maxclients, channels, maxdown=maxdown, maxup=maxup, max_duplicate_peers=max_duplicate_peers)

    def _get_and_reset_bytes_received(self):
        if self._enet_host is None: return 0
        try:
            return self._enet_host.total_received_data
        finally:
            self._enet_host.reset_total_received_data()

    def _get_and_reset_bytes_sent(self):
        if self._enet_host is None: return 0
        try:
            return self._enet_host.total_sent_data
        finally:
            self._enet_host.reset_total_sent_data()

    def _get_peer_count(self):
        if self._enet_host is None: return 0
        return self._enet_host.peer_count
