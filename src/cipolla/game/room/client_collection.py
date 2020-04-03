import contextlib

from cube2protocol.cube_data_stream import CubeDataStream # type: ignore

from cipolla.game.client.client import Client
from cipolla.game.player.player import Player
from typing import Any, Iterator, List, Optional, Tuple, Union, Set, Dict, Iterable

class ClientCollection(object):
    def __init__(self) -> None:
        # cn: client
        self._clients: Dict[int, Client] = {}

    def add(self, client: Client) -> None:
        self._clients[client.cn] = client

    def remove(self, client: Client) -> None:
        del self._clients[client.cn]

    @property
    def count(self) -> int:
        return len(self._clients)

    def to_list(self) -> List[Any]:
        return list(self._clients.values())

    def to_iterator(self):
        return iter(self._clients.values())

    def by_cn(self, cn):
        return self._clients.get(cn, None)

    def broadcast(self, channel: int, data: CubeDataStream, reliable: bool = False, _exclude: Optional[Union[List[Client], List[Player], Tuple]] = None, _clients: Optional[List[Client]] = None) -> None:
        from cipolla.game.player.player import Player
        clients = _clients or self._clients.values()
        exclude = set(_exclude or ())
        for v in tuple(exclude):
            if isinstance(v, Player):
                exclude.add(v.client)
        for client in clients:
            if not client in exclude:
                client.send(channel, data, reliable)

    @contextlib.contextmanager
    def broadcastbuffer(self, channel: int, reliable: bool = False, exclude: Optional[Union[List[Client], Tuple, List[Player]]] = None, clients: Optional[List[Client]] = None) -> Iterator[CubeDataStream]:
        cds = CubeDataStream()
        yield cds
        self.broadcast(channel, cds, reliable, exclude, clients)
