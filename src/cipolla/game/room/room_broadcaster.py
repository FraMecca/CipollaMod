import contextlib
import traceback

from cube2protocol.cube_data_stream import CubeDataStream
from cipolla.protocol import swh


from cipolla.game.client.client import Client
from cipolla.game.player.player import Player
from cipolla.game.room.client_collection import ClientCollection
from cipolla.game.room.player_collection import PlayerCollection
from cube2common.vec import vec
from typing import Callable, Iterator, Tuple
class RoomBroadcaster(object):
    def __init__(self, client_collection: ClientCollection, player_collection: PlayerCollection) -> None:
        self._client_collection = client_collection
        self._player_collection = player_collection

    @contextlib.contextmanager
    def broadcastbuffer(self, channel: int, reliable: bool, *args) -> Iterator[CubeDataStream]:
        with self.clientbuffer(channel, reliable, *args) as cds:
            yield cds

    @property
    def clientbuffer(self) -> Callable:
        return self._client_collection.broadcastbuffer

    def resume(self) -> None:
        with self.broadcastbuffer(1, True) as cds:
            swh.put_pausegame(cds, 0)

    def pause(self):
        with self.broadcastbuffer(1, True) as cds:
            swh.put_pausegame(cds, 1)

    def time_left(self, seconds):
        with self.broadcastbuffer(1, True) as cds:
            swh.put_timeup(cds, seconds)

    def intermission(self):
        self.time_left(0)

    def shotfx(self, player: Player, gun: int, shot_id: int, from_pos: vec, to_pos: vec) -> None:
        with self.broadcastbuffer(1, True, [player]) as cds:
            swh.put_shotfx(cds, player, gun, shot_id, from_pos, to_pos)

    def explodefx(self, player, gun, explode_id):
        with self.broadcastbuffer(1, True, [player]) as cds:
            swh.put_explodefx(cds, player, gun, explode_id)

    def player_died(self, player, killer, teams):
        with self.broadcastbuffer(1, True) as cds:
            swh.put_died(cds, player, killer, teams)

    def player_disconnected(self, player: Player) -> None:
        with self.broadcastbuffer(1, True) as cds:
            swh.put_cdis(cds, player)

    def teleport(self, player, teleport, teledest):
        with self.broadcastbuffer(0, True, [player]) as cds:
            swh.put_teleport(cds, player, teleport, teledest)

    def jumppad(self, player, jumppad):
        with self.broadcastbuffer(0, True, [player]) as cds:
            swh.put_jumppad(cds, player, jumppad)

    def server_message(self, message: str, exclude: Tuple = ()) -> None:
        with self.broadcastbuffer(1, True, exclude) as cds:
            swh.put_servmsg(cds, message)

    def client_connected(self, client: Client) -> None:
        player = client.get_player()
        with self.broadcastbuffer(1, True, [client]) as cds:
            swh.put_resume(cds, [player])
            swh.put_initclients(cds, [player])

    def current_masters(self, mastermode, clients):
        with self.broadcastbuffer(1, True) as cds:
            swh.put_currentmaster(cds, mastermode, clients)

    def sound(self, sound):
        for client in self._client_collection.to_iterator():
            with client.sendbuffer(1, True) as cds:
                tm = CubeDataStream()
                swh.put_sound(tm, sound)
                swh.put_clientdata(cds, client, str(tm))

    def flush_messages(self) -> None:
        try:
            class ClientBufferReference(object):
                def __init__(self, client, positions_next_byte, positions_size, messages_next_byte, messages_size):
                    self.client = client
                    self.positions_next_byte = positions_next_byte
                    self.positions_size = positions_size
                    self.messages_next_byte = messages_next_byte
                    self.messages_size = messages_size

            room_positions = CubeDataStream()
            room_messages = CubeDataStream()

            references = []

            positions_next_byte = 0
            messages_next_byte = 0

            for client in self._client_collection.to_iterator():
                player = client.get_player()

                positions_first_byte = positions_next_byte
                messages_first_byte = messages_next_byte

                player.write_state(room_positions, room_messages)

                positions_next_byte = len(room_positions)
                messages_next_byte = len(room_messages)

                positions_size = positions_next_byte - positions_first_byte
                messages_size = messages_next_byte - messages_first_byte

                references.append(ClientBufferReference(client, positions_next_byte, positions_size, messages_next_byte, messages_size))

            positions_len = len(room_positions)
            messages_len = len(room_messages)

            room_positions.write(room_positions)
            room_messages.write(room_messages)

            position_data = memoryview(room_positions.data)
            message_data = memoryview(room_messages.data)

            for ref in references:
                client = ref.client

                pnb = ref.positions_next_byte
                mnb = ref.messages_next_byte

                psize = ref.positions_size
                msize = ref.messages_size

                if positions_len - psize > 0:
                    # TODO: Use no_allocate option here
                    client.send(0, position_data[pnb:pnb + (positions_len - psize)], False, False)

                if messages_len - msize > 0:
                    # TODO: Use no_allocate option here
                    client.send(1, message_data[mnb:mnb + (messages_len - msize)], True, False)

            for player in self._player_collection.to_iterator():
                player.state.clear_flushed_state()
        except:
            traceback.print_exc()
