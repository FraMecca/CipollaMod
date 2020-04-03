from twisted.internet import reactor # type: ignore

from cipolla.game.client.exceptions import InvalidPlayerNumberReference
from cipolla.game.player.player import Player

from typing import Dict

class ClientPlayerCollection(object):
    def __init__(self, cn: int) -> None:
        self.cn = cn
        self.players: Dict[int, Player] = {}

    def has_pn(self, pn: int = -1) -> bool:
        if pn == -1:
            pn = self.cn

        return pn in self.players

    def get_player(self, pn: int = -1) -> Player:
        if pn == -1:
            pn = self.cn

        if pn in self.players:
            return self.players[pn]
        else:
            raise InvalidPlayerNumberReference(pn)

    def add_player(self, player: Player) -> None:
        self.players[player.pn] = player

    def cleanup_players(self) -> None:
        for player in self.players.values():
            reactor.callLater(60, self._cleanup_player, player)

    def _cleanup_player(self, player):
        player.cleanup()

    def player_iter(self):
        return iter(self.players.values())
