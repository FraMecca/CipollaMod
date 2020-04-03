import uuid

from cipolla.game.player.player_state import PlayerState
from cipolla.game.server_message_formatter import smf
from cipolla.protocol import swh # type: ignore

from typing import Dict, Any

from cube2protocol.cube_data_stream import CubeDataStream
from typing import Callable
from cipolla.game.client.client import Client

class Player(object):

    instances_by_uuid: Dict[str, Any] = {} # TODO: put player

    def __init__(self, client: Client, playernum: int, name: str, playermodel: int) -> None:
        self.client = client
        self._pn: int = playernum
        self.name: str = ''.join(name)
        self.playermodel: int = playermodel
        self._team: str = ""
        self._isai: bool = False
        self._uuid: str = str(uuid.uuid4())

        Player.instances_by_uuid[self.uuid] = self

        self._state: PlayerState = PlayerState()

    @property
    def cn(self) -> int:
        return self._pn

    @property
    def pn(self) -> int:
        return self._pn

    @property
    def ping(self):
        return self.client.ping

    @property
    def privilege(self) -> int:
        if self.isai: return 0
        else: return self.client.privilege

    @property
    def state(self) -> PlayerState:
        return self._state

    @property
    def isai(self) -> bool:
        return self._isai

    @property
    def uuid(self) -> str:
        return self._uuid

    @property
    def room(self):
        return self.client.room

    @property
    def shares_name(self) -> bool:
        return self.room.is_name_duplicate(self.name)

    def __format__(self, format_spec):
        if self.shares_name or self.isai:
            fmt = "{name#player.name} {pn#player.pn}"
        else:
            fmt = "{name#player.name}"

        return smf.format(fmt, player=self)

    def on_respawn(self, lifesequence, gunselect):
        self.state.on_respawn(lifesequence, gunselect)

    def write_state(self, room_positions: CubeDataStream, room_messages: CubeDataStream) -> None:
        if self.state.position is not None:
            room_positions.write(self.state.position)

        if not self.state.messages.empty():
            swh.put_clientdata(room_messages, self, self.state.messages)

    def cleanup(self):
        Player.instances_by_uuid.pop(self.uuid, None)

    def send(self, channel, data, reliable):
        return self.client.send(channel, data, reliable)

    def send_server_message(self, message):
        self.client.send_server_message(message)

    @property
    def sendbuffer(self) -> Callable:
        return self.client.sendbuffer
