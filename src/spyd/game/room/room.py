import math
import traceback

from twisted.internet import reactor, defer

from cube2common.constants import MAXROOMLEN, MAXSERVERDESCLEN, MAXSERVERLEN, mastermodes, privileges
from spyd.game.client.exceptions import InsufficientPermissions, GenericError
from spyd.game.room.client_collection import ClientCollection
from spyd.game.room.player_collection import PlayerCollection
from spyd.game.room.game_event_handler import GameEventHandler
from spyd.game.room.room_broadcaster import RoomBroadcaster
from spyd.game.room.room_entry_context import RoomEntryContext
from spyd.game.room.room_map_mode_state import RoomMapModeState
from spyd.game.map.map_rotation import MapRotation, test_rotation_dict
from spyd.game.server_message_formatter import smf, format_cfg_message
from spyd.game.timing.game_clock import GameClock
from spyd.config_manager import ConfigManager
from spyd.protocol import swh
from spyd.utils.truncate import truncate


class Room(object):
    '''
    The room serves as the central hub for all players who are in the same game.
    It provides four things;
    * Event handling functions which accept client events
    * Event handling functions which accept player events
    * Accessors to query the state of the room.
    * Setters to modify the state of the room.
    '''
    def __init__(self, room_name=None, map_meta_data_accessor=None):
        self._game_clock = GameClock()
        self._attach_game_clock_event_handlers()

        self._server_name = ConfigManager().server.name
        self._name = room_name

        self._clients = ClientCollection()
        self._players = PlayerCollection()
        self._mods = {} # TODO: activate mods at room initialization
        self._messages = ConfigManager().rooms[room_name].messages

        # '123.321.123.111': {client, client, client}
        self._client_ips = {}

        self.maxplayers = ConfigManager().rooms[self._name].maxplayers

        self.decommissioned = False

        # self.mastermask = 0 if self.temporary else -1
        self.mastermask = -1
        self.mastermode = 0
        self.resume_delay = None

        self.last_destination_room = None

        # Holds the client objects with each level of permissions
        self.masters = set()
        self.auths = set()
        self.admins = set()

        self._player_event_handler = GameEventHandler()

        map_rotation_data = test_rotation_dict
        map_rotation = MapRotation.from_dictionary(map_rotation_data)
        self._map_mode_state = RoomMapModeState(self, map_rotation, map_meta_data_accessor, self._game_clock)

        self._broadcaster = RoomBroadcaster(self._clients, self._players)


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
    def server_name(self):
        return self._server_name

    @name.setter
    def name(self, value):
        self._name = truncate(value, MAXROOMLEN)

    @property
    def lan_info_name(self):
        server_name = truncate(self._server_name, MAXSERVERLEN)
        # room_title = smf.format("{server_name} #{room.name}", room=self, server_name=server_name)
        room_title = self.name
        return room_title

    def get_entry_context(self, client, player):
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
    def teams_size(self):
        from spyd.game.gamemode.bases.teamplay_base import base_teams
        teams = {team.name: (len(players), team, players) for team, players in self._players.by_team().items()}

        # add base teams
        if 'good' not in teams:
            teams['good'] = (0, base_teams['good'], [])
        if 'evil' not in teams:
            teams['evil'] = (0, base_teams['evil'], [])

        return teams


    @property
    def playing_count(self):
        count = 0
        for player in self.players:
            if not player.state.is_spectator:
                count += 1
        return count

    @property
    def player_count(self):
        return self._clients.count

    @property
    def empty(self):
        return self.player_count == 0

    def get_client(self, cn):
        return self._clients.by_cn(cn)

    def get_player(self, pn):
        return self._players.by_pn(pn)

    @property
    def is_paused(self):
        return self._game_clock.is_paused

    @property
    def is_resuming(self):
        return self._game_clock.is_resuming

    @property
    def is_intermission(self):
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
    def gamemode(self):
        return self._map_mode_state.gamemode

    @property
    def map_name(self):
        return self._map_mode_state.map_name

    @property
    def mode_num(self):
        return self._map_mode_state.mode_num

    @property
    def is_teammode(self):
        return self.gamemode.hasteams

    @property
    def mode_name(self):
        return self._map_mode_state.mode_name

    def get_map_names(self):
        return self._map_mode_state.get_map_names()

    def is_name_duplicate(self, name):
        return self._players.is_name_duplicate(name)

    def contains_client_with_ip(self, client_ip):
        return client_ip in self._client_ips

    def is_mod_active(self, mod_name):
        return mod_name in self._mods

    def get_mod(self, mod_name):
        return self._mods[mod_name]

    def add_mod(self, mod):
        self._mods[mod.name] = mod

    def del_mod(self, mod):
        assert self._mods[mod.name] is mod
        del self._mods[mod.name]

    ###########################################################################
    #######################         Setters         ###########################
    ###########################################################################

    @defer.inlineCallbacks
    def client_enter(self, entry_context):
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

    def client_leave(self, client):
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

    def pause(self):
        self._game_clock.pause()

    def resume(self):
        self._game_clock.resume(self.resume_delay)

    def set_resuming_state(self):
        "Used to set the game clock into the resuming state pending some external event."
        self._game_clock.set_resuming_state()

    def end_match(self):
        self._game_clock.timeleft = 0

    def change_map_mode(self, map_name, mode_name):
        self._game_clock.cancel()
        return self._map_mode_state.change_map_mode(map_name, mode_name)

    def rotate_map_mode(self):
        self._game_clock.cancel()
        return self._map_mode_state.rotate_map_mode()

    def await_map_mode_initialized(self):
        return self._map_mode_state.await_map_mode_initialized(self.player_count)

    def set_mastermode(self, mastermode):
        self.mastermode = mastermode
        self._update_current_masters()

    @property
    def broadcastbuffer(self):
        return self._broadcaster.broadcastbuffer

    def server_message(self, message, exclude=()):
        self._broadcaster.server_message(message, exclude)

    ###########################################################################
    #######################  Client event handling  ###########################
    ###########################################################################

    def handle_client_event(self, event_name, client, *args, **kwargs):
        handler = client.role.handle_event
        deferred = defer.maybeDeferred(handler, event_name, self, client, *args, **kwargs)
        deferred.addErrback(client.handle_exception)

    ###########################################################################
    #######################  Player event handling  ###########################
    ###########################################################################

    def handle_player_event(self, event_name, player, *args, **kwargs):
        handler = self._player_event_handler.handle_event
        deferred = defer.maybeDeferred(handler, event_name, self, player, *args, **kwargs)
        deferred.addErrback(player.client.handle_exception)

    ###########################################################################
    #####################  Game clock event handling  #########################
    ###########################################################################

    def _attach_game_clock_event_handlers(self):
        self._game_clock.add_resumed_callback(self._on_game_clock_resumed)
        self._game_clock.add_paused_callback(self._on_game_clock_paused)
        self._game_clock.add_resume_countdown_tick_callback(self._on_game_clock_resume_countdown_tick)
        self._game_clock.add_timeleft_altered_callback(self._on_game_clock_timeleft_altered)
        self._game_clock.add_intermission_started_callback(self._on_game_clock_intermission)
        self._game_clock.add_intermission_ended_callback(self._on_game_clock_intermission_ended)

    def _on_game_clock_resumed(self):
        self._broadcaster.resume()
        if not self.gamemode.initialized:
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

    def _flush_messages(self):
        if not self.decommissioned:
            reactor.callLater(0, reactor.addSystemEventTrigger, 'before', 'flush_bindings', self._flush_messages)
        self._broadcaster.flush_messages()

    def _initialize_client_match_data(self, cds, client):
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

    def _initialize_client(self, client):
        existing_players = list(self.players)

        with client.sendbuffer(1, True) as cds:
            swh.put_welcome(cds)
            self._put_room_title(cds, client)

            possible_privileged_clients = [client] + self._clients.to_list()

            swh.put_currentmaster(cds, self.mastermode, possible_privileged_clients)

            self._initialize_client_match_data(cds, client)

            swh.put_initclients(cds, existing_players)
            swh.put_resume(cds, existing_players)

        print(self._messages)
        if 'server_welcome' in self._messages:
            message = self._messages['server_welcome']
            formatted = format_cfg_message(message, self, client.get_player())
            defer.maybeDeferred(client.send_server_message, formatted)
        if 'player_connect' in self._messages:
            message = self._messages['player_connect']
            formatted = format_cfg_message(message, self, client.get_player())
            defer.maybeDeferred(self.public_message, formatted)

    def _player_disconnected(self, player):
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

    def _get_room_title(self):
        server_name = truncate(self._server_name, MAXSERVERLEN)
        # room_title = smf.format("{server_name} {room_title#room.name}", room=self, server_name=server_name)
        room_title = self.name
        return room_title

    def _put_room_title(self, cds, client):
        room_title = truncate(self._get_room_title(), MAXSERVERDESCLEN)
        swh.put_servinfo(cds, client, haspwd=False, description=room_title, domain='')

    def _send_room_title(self, client):
        with client.sendbuffer(1, True) as cds:
            self._put_room_title(cds, client)

    def _on_name_changed(self, *args):
        for client in self.clients:
            self._send_room_title(client)

    def public_message(self, msg):
        if msg:
            self._broadcaster.server_message(msg)

    def _set_player_spectator(self, player, spectate):
        if not spectate and player.state.is_spectator:
            self.gamemode.on_player_unspectate(player)

        elif spectate and not player.state.is_spectator:
            self.gamemode.on_player_spectate(player)

        else:
            print("invalid change")

    def _set_others_privilege(self, client, target, requested_privilege):
        raise GenericError("Setting other player privileges isn't currently implemented.")

    def _client_try_set_privilege(self, client, target, requested_privilege, pass_hash):
        if client is target:
            return self._set_self_privilege(client, requested_privilege, pass_hash)
        else:
            return self._set_others_privilege(client, target, requested_privilege)

    def _update_current_masters(self):
        self._broadcaster.current_masters(self.mastermode, self.clients)

    #TODO remove and reimplement
    def _client_change_privilege(self, client, target, requested_privilege):
        if requested_privilege == privileges.PRIV_NONE:
            self.admins.discard(target)
            self.auths.discard(target)
            self.masters.discard(target)
        elif requested_privilege == privileges.PRIV_MASTER:
            self.masters.add(target)
        elif requested_privilege == privileges.PRIV_AUTH:
            self.auths.add(target)
        elif requested_privilege == privileges.PRIV_ADMIN:
            self.admins.add(target)
        self._update_current_masters()

    def _set_self_privilege(self, client, requested_privilege, password):
        room_classification = "temporary" if self.temporary else "permanent"

        if requested_privilege > privileges.PRIV_NONE:
            privilege_action = "claim"
            permission_involved = requested_privilege
        else:
            privilege_action = "relinquish"
            permission_involved = client.privilege

        functionality_category = Room.set_self_privilege_functionality_tree.get(room_classification, {}).get(privilege_action, {})

        functionality = functionality_category.get(permission_involved, None)

        if functionality is None:
            raise InsufficientPermissions("You do not have permissions to do that.")

        if client.allowed(functionality):
            self._client_change_privilege(client, client, requested_privilege)
        else:
            raise InsufficientPermissions(functionality.denied_message)

    def get_target_client(self, target_pn):
        if target_pn.is_digit():
            return room.get_client(int(target_pn))
        else:
            return None
