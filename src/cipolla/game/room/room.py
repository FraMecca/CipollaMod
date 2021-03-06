import math
import traceback

from twisted.internet import reactor, defer # type: ignore
from twisted.internet.defer import Deferred # type: ignore

from cube2common.constants import MAXROOMLEN, MAXSERVERDESCLEN, MAXSERVERLEN, mastermodes, privileges
from cube2protocol.cube_data_stream import CubeDataStream # type: ignore
from cipolla.game.client.exceptions import InsufficientPermissions, GenericError
from cipolla.game.room.client_collection import ClientCollection
from cipolla.game.room.player_collection import PlayerCollection
from cipolla.game.room.game_event_handler import GameEventHandler
from cipolla.game.room.room_broadcaster import RoomBroadcaster
from cipolla.game.room.room_entry_context import RoomEntryContext
from cipolla.game.room.room_map_mode_state import RoomMapModeState
from cipolla.game.map.map_rotation import MapRotation, test_rotation_dict
from cipolla.game.server_message_formatter import smf, format_cfg_message
from cipolla.game.map.team import Team
from cipolla.game.timing.game_clock import GameClock
from cipolla.config_manager import ConfigManager
from cipolla.protocol import swh
from cipolla.utils.truncate import truncate


from cipolla.game.client.client import Client
from cipolla.game.gamemode.insta import Insta # type: ignore
from cipolla.game.map.async_map_meta_data_accessor import AsyncMapMetaDataAccessor
from cipolla.mods.abstract_mod import AbstractMod
from cipolla.game.player.player import Player
from typing import Any, Callable, Dict, Iterator, List, Tuple, Optional, Set

from cipolla.utils.tracing import tracer # type: ignore

class Room(object):
    '''
    The room serves as the central hub for all players who are in the same game.
    It provides four things;
    * Event handling functions which accept client events
    * Event handling functions which accept player events
    * Accessors to query the state of the room.
    * Setters to modify the state of the room.
    '''
    def __init__(self, room_name: str, map_meta_data_accessor: Optional[AsyncMapMetaDataAccessor] = None, defaultGameMode: str = 'ffa') -> None:
        self._game_clock = GameClock()
        self._attach_game_clock_event_handlers()

        self._server_name = ConfigManager().server.name
        self._name = room_name

        self._clients = ClientCollection()
        self._players = PlayerCollection()
        self._mods: Dict[str, AbstractMod] = {}
        self._messages = ConfigManager().rooms[room_name].messages

        # '123.321.123.111': {client, client, client}
        self._client_ips: Dict = {}

        self.maxplayers = ConfigManager().rooms[self._name].maxplayers

        self.decommissioned = False

        # self.mastermask = 0 if self.temporary else -1
        self.mastermask = -1
        self.mastermode = 0
        self.resume_delay = 3

        self.last_destination_room = None

        # Holds the client objects with each level of permissions
        self.masters: Set[Client] = set()
        self.auths: Set[Client] = set()
        self.admins: Set[Client] = set()

        self._player_event_handler = GameEventHandler()

        # map_rotation_data = test_rotation_dict
        # don't load this, load the one specified in config
        gamemode = ConfigManager().maps.mode_indexes[defaultGameMode]
        map_rotation = MapRotation.from_dictionary(*ConfigManager().get_rotation_dict(), defaultMode=gamemode)
        self._map_mode_state = RoomMapModeState(self, map_rotation, map_meta_data_accessor, self._game_clock)

        self._broadcaster = RoomBroadcaster(self._clients, self._players)

        self.await_map_mode_initialized() # start game immediately, even if no players

        reactor.addSystemEventTrigger('before', 'flush_bindings', self._flush_messages)


    ###########################################################################
    #######################        Accessors        ###########################
    ###########################################################################

    def __format__(self, format_spec):
        return smf.format("{room#room.name}", room=self)

    @property
    def name(self):
        return self._name

    @property
    def server_name(self) -> str:
        return self._server_name

    @name.setter # type: ignore # TODO: get rid of this
    def name(self, value):
        self._name = truncate(value, MAXROOMLEN)

    @property
    def lan_info_name(self):
        server_name = truncate(self._server_name, MAXSERVERLEN)
        # room_title = smf.format("{server_name} #{room.name}", room=self, server_name=server_name)
        room_title = self.name
        return room_title

    def get_entry_context(self, client: Client, player: Player) -> RoomEntryContext:
        '''
        Returns an object which encapsulates the details about a client request
        to join this room.
        This gives the room an opportunity to raise exceptions before any
        work change actually happen. (for example room being full, or private.)
        '''
        return RoomEntryContext(client)

    @property
    def clients(self):
        return self._clients.to_iterator()

    @property
    def players(self):
        return self._players.to_iterator()

    @property
    def teams_size(self) -> Dict[str, Tuple[int, Team, List[Any]]]:
        teams = {team.name: (len(players), team, players) for team, players in self._players.by_team(self.gamemode.teams).items()}

        # add base teams
        if 'good' not in teams.keys():
            teams['good'] = (0, Team(0, 'good'), [])
        if 'evil' not in teams:
            teams['evil'] = (0, Team(0, 'evil'), [])

        return teams

    @property
    def teams(self):
        assert self.is_teammode
        return self.gamemode.teams

    @property
    def playing_count(self):
        count = 0
        for player in self.players:
            if not player.state.is_spectator:
                count += 1
        return count

    @property
    def player_count(self) -> int:
        return self._clients.count

    @property
    def empty(self):
        return self.player_count == 0

    def get_client(self, cn):
        return self._clients.by_cn(cn)

    def get_player(self, pn):
        return self._players.by_pn(pn)

    def get_player_by_name(self, name):
        players = dict(map(lambda p: (p.name, p), self.players))
        return players.get(name, None)

    @property
    def is_paused(self) -> bool:
        return self._game_clock.is_paused

    @property
    def is_resuming(self):
        return self._game_clock.is_resuming

    @property
    def is_intermission(self) -> bool:
        return self._game_clock.is_intermission

    @property
    def timeleft(self):
        return int(math.ceil(self._game_clock.timeleft))

    @timeleft.setter
    def timeleft(self, seconds):
        self._game_clock.timeleft = seconds

    @property
    def gamemillis(self):
        return int(self._game_clock.time_elapsed * 1000)

    @property
    def gamemode(self) -> Insta: # TODO: fix, it is gamemode base
        return self._map_mode_state.gamemode

    @property
    def map_name(self):
        return self._map_mode_state.map_name

    @property
    def mode_num(self):
        return self._map_mode_state.mode_num

    @property
    def is_teammode(self) -> bool:
        return self.gamemode.hasteams

    @property
    def mode_name(self):
        return self._map_mode_state.mode_name

    def is_name_duplicate(self, name):
        return self._players.is_name_duplicate(name)

    def contains_client_with_ip(self, client_ip):
        return client_ip in self._client_ips

    def is_mod_active(self, mod_name: str) -> bool:
        return mod_name in self._mods

    def get_mod(self, mod_name):
        return self._mods[mod_name]

    def add_mod(self, mod):
        self._mods[mod.name] = mod

    def del_mod(self, mod):
        assert self._mods[mod.name] is mod
        del self._mods[mod.name]

    def admins_present(self):
        return bool(self.admins)

    def masters_present(self):
        return bool(self.masters)

    ###########################################################################
    #######################         Setters         ###########################
    ###########################################################################

    @defer.inlineCallbacks
    def client_enter(self, entry_context: RoomEntryContext) -> Iterator[Deferred]:
        yield self.await_map_mode_initialized()

        client = entry_context.client
        player = client.get_player()

        player.state.use_game_clock(self._game_clock)

        self._initialize_client(client)
        self._broadcaster.client_connected(client)

        self._clients.add(client)
        self._players.add(player)

        if not client.host in self._client_ips:
            self._client_ips[client.host] = set()
        self._client_ips[client.host].add(client)

        if client in self.admins or client in self.masters or client in self.auths:
            self._update_current_masters()

        self.gamemode.on_player_connected(player)

    def client_leave(self, client: Client) -> None:
        self._clients.remove(client)
        for player in client.player_iter():
            self._player_disconnected(player)

        if client in self.masters or client in self.admins:
            self.masters.discard(client)
            self.auths.discard(client)
            self.admins.discard(client)

        clients_with_ip = self._client_ips.get(client.host, set())
        clients_with_ip.discard(client)
        if len(clients_with_ip) == 0:
            del self._client_ips[client.host]

        with client.sendbuffer(1, True) as cds:
            for remaining_client in self._clients.to_iterator():
                swh.put_cdis(cds, remaining_client)

    @tracer
    def pause(self):
        self._game_clock.pause()
    @tracer
    def resume(self) -> None:
        self._game_clock.resume(self.resume_delay)

    def set_resuming_state(self):
        "Used to set the game clock into the resuming state pending some external event."
        self._game_clock.set_resuming_state()

    def end_match(self):
        self._game_clock.timeleft = 0

    def change_map_mode(self, map_name: str, mode_name: str) -> Deferred:
        self._game_clock.cancel()
        return self._map_mode_state.change_map_mode(map_name, mode_name)

    def rotate_map_mode(self):
        self._game_clock.cancel()
        return self._map_mode_state.rotate_map_mode()

    def await_map_mode_initialized(self) -> Deferred:
        return self._map_mode_state.await_map_mode_initialized(self.player_count)

    def set_mastermode(self, mastermode):
        self.mastermode = mastermode
        self._update_current_masters()

    @property
    def broadcastbuffer(self) -> Callable:
        return self._broadcaster.broadcastbuffer

    def server_message(self, message, exclude=()):
        self._broadcaster.server_message(message, exclude)

    ###########################################################################
    #######################  Client event handling  ###########################
    ###########################################################################

    @tracer
    def handle_client_event(self, event_name: str, client: Client, *args, **kwargs) -> None:
        handler = client.role.handle_event
        deferred = defer.maybeDeferred(handler, event_name, self, client, *args, **kwargs)
        deferred.addErrback(client.handle_exception)

    ###########################################################################
    #######################  Player event handling  ###########################
    ###########################################################################

    def handle_player_event(self, event_name: str, player: Player, *args, **kwargs) -> None:
        handler = self._player_event_handler.handle_event
        deferred = defer.maybeDeferred(handler, event_name, self, player, *args, **kwargs)
        deferred.addErrback(player.client.handle_exception)

    ###########################################################################
    #####################  Game clock event handling  #########################
    ###########################################################################

    def _attach_game_clock_event_handlers(self) -> None:
        self._game_clock.add_resumed_callback(self._on_game_clock_resumed)
        self._game_clock.add_paused_callback(self._on_game_clock_paused)
        self._game_clock.add_resume_countdown_tick_callback(self._on_game_clock_resume_countdown_tick)
        self._game_clock.add_timeleft_altered_callback(self._on_game_clock_timeleft_altered)
        self._game_clock.add_intermission_started_callback(self._on_game_clock_intermission)
        self._game_clock.add_intermission_ended_callback(self._on_game_clock_intermission_ended)

    def _on_game_clock_resumed(self) -> None:
        self._broadcaster.resume()
        if not self.gamemode or not self.gamemode.initialized:
            self.gamemode.initialize()

    def _on_game_clock_paused(self):
        self._broadcaster.pause()

    def _on_game_clock_resume_countdown_tick(self, seconds):
        self._broadcaster.server_message(smf.format("Resuming in {value#seconds}...", seconds=seconds))

    def _on_game_clock_timeleft_altered(self, seconds):
        self._broadcaster.time_left(int(math.ceil(seconds)))

    def _on_game_clock_intermission(self):
        self._broadcaster.intermission()

    def _on_game_clock_intermission_ended(self):
        self._broadcaster.server_message("Intermission has ended.")
        try:
            self.rotate_map_mode()
        except:
            traceback.print_exc()

    ###########################################################################
    #######################  Other private methods  ###########################
    ###########################################################################

    def _flush_messages(self) -> None:
        if not self.decommissioned:
            reactor.callLater(0, reactor.addSystemEventTrigger, 'before', 'flush_bindings', self._flush_messages)
        self._broadcaster.flush_messages()

    def _initialize_client_match_data(self, cds: CubeDataStream, client: Client) -> None:
        player = client.get_player()

        swh.put_mapchange(cds, self._map_mode_state.map_name, self._map_mode_state.mode_num, hasitems=False)

        if self.gamemode.timed and self.timeleft is not None:
            swh.put_timeup(cds, self.timeleft)

        if self.is_paused:
            swh.put_pausegame(cds, 1)

        if self.mastermode >= mastermodes.MM_LOCKED:
            player.state.is_spectator = True
            swh.put_spectator(cds, player)

        self.gamemode.initialize_player(cds, player)

        if not player.state.is_spectator and not self.is_intermission:
            player.state.respawn()
            self.gamemode.spawn_loadout(player)
            swh.put_spawnstate(cds, player)

    def _initialize_client(self, client: Client) -> None:
        existing_players = list(self.players)

        with client.sendbuffer(1, True) as cds:
            swh.put_welcome(cds)
            self._put_room_title(cds, client)

            possible_privileged_clients = [client] + self._clients.to_list()

            swh.put_currentmaster(cds, self.mastermode, possible_privileged_clients)

            self._initialize_client_match_data(cds, client)

            swh.put_initclients(cds, existing_players)
            swh.put_resume(cds, existing_players)

        if 'server_welcome' in self._messages:
            message = self._messages['server_welcome']
            formatted = format_cfg_message(message, self, client.get_player())
            defer.maybeDeferred(client.send_server_message, formatted)
        if 'player_connect' in self._messages:
            message = self._messages['player_connect']
            formatted = format_cfg_message(message, self, client.get_player())
            defer.maybeDeferred(self.public_message, formatted)

    def _player_disconnected(self, player: Player) -> None:
        self._players.remove(player)
        self._broadcaster.player_disconnected(player)
        self.gamemode.on_player_disconnected(player)
        if 'server_goodbye' in self._messages:
            message = self._messages['server_goodbye']
            formatted = format_cfg_message(message, self, player)
            defer.maybeDeferred(player.client.send_server_message, formatted)
        if 'player_disconnect' in self._messages:
            message = self._messages['player_disconnect']
            formatted = format_cfg_message(message, self, player)
            defer.maybeDeferred(self.public_message, formatted)

    def _get_room_title(self) -> str:
        server_name = truncate(self._server_name, MAXSERVERLEN)
        # room_title = smf.format("{server_name} {room_title#room.name}", room=self, server_name=server_name)
        room_title = self.name
        return room_title

    def _put_room_title(self, cds: CubeDataStream, client: Client) -> None:
        room_title = truncate(self._get_room_title(), MAXSERVERDESCLEN)
        swh.put_servinfo(cds, client, haspwd=False, description=room_title, domain='')

    def _send_room_title(self, client):
        with client.sendbuffer(1, True) as cds:
            self._put_room_title(cds, client)

    def _on_name_changed(self, *args):
        for client in self.clients:
            self._send_room_title(client)

    def public_message(self, msg: str) -> None:
        if msg:
            self._broadcaster.server_message(msg)

    def _set_player_spectator(self, player, spectate):
        if not spectate and player.state.is_spectator:
            self.gamemode.on_player_unspectate(player)

        elif spectate and not player.state.is_spectator:
            self.gamemode.on_player_spectate(player)

        else:
            print("invalid change")

    def _update_current_masters(self) -> None:
        self._broadcaster.current_masters(self.mastermode, self.clients)

    def change_privilege(self, target: Client, requested_privilege: int) -> None:
        from cipolla.game.room.roles import AdminRole, MasterRole, BaseRole
        if requested_privilege == privileges.PRIV_NONE:
            target.role = BaseRole()
            self.admins.discard(target)
            self.auths.discard(target)
            self.masters.discard(target)
        elif requested_privilege == privileges.PRIV_MASTER:
            target.role = MasterRole()
            self.masters.add(target)
        elif requested_privilege == privileges.PRIV_AUTH:
            self.auths.add(target)
        elif requested_privilege == privileges.PRIV_ADMIN:
            target.role = AdminRole()
            self.admins.add(target)
        self._update_current_masters()

    def get_target_client(self, target_pn):
        if target_pn.is_digit():
            return room.get_client(int(target_pn))
        else:
            return None
