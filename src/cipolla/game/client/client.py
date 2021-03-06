import contextlib
import logging
import time
import traceback

from twisted.internet import reactor # type: ignore
from twisted.python.failure import Failure # type: ignore

from cube2common.constants import disconnect_types, MAXNAMELEN # type: ignore
from cube2protocol.cube_data_stream import CubeDataStream # type: ignore
from cipolla.game.client.exceptions import *
from cipolla.game.room.exceptions import *
from cipolla.game.room.exceptions import RoomEntryFailure
from cipolla.game.server_message_formatter import error, smf, denied, state_error, usage_error
from cipolla.protocol import swh
from cipolla.utils.constrain import ConstraintViolation
from cipolla.utils.filtertext import filtertext
from cipolla.utils.ping_buffer import PingBuffer
from cipolla.utils.tracing import tracer

from typing import Dict, Iterator, List, Union
logger = logging.getLogger(__name__)

class Client(object):
    '''
    Handles the per client networking, and distributes the messages out to the players (main, bots).
    '''
    def __init__(self, protocol, clientnum_handle, room, auth_world_view, servinfo_domain, punitive_model):
        from cipolla.game.room.room import Room
        from cipolla.game.room.roles import BaseRole, MasterRole, AdminRole
        from cipolla.game.client.client_player_collection import ClientPlayerCollection
        from cipolla.game.client.client_auth_state import ClientAuthState

        self.cn_handle = clientnum_handle
        self.cn = clientnum_handle.cn
        self.room: Room = room
        self.role = BaseRole()
        self.connection_sequence_complete = False

        self._client_player_collection = ClientPlayerCollection(self.cn)

        self.protocol_wrapper = protocol
        self.host = protocol.transport.host
        self.port = protocol.transport.port

        self.ping_buffer = PingBuffer()

        self.connect_time = int(time.time())

        self._ignored_preconnect_message_types = ("N_POS", "N_PING")
        self._allowed_preconnect_message_types = ("N_CONNECT", "N_AUTHANS")
        self._ignore_client_messages = False

        self._client_auth_state = ClientAuthState(self, auth_world_view)

        self._servinfo_domain = servinfo_domain

        self._punitive_model = punitive_model


        self.command_context = {}


    def __format__(self, format_spec):
        player = self.get_player()

        if player.shares_name or player.isai:
            fmt = "{name#player.name} {pn#player.pn}"
        else:
            fmt = "{name#player.name}"

        return smf.format(fmt, player=player)

    def connected(self) -> None:
        print("connect:", self.host)
        with self.sendbuffer(1, True) as cds:
            swh.put_servinfo(cds, self, haspwd=False, description="", domain=self._servinfo_domain)

        self.connect_timeout_deferred = reactor.callLater(1, self.connect_timeout)

    def disconnected(self) -> None:
        print("disconnect:", self.host)
        if self.is_connected:
            self.room.client_leave(self)

        self.cn_handle.release()
        self._client_player_collection.cleanup_players()

    def connect_timeout(self):
        '''Disconnect client because it didn't send N_CONNECT soon enough.'''
        self.disconnect(disconnect_types.DISC_NONE, message=error("Hey What's up, you didn't send an N_CONNECT message!"))

    def connect_received(self, message: Dict[str, Union[str, int]]) -> None:
        '''Create the main player instance for this client and join room.'''
        from cipolla.game.player.player import Player
        if not self.connect_timeout_deferred.called:
            self.connect_timeout_deferred.cancel()

        assert isinstance(message['name'], str)
        assert isinstance(message['playermodel'], int), message
        assert isinstance(message['authname'], str)
        # TODO refactor and include checking of incoming msgs

        name = filtertext(message['name'], False, MAXNAMELEN)
        playermodel = message['playermodel']
        player = Player(self, self.cn, name, playermodel)
        self.add_player(player)

        assert isinstance(message['pwdhash'], str)
        assert isinstance(message['authname'], str)
        pwdhash: str = message['pwdhash']
        authdomain = message['authdomain']
        authname: str = message['authname']

        if len(authname) > 0:
            deferred = self.auth(authdomain, authname)
            deferred.addCallbacks(self.connection_auth_finished, lambda e: self.connection_auth_finished(None, pwdhash), (pwdhash,))
        else:
            self.connection_auth_finished(None, pwdhash)

    def connection_auth_finished(self, authentication: None, pwdhash: str) -> None:
        player = self.get_player()

        ban_info = self._punitive_model.get_effect('ban', self.host)
        if ban_info is not None and not ban_info.expired:
            return self.disconnect(disconnect_types.DISC_IPBAN, error("You are banned."))

        try:
            room_entry_context = self.room.get_entry_context(self, player)
        except RoomEntryFailure as e:
            return self.disconnect(e.disconnect_type, str(e))

        self.room.client_enter(room_entry_context)

        self.connection_sequence_complete = True

    def send_server_message(self, message: str) -> None:
        if message:
            with self.sendbuffer(1, True) as cds:
                swh.put_servmsg(cds, message)

    def change_role(self, new_role):
        self.role = new_role

    @property
    def is_connected(self) -> bool:
        return self.has_pn() and self.connection_sequence_complete

    @property
    def uuid(self):
        return self.get_player().uuid

    @property
    def ping(self):
        return self.ping_buffer.avg()

    @property
    def time_online(self):
        return int(time.time()) - self.connect_time

    def has_pn(self, pn: int = -1) -> bool:
        return self._client_player_collection.has_pn(pn=pn)

    def get_player(self, pn: int = -1):
        return self._client_player_collection.get_player(pn=pn)

    def add_player(self, player) -> None:
        self._client_player_collection.add_player(player)

    def player_iter(self):
        return self._client_player_collection.player_iter()

    def send(self, channel: int, data: CubeDataStream, reliable: bool, no_allocate: bool = False) -> None:
        if type(data) == memoryview:
            data = data.tobytes()
        elif type(data) == CubeDataStream:
            data = memoryview(data.data).tobytes()
        elif type(data) != str:
            data = str(data)
        self.protocol_wrapper.send(channel, data, reliable, no_allocate)

    @contextlib.contextmanager
    def sendbuffer(self, channel: int, reliable: bool) -> Iterator[CubeDataStream]:
        cds = CubeDataStream()
        yield cds
        self.send(channel, cds, reliable)

    def disconnect(self, disconnect_type, message=None, timeout=3.0):
        self.protocol_wrapper.disconnect_with_message(disconnect_type, message, timeout)

    def auth(self, authdomain, authname):
        return self._client_auth_state.auth(authdomain, authname)

    def answer_auth_challenge(self, authdomain, authid, answer):
        return self._client_auth_state.answer_auth_challenge(authdomain, authid, answer)

    def handle_exception(self, e):
        if isinstance(e, Failure):
            e = e.value

        if isinstance(e, InsufficientPermissions):
            self.send_server_message(denied(e.message))
        elif isinstance(e, StateError):
            self.send_server_message(state_error(e.message))
        elif isinstance(e, UsageError):
            self.send_server_message(usage_error(e.message))
        elif isinstance(e, GenericError):
            self.send_server_message(error(e.message))
        elif isinstance(e, UnknownEvent):
            print(f"Unhandled player event: {str(e)}")
        elif isinstance(e, ConstraintViolation):
            print("Disconnecting client {} due to constraint violation {}.".format(self.host, e.constraint_name))
            self.disconnect(disconnect_types.DISC_MSGERR)

    def _message_received(self, message_type: str, message: Dict[str, Union[str, int, List[int], bytes, List]]) -> None:
        if self._ignore_client_messages: return
        try:
            if (not self.is_connected) and (message_type in self._ignored_preconnect_message_types):
                pass
            elif (not self.is_connected) and (message_type not in self._allowed_preconnect_message_types):
                self.disconnect(disconnect_types.DISC_MSGERR)
                return
            else:
                try:
                    self.role.handle_message(self, self.room, message_type, message)
                except UnknownMessage as e:
                    print("Client received unhandled message type:", message_type, message)
                    pass
                except (InsufficientPermissions, StateError, UsageError, GenericError, ConstraintViolation) as e:
                    self.handle_exception(e)
        except ConstraintViolation as e:
            pass  # Plenty of information already printed.
        except:
            traceback.print_exc()
            self.disconnect(disconnect_types.DISC_MSGERR)
            self._ignore_client_messages = True

    @property
    def privilege(self) -> int:
        return self.role.privilege
