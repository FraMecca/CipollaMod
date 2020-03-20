import contextlib

from cube2protocol.cube_data_stream import CubeDataStream
from spyd.game.player.player import Player


class ClientCollection(object):
    def __init__(self):
        # cn: client
        self._clients = {}

    def add(self, client):
        self._clients[client.cn] = client

    def remove(self, client):
        del self._clients[client.cn]

    @property
    def count(self):
        return len(self._clients)

    def to_list(self):
        return list(self._clients.values())

    def to_iterator(self):
        return iter(self._clients.values())

    def by_cn(self, cn):
        return self._clients[cn]

    def broadcast(self, channel, data, reliable=False, exclude=None, clients=None):
        clients = clients or iter(self._clients.values())
        exclude = set(exclude or ())
        for v in tuple(exclude):
            if isinstance(v, Player):
                exclude.add(v.client)
        for client in clients:
            if not client in exclude:
                client.send(channel, data, reliable)

    @contextlib.contextmanager
    def broadcastbuffer(self, channel, reliable=False, exclude=[], clients=None):
        cds = CubeDataStream()
        yield cds
        self.broadcast(channel, cds, reliable, exclude, clients)
