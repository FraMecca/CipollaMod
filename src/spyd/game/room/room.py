from twisted.internet import reactor

from cube2common.constants import INTERMISSIONLEN, client_states, MAXROOMLEN, MAXSERVERDESCLEN, MAXSERVERLEN, mastermodes, privileges
from cube2common.cube_data_stream import CubeDataStream
from spyd.game.client.client_message_handling_base import InsufficientPermissions, UnknownPlayer, GenericError
from spyd.game.gamemode import get_mode_name_from_num
from spyd.game.room.client_collection import ClientCollection
from spyd.game.room.player_collection import PlayerCollection
from spyd.game.room.room_broadcaster import RoomBroadcaster
from spyd.game.room.room_entry_context import RoomEntryContext
from spyd.game.room.room_map_mode_state import RoomMapModeState
from spyd.game.server_message_formatter import smf, error
from spyd.game.timing.game_clock import GameClock
from spyd.protocol import swh
from spyd.utils.match_fuzzy import match_fuzzy
from spyd.utils.truncate import truncate
from spyd.utils.value_model import ValueModel
from spyd.permissions.functionality import Functionality


class Room(object):
    '''
    The room serves as the central hub for all players who are in the same game.
    It provides four things;
    * Event handling functions which accept client events
    * Event handling functions which accept player events
    * Accessors to query the state of the room.
    * Setters to modify the state of the room.
    '''
    def __init__(self, room_name=None, room_manager=None, server_name_model=None, map_rotation=None, map_meta_data_accessor=None, command_executer=None):
        self._game_clock = GameClock()
        self._attach_game_clock_event_handlers()
        
        self.manager = room_manager

        self._server_name_model = server_name_model or ValueModel("123456789ABCD")
        self._name = ValueModel(room_name or "1234567")
        self._server_name_model.observe(self._on_name_changed)
        self._name.observe(self._on_name_changed)

        self._clients = ClientCollection()
        self._players = PlayerCollection()
        
        self.command_executer = command_executer
        self.command_context = {}

        self.mastermask = 0
        self.mastermode = 0
        self.resume_delay = None

        self.temporary = False
        self.decommissioned = False
        
        # Holds the client objects with each level of permissions
        self.masters = set()
        self.auths   = set()
        self.admins  = set()

        self._map_mode_state = RoomMapModeState(self, map_rotation, map_meta_data_accessor)

        self._broadcaster = RoomBroadcaster(self._clients, self._players)
        reactor.addSystemEventTrigger('before', 'flush_bindings', self._flush_messages)

    ###########################################################################
    #######################        Accessors        ###########################
    ###########################################################################

    def __format__(self, format_spec):
        return smf.format("{room#room.name}", room=self)

    @property
    def name(self):
        return self._name.value

    @name.setter
    def name(self, value):
        self._name.value = truncate(value, MAXROOMLEN)

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
    def playing_count(self):
        count = 0
        for player in self.players:
            if not player.state.is_spectator:
                count += 1
        return count

    def get_client(self, cn):
        return self._clients.by_cn(cn)

    def get_player(self, pn):
        return self._players.by_pn(pn)

    @property
    def is_paused(self):
        return self._game_clock.is_paused

    @property
    def timeleft(self):
        return self._game_clock.timeleft

    @property
    def gamemode(self):
        return self._map_mode_state.gamemode

    @property
    def map_name(self):
        return self._map_mode_state.map_name

    @property
    def mode_name(self):
        return self._map_mode_state.mode_name

    def is_name_duplicate(self, name):
        return self._players.is_name_duplicate(name)

    ###########################################################################
    #######################         Setters         ###########################
    ###########################################################################

    def client_enter(self, entry_context):
        if not self._map_mode_state.initialized or self._map_mode_state.rotate_on_first_player and len(self.players) == 0:
            self.rotate_map_mode()

        client = entry_context.client
        player = client.get_player()

        player.state.use_game_clock(self._game_clock)

        self._initialize_client(client)
        self._broadcaster.client_connected(client)

        self._clients.add(client)
        self._players.add(player)

        self.gamemode.on_player_connected(player)

    def client_leave(self, client):
        self._clients.remove(client)
        for player in client.players.itervalues():
            self._player_disconnected(player)
        if client in self.masters or client in self.admins:
            self.masters.discard(client)
            self.admins.discard(client)
            

    def pause(self):
        self._game_clock.pause()

    def resume(self):
        self._game_clock.resume(self.resume_delay)
        
    def end_match(self):
        print "end_match called"
        self._game_clock.timeleft = 0

    def change_map_mode(self, map_name, mode_name):
        self._map_mode_state.change_map_mode(map_name, mode_name)
        self._new_map_mode_initialize()

    def rotate_map_mode(self):
        self._map_mode_state.rotate_map_mode()
        self._new_map_mode_initialize()

    @property
    def broadcastbuffer(self):
        return self._broadcaster.broadcastbuffer

    ###########################################################################
    #######################  Client event handling  ###########################
    ###########################################################################

    def on_client_set_master(self, client, target_cn, password_hash, requested_privilege):
        target = self.get_client(target_cn)
        if target is None:
            raise UnknownPlayer('No client with cn {cn#cn} found.')

        self._client_try_set_privilege(client, target, requested_privilege)

    temporary_set_mastermode_functionality = Functionality("spyd.game.room.temporary.set_mastermode")
    set_mastermode_functionality = Functionality("spyd.game.room.set_mastermode")
    
    def on_client_set_master_mode(self, client, mastermode):
        allowed_set_mastermode = client.allowed(Room.set_mastermode_functionality) or (self.temporary and client.allowed(Room.temporary_set_mastermode_functionality))

        if not allowed_set_mastermode:
            raise InsufficientPermissions('Insufficient permissions to change mastermode.')

        if mastermode < mastermodes.MM_OPEN or mastermode > mastermodes.MM_PRIVATE:
            client.send_server_message(error("Mastermode out of allowed range."))
            return

        self.mastermode = mastermode
        self._update_current_masters()

    def on_client_set_team(self, client, target_pn, team_name):
        # TODO: Implement permissions for changing player teams
        can_set_others_teams = True

        if not can_set_others_teams:
            raise InsufficientPermissions('Insufficient permissions to change player teams.')

        player = self.get_player(target_pn)
        if player is None:
            raise UnknownPlayer(cn=target_pn)

        self.gamemode.on_player_try_set_team(client.get_player(), player, player.team.name, team_name)

    def on_client_set_spectator(self, client, target_pn, spectate):
        # TODO: Implement permissions for spectating players
        can_spectate_others = True

        if not can_spectate_others:
            raise InsufficientPermissions('Insufficient permissions to change who is spectating.')

        player = self.get_player(target_pn)
        if player is None:
            raise UnknownPlayer(cn=target_pn)

    def on_client_kick(self, client, target_pn, reason):
        # TODO: Implement kicking of players and insertion of bans
        pass

    def on_client_clear_bans(self, client):
        # TODO: Implement clearing of bans
        pass

    def on_client_map_vote(self, client, map_name, mode_num):
        # TODO: Implement map voting and setting of the map when players have elevated permissions and the room is locked
        mode_name = get_mode_name_from_num(mode_num)
        valid_map_names = self._map_mode_state.get_map_names()
        map_name_match = match_fuzzy(map_name, valid_map_names)
        if map_name_match is None:
            raise GenericError('Could not resolve map name to valid map. Please try again.')
        self.change_map_mode(map_name_match, mode_name)

    def on_client_map_crc(self, client, crc):
        # TODO: Implement optional spectating of clients without valid map CRC's
        pass

    def on_client_item_list(self, client, item_list):
        self.gamemode.on_client_item_list(client, item_list)

    def on_client_base_list(self, client, base_list):
        self.gamemode.on_client_base_list(client, base_list)

    def on_client_flag_list(self, client, flag_list):
        self.gamemode.on_client_flag_list(client, flag_list)

    def on_client_pause_game(self, client, pause):
        # TODO: Implement permissions for pausing the game
        can_pause_game = True

        if not can_pause_game:
            raise InsufficientPermissions('Insufficient permissions to pause game.')

        if pause:
            self.pause()
        else:
            self.resume()

    def on_client_set_demo_recording(self, client, value):
        pass

    def on_client_stop_demo_recording(self, client):
        pass

    def on_client_clear_demo(self, client, demo_id):
        pass

    def on_client_list_demos(self, client):
        pass

    def on_client_get_demo(self, client, demo_id):
        pass

    def on_client_add_bot(self, client, skill):
        pass

    def on_client_delete_bot(self, client):
        pass

    def on_client_set_bot_balance(self, client, balance):
        pass

    def on_client_set_bot_limit(self, client, limit):
        pass

    def on_client_check_maps(self, client):
        pass

    def on_client_set_game_speed(self, client, speed):
        pass

    def on_client_edit_get_map(self, client):
        pass

    def on_client_edit_new_map(self, client, size):
        pass

    def on_client_edit_remip(self, client):
        pass

    def on_client_command(self, client, command):
        pass

    ###########################################################################
    #######################  Player event handling  ###########################
    ###########################################################################

    def on_player_switch_model(self, player, playermodel):
        player.playermodel = playermodel
        swh.put_switchmodel(player.state.messages, playermodel)

    def on_player_switch_name(self, player, name):
        player.name = name
        with self.broadcastbuffer(1, True) as cds:
            tm = CubeDataStream()
            swh.put_switchname(tm, "aaaaa")
            swh.put_clientdata(cds, player.client, str(tm))

    def on_player_switch_team(self, player, team_name):
        self.gamemode.on_player_try_set_team(player, player, player.team.name, team_name)

    def on_player_taunt(self, player):
        self.gamemode.on_player_taunt(player)

    def on_player_teleport(self, player, teleport, teledest):
        self._broadcaster.teleport(player, teleport, teledest)

    def on_player_jumppad(self, player, jumppad):
        self._broadcaster.jumppad(player, jumppad)

    def on_player_suicide(self, player):
        self._broadcaster.player_died(player, player)
        player.state.state = client_states.CS_DEAD
        self.gamemode.on_player_death(player, player)

    def on_player_shoot(self, player, shot_id, gun, from_pos, to_pos, hits):
        self.gamemode.on_player_shoot(player, shot_id, gun, from_pos, to_pos, hits)

    def on_player_explode(self, player, cmillis, gun, explode_id, hits):
        self.gamemode.on_player_explode(player, cmillis, gun, explode_id, hits)

    def on_player_request_spawn(self, player):
        self.gamemode.on_player_request_spawn(player)

    def on_player_spawn(self, player, lifesequence, gunselect):
        player.state.state = client_states.CS_ALIVE
        player.state.lifesequence = lifesequence
        player.state.gunselect = gunselect

        swh.put_spawn(player.state.messages, player.state)

    def on_player_gunselect(self, player, gunselect):
        player.state.gunselect = gunselect
        swh.put_gunselect(player.state.messages, gunselect)

    def on_player_sound(self, player, sound):
        swh.put_sound(player.state.messages, sound)

    def on_player_pickup_item(self, player, item_index):
        self.gamemode.on_player_pickup_item(player, item_index)

    def on_player_replenish_ammo(self, player):
        pass

    def on_player_take_flag(self, player, flag, version):
        self.gamemode.on_player_take_flag(player, flag, version)

    def on_player_try_drop_flag(self, player):
        self.gamemode.on_player_try_drop_flag(player)

    def on_player_game_chat(self, player, text):
        if text[0] == "#":
            self.command_executer.execute(self, player.client, text)
        else:
            swh.put_text(player.state.messages, text)

    def on_player_team_chat(self, player, text):
        if player.isai: return
        clients = filter(lambda c: c.get_player().team == player.team, self.clients)
        with self.broadcastbuffer(1, True, [player.client], clients) as cds:
            swh.put_sayteam(cds, player.client, text)

    def on_player_edit_mode(self, player, editmode):
        with self.broadcastbuffer(1, True, [player]) as cds:
            tm = CubeDataStream()
            swh.put_editmode(tm, editmode)
            swh.put_clientdata(cds, player.client, str(tm))

    def on_player_edit_entity(self, player, entity_id, entity_type, x, y, z, attrs):
        pass

    def on_player_edit_face(self, selection, direction, mode):
        pass

    def on_player_edit_material(self, selection, material, material_filter):
        pass

    def on_player_edit_texture(self, selection, texture, all_faces):
        pass

    def on_player_edit_copy(self, selection):
        pass

    def on_player_edit_paste(self, selection):
        pass

    def on_player_edit_flip(self, selection):
        pass

    def on_player_edit_delete_cubes(self, selection):
        pass

    def on_player_edit_rotate(self, selection, axis):
        pass

    def on_player_edit_replace(self, selection, texture, new_texture, in_selection):
        pass

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
        self._broadcaster.server_message("Resuming in {} seconds...".format(seconds))

    def _on_game_clock_timeleft_altered(self, seconds):
        self._broadcaster.time_left(seconds)
        print "room._on_game_clock_timeleft_altered called", seconds

    def _on_game_clock_intermission(self):
        self._broadcaster.server_message("Intermission has started.")
        self._broadcaster.intermission()

    def _on_game_clock_intermission_ended(self):
        self._broadcaster.server_message("Intermission has ended.")
        self.rotate_map_mode()

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

        self.gamemode.initialize_player(cds, player)
    
        if player.state.can_spawn:
            player.state.respawn(self.gamemode)
            swh.put_spawnstate(cds, player)

    def _initialize_client(self, client):
        existing_players = list(self.players)

        with client.sendbuffer(1, True) as cds:
            swh.put_welcome(cds)
            self._put_room_title(cds, client)

            swh.put_currentmaster(cds, self.mastermode, self.clients)

            self._initialize_client_match_data(cds, client)

            swh.put_resume(cds, existing_players)
            swh.put_initclients(cds, existing_players)

    def _new_map_mode_initialize(self):
        with self._broadcaster.broadcastbuffer(1, True) as cds:
            swh.put_mapchange(cds, self.map_name, self.gamemode.clientmodenum, hasitems=False)

            for player in self.players:
                self.gamemode.initialize_player(cds, player)

        if self.gamemode.timed:
            self._game_clock.start(self.gamemode.timeout, INTERMISSIONLEN)
        else:
            self._game_clock.start_untimed()

        self._game_clock.resume(self.resume_delay)

        for player in self.players:
            player.state.reset()
            player.state.respawn(self.gamemode)
            
        for client in self.clients:
            with client.sendbuffer(1, True) as cds:
                self._initialize_client_match_data(cds, client)
                for player in client.players.itervalues():
                    swh.put_spawnstate(cds, player)

    def _player_disconnected(self, player):
        self._players.remove(player)
        self._broadcaster.player_disconnected(player)
        self.gamemode.on_player_disconnected(player)

    def _get_room_title(self):
        server_name = truncate(self._server_name_model.value, MAXSERVERLEN)
        room_title = smf.format("{server_name} {room_title#room.name}", room=self, server_name=server_name)
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

    set_self_privilege_functionality_tree = {
        'temporary': {
            'claim': {
                privileges.PRIV_MASTER: Functionality("spyd.game.room.temporary.claim_master", "You do not have permission to claim master."),
                privileges.PRIV_AUTH: Functionality("spyd.game.room.temporary.claim_auth", "You do not have permission to claim auth."),
                privileges.PRIV_ADMIN: Functionality("spyd.game.room.temporary.claim_admin", "You do not have permission to claim admin.")
            },
            'relinquish': {
                privileges.PRIV_MASTER: Functionality("spyd.game.room.temporary.relinquish_master", "Cannot relinquish master."),
                privileges.PRIV_AUTH: Functionality("spyd.game.room.temporary.relinquish_auth", "Cannot relinquish auth."),
                privileges.PRIV_ADMIN: Functionality("spyd.game.room.temporary.relinquish_admin", "Cannot relinquish master.")
            }
        },
        'permanent': {
            'claim': {
                privileges.PRIV_MASTER: Functionality("spyd.game.room.permanent.claim_master", "You do not have permission to claim master in permanent rooms."),
                privileges.PRIV_AUTH: Functionality("spyd.game.room.permanent.claim_auth", "You do not have permission to claim auth in permanent rooms."),
                privileges.PRIV_ADMIN: Functionality("spyd.game.room.permanent.claim_admin", "You do not have permission to claim admin in permanent rooms.")
            },
            'relinquish': {
                privileges.PRIV_MASTER: Functionality("spyd.game.room.permanent.relinquish_master", "Cannot relinquish master."),
                privileges.PRIV_AUTH: Functionality("spyd.game.room.permanent.relinquish_master", "Cannot relinquish auth."),
                privileges.PRIV_ADMIN: Functionality("spyd.game.room.permanent.relinquish_admin", "Cannot relinquish master.")
            }
        }
    }


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
    
    def _set_self_privilege(self, client, requested_privilege):
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

    def _set_others_privilege(self, client, target, requested_privilege):
        raise GenericError("Setting other player privileges isn't currently implemented.")

    def _client_try_set_privilege(self, client, target, requested_privilege):
        if client is target:
            return self._set_self_privilege(client, requested_privilege)
        else:
            return self._set_others_privilege(client, target, requested_privilege)

    def _update_current_masters(self):
        self._broadcaster.current_masters(self.mastermode, self.clients)
