import time

from cube2common.constants import mastermodes, disconnect_types, privileges
from cipolla.game.server_message_formatter import error
from cipolla.punitive_effects.punitive_effect_info import TimedExpiryInfo, EffectInfo
from cipolla.game.client.exceptions import InsufficientPermissions
from cipolla.game.gamemode.gamemodes import get_mode_name_from_num # type: ignore
from cipolla.game.map.resolve_map_name import resolve_map_name
from cipolla.game.client.exceptions import InsufficientPermissions, StateError, UnknownPlayer
from cipolla.game.room.exceptions import UnknownEvent
from cipolla.game.server_message_formatter import *
from cipolla.game.client.exceptions import *
from cube2common.vec import vec
from cube2common.constants import *
from cipolla.protocol import swh
from cipolla.utils.filtertext import filtertext
from cipolla.utils.dictionary_get import dictget
from cipolla.game.edit.selection import Selection


from cipolla.utils.tracing import *


from cipolla.game.client.client import Client
from cipolla.game.room.room import Room
from typing import Any, Dict, List, Union

class BaseRole(object):
    def __init__(self) -> None:
        self.privilege = privileges.PRIV_NONE

        self.actions = {
            'set_bot_limit':       self.on_disabled,
            'check_maps':          self.on_disabled,
            'edit_remip':          self.on_disabled,
            'edit_new_map':        self.on_disabled,
            'edit_get_map':        self.on_disabled,
            'get_demo':            self.on_disabled,
            'list_demos':          self.on_disabled,
            'clear_demo':          self.on_disabled,
            'stop_demo_recording': self.on_disabled,
            'set_demo_recording':  self.on_disabled,
            'add_bot':             self.on_disabled,
            'delete_bot':          self.on_disabled,
            'set_bot_balance':     self.on_disabled,
            'set_game_speed':      self.on_disabled,

            'give_master':         self.on_not_allowed,
            'set_master_mode':     self.on_not_allowed,
            'set_team':            self.on_not_allowed,
            'kick':                self.on_not_allowed,
            'clear_bans':          self.on_not_allowed,
            'map_vote':            self.on_not_allowed,
            'pause_game':          self.on_not_allowed,

            'set_master':          self.on_set_master,
            'set_spectator':       self.on_set_spectator,
            'item_list':           self.on_item_list,
            'flag_list':           self.on_flag_list,
            'base_list':           self.on_base_list,
            'map_crc':             self.on_map_crc,
            'command':             self.on_command,

            'N_SHOOT':             self.on_shoot,
            'N_ADDBOT':            self.on_addbot,
            'N_DELBOT':            self.on_delbot,
            'N_AUTHANS':           self.on_nauthans,
            'N_AUTHKICK':          self.on_authkick,
            'N_AUTHTRY':           self.on_authtry,
            'N_BASES':             self.on_bases,
            'N_BOTBALANCE':        self.on_botbalance,
            'N_BOTLIMIT':          self.on_botlimit,
            'N_CHECKMAPS':         self.on_checkmaps,
            'N_CLEARBANS':         self.on_clearbans,
            'N_CLEARDEMOS':        self.on_disabled,
            'N_CLIENTPING':        self.on_clientping,
            'N_CLIPBOARD':         self.on_clipboard,
            'N_CONNECT':           self.on_connect,
            'N_COPY':              self.on_copy,
            'N_DELCUBE':           self.on_delcube,
            'N_EDITENT':           self.on_editent,
            'N_EDITF':             self.on_editf,
            'N_EDITMODE':          self.on_editmode,
            'N_EDITM':             self.on_editm,
            'N_EDITT':             self.on_editt,
            'N_EDITVAR':           self.on_editvar,
            'N_EXPLODE':           self.on_explode,
            'N_FORCEINTERMISSION': self.on_forceintermission,
            'N_GAMESPEED':         self.on_gamespeed,
            'N_GETDEMO':           self.on_disabled,
            'N_GETMAP':            self.on_getmap,
            'N_GUNSELECT':         self.on_gunselect,
            'N_INITFLAGS':         self.on_initflags,
            'N_ONFLIP':            self.on_flip,
            'N_ITEMLIST':          self.on_itemlist,
            'N_ITEMPICKUP':        self.on_itempickup,
            'N_JUMPPAD':           self.on_jumppad,
            'N_KICK':              self.on_kick,
            'N_LISTDEMOS':         self.on_disabled,
            'N_MAPCHANGE':         self.on_mapchange,
            'N_MAPCRC':            self.on_mapcrc,
            'N_MAPVOTE':           self.on_mapvote,
            'N_NEWMAP':            self.on_newmap,
            'N_MASTERMODE':        self.on_not_allowed,
            'N_PASTE':             self.on_paste,
            'N_PAUSEGAME':         self.on_not_allowed,
            'N_PING':              self.on_ping,
            'N_POS':               self.on_pos,
            'N_POS':               self.on_pos,
            'N_RECORDDEMO':        self.on_disabled,
            'N_REMIP':             self.on_remip,
            'N_REPAMMO':           self.on_repammo,
            'N_REPLACE':           self.on_replace,
            'N_SAYTEAM':           self.on_sayteam,
            'N_SERVCMD':           self.on_servcmd,
            'N_ROTATE':            self.on_rotate,
            'N_SOUND':             self.on_sound,
            'N_SPAWN':             self.on_spawn,
            'N_SETMASTER':         self.on_setmaster,
            'N_SPECTATOR':         self.on_spectator,
            'N_STOPDEMO':          self.on_disabled,
            'N_SETTEAM':           self.on_setteam,
            'N_SUICIDE':           self.on_suicide,
            'N_SWITCHMODEL':       self.on_switchmodel,
            'N_SWITCHNAME':        self.on_switchname,
            'N_SWITCHTEAM':        self.on_switchteam,
            'N_TAKEFLAG':          self.on_takeflag,
            'N_TAUNT':             self.on_taunt,
            'N_TELEPORT':          self.on_teleport,
            'N_TEXT':              self.on_text,
            'N_TRYDROPFLAG':       self.on_trydropflag,
            'N_TRYSPAWN':          self.on_tryspawn,
        }

    def handle_event(self, event_name: str, room: Room, *args, **kwargs) -> None:
        action = self.actions.get(event_name, self.on_unknown_event)
        return action(room, *args, **kwargs) # type: ignore
        # TODO: mypy

    def handle_message(self, client: Client, room: Room, message_type: str, message: Dict[str, Any]) -> None:
        action = self.actions.get(message_type, self.on_unknown_message)
        return action(client, room, message) # type: ignore
        # TODO: mypy

    def on_unknown_message(self, client, room, message):
        print("===ERROR UnknownMessage:", message)
        raise UnknownMessage(message)

    # from game_event_handler
    def handle_text_event(self, text, room, player):
        def parse(text):
            text = text[1:].split(' ')
            return text[0], text[1:]

        cmd, args = parse(text)

        if not cmd in self.text_actions:
            player.client.send_server_message(error('Command does not exist. Type #commands for more info'))
        return self.text_actions[cmd](room, player, cmd, args)

    def on_unknown_event(self, ev_name, *args, **kwargs):
        print("===ERROR UnknownEvent:", *args, **kwargs)
        raise UnknownEvent('Event: '+ev_name+' Arguments: '+str(args) + str(kwargs))

    def on_disabled(self, room, client, *a, **kw):
        client.send_server_message(red('Command disabled'))
        pass

    def on_set_master(self, room, client, target_pn, *args):
        client_target = room.get_player(target_pn).client

        if client == client_target:
            if not room.admins_present() and not room.masters_present():
                room.change_privilege(client, privileges.PRIV_MASTER)
            else:
                client.send_server_message(info('master is already claimed'))

    def on_check_maps(self, room, client):
        pass

    def on_set_bot_limit(self, room, client, limit):
        pass

    def on_item_list(self, room, client, item_list):
        room.gamemode.on_client_item_list(client, item_list)

    def on_flag_list(self, room: Room, client: Client, flag_list: Union[List, List]) -> None:
        room.gamemode.on_client_flag_list(client, flag_list)

    # def on_give_master(self, room, client, client_target):
    #     room._client_change_privilege(client, client_target, 1)

    def on_delete_bot(self, room, client):
        pass

    def on_edit_new_map(self, room, client, size):
        pass

    def on_add_bot(self, room, client, skill):
        pass

    def on_base_list(self, room, client, base_list):
        room.gamemode.on_client_base_list(client, base_list)

    def on_map_crc(self, room: Room, client: Client, crc: int) -> None:
        # TODO: Implement optional spectating of clients without valid map CRC's
        pass

    def on_map_vote(self, room, client, map_name, mode_num):
        mode_name = get_mode_name_from_num(mode_num)
        map_name = yield resolve_map_name(room, map_name)
        room.change_map_mode(map_name, mode_name)

    def on_clear_bans(self, room, client):
        # TODO: Permissions checks
        client._punitive_model.clear_effects('ban')

    def on_command(self, room, client, command):
        pass

    def on_set_bot_balance(self, room, client, balance):
        pass

    def on_set_game_speed(self, room, client, speed):
        pass

    def on_edit_get_map(self, room, client):
        pass

    def on_not_allowed(self,  *args, **kwargs):
        from cipolla.game.player.player import Player
        from cipolla.game.client.client import Client
        message = 'you are unable to use this command'
        for cc in args:
            if isinstance(cc, Player):
                cc.client.send_server_message(red(message))
                return
            elif isinstance(cc, Client):
                cc.send_server_message(red(message))
                return

    def on_commands(self, room, player, *args, **kwargs):
        available_commands = self.text_actions.keys()
        formatted_command_list = list(map(lambda s: '#'+s, available_commands))
        player.client.send_server_message("\f7Commands: " + " | ".join(formatted_command_list))

    def on_info(self, *args, **kwargs):
        #TODO get info server
        # client.send_server_message(info(cipolla_server.server_info_model.value))
        pass

    def on_stats(self, *args, **kwargs):
        #TODO statsss
        pass

    def on_list_mods(self, room, player, *args, **kw):
        mods = ModsManager().list_mods()
        player.client.send_server_message(info("Available mods: " + " | ".join(mods)))

    def on_shoot(self, client: Client, room: Room, message: Dict[str, int]) -> None:
        player = client.get_player(message['aiclientnum'])
        shot_id = message['shot_id']
        gun = message['gun']
        from_pos = vec(*dictget(message, 'fx', 'fy', 'fz')) # type: ignore
        to_pos = vec(*dictget(message, 'tx', 'ty', 'tz')) # type: ignore
        hits = message['hits']
        room.handle_player_event('shoot', player, shot_id, gun, from_pos, to_pos, hits)

    def on_addbot(self, client, room, message):
        # room.handle_client_event('add_bot', client, message['skill'])
        # TODO: not implemented
        pass

    def on_nauthans(self, client, room, message):
        authdomain = message['authdomain']
        authid = message['authid']
        answer = message['answer']
        client.answer_auth_challenge(authdomain, authid, answer)

    def on_authkick(self, client, room, message):
        # authdomain = message['authdomain']
        # authname = message['authname']
        # target_pn = message['target_cn']
        # reason = message['reason']
        # TODO: not implemented
        # deferred = client.auth(authdomain, authname)
        # callback = lambda r: room.handle_client_event('kick', client, target_pn, reason)
        # deferred.addCallbacks(callback, callback)
        pass

    def on_authtry(self, client, room, message):
        # authdomain = message['authdomain']
        # authname = message['authname']
        # deferred = client.auth(authdomain, authname)
        # TODO: not implemented
        pass

    def on_bases(self, client, room, message):
        # TODO: not implemented
        # room.handle_client_event('base_list', client, message['bases'])
        pass

    def on_botbalance(self, client, room, message):
        # TODO: not implemented
        # room.handle_client_event('set_bot_balance', client, message['balance'])
        pass

    def on_botlimit(self, client, room, message):
        # TODO: not implemented
        # room.handle_client_event('set_bot_limit', client, message['limit'])
        pass

    def on_checkmaps(self, client, room, message):
        # TODO: not implemented
        # room.handle_client_event('check_maps', client)
        pass

    def on_clearbans(self, client, room, message):
        # TODO: not implemented
        # room.handle_client_event('clear_bans', client)
        pass

    def on_clientping(self, client: Client, room: Room, message: Dict[str, int]) -> None:
        ping = message['ping']
        client.ping_buffer.add(ping)
        player = client.get_player()
        swh.put_clientping(player.state.messages, ping)

    def on_clipboard(self, client, room, message):
        pass

    def on_connect(self, client: Client, room: Room, message: Dict[str, Union[str, int]]) -> None:
        if not client.is_connected:
            client.connect_received(message)

    def on_copy(self, client, room, message):
        del message['aiclientnum']
        player = client.get_player()
        selection = Selection.from_message(message)
        room.handle_player_event('edit_copy', player, selection)

    def on_delbot(self, client, room, message):
        # room.handle_client_event('delete_bot', client)
        # TODO: not implemented
        pass

    def on_delcube(self, client, room, message):
        del message['aiclientnum']
        player = client.get_player()
        selection = Selection.from_message(message)
        room.handle_player_event('edit_delete_cubes', player, selection)

    def on_editent(self, client, room, message):
        player = client.get_player()
        entity_id = message['entid']
        entity_type = message['type']
        x, y, z = dictget(message, 'x', 'y', 'z')
        attrs = message['attrs']
        room.handle_player_event('edit_entity', player, entity_id, entity_type, x, y, z, attrs)

    def on_editf(self, client, room, message):
        del message['aiclientnum']
        player = client.get_player()
        direction = message['direction']
        mode = message['mode']
        room.handle_player_event('edit_face', player, selection, direction, mode)

    def on_editmode(self, client, room, message):
        player = client.get_player()
        room.handle_player_event('edit_mode', player, message['value'])

    def on_editm(self, client, room, message):
        del message['aiclientnum']
        player = client.get_player()
        selection = Selection.from_message(message)
        material = message['material']
        material_filter = message['material_filter']
        room.handle_player_event('edit_material', player, selection, material, material_filter)


    def on_editt(self, client, room, message):
        del message['aiclientnum']
        player = client.get_player()
        selection = Selection.from_message(message)
        texture = message['texture']
        all_faces = message['all_faces']
        room.handle_player_event('edit_texture', player, selection, texture, all_faces)

    def on_editvar(self, client, room, message):
        pass

    def on_explode(self, client, room, message):
        player = client.get_player(message['aiclientnum'])
        cmillis = message['cmillis']
        gun = message['gun']
        explode_id = message['explode_id']
        hits = message['hits']
        room.handle_player_event('explode', player, cmillis, gun, explode_id, hits)

    def on_forceintermission(self, client, room, message):
        pass

    def on_gamespeed(self, client, room, message):
        # room.handle_client_event('set_game_speed', client, message['value'])
        # TODO: not implemented
        pass

    def on_gunselect(self, client: Client, room: Room, message: Dict[str, int]) -> None:
        player = client.get_player(message['aiclientnum'])
        room.handle_player_event('gunselect', player, message['gunselect'])

    def on_initflags(self, client: Client, room: Room, message: Dict[str, Union[List, int, List]]) -> None:
        # room.handle_client_event('flag_list', client, message['flags'])
        # TODO: not implemented
        pass

    def on_itemlist(self, client, room, message):
        # room.handle_client_event('item_list', client, message['items'])
        # TODO: not implemented
        pass

    def on_itempickup(self, client, room, message):
        # player = client.get_player(message['aiclientnum'])
        # room.handle_player_event('pickup_item', player, message['item_index'])
        # # TODO: not implemented
        pass


    def on_jumppad(self, client, room, message):
        player = client.get_player(message['aiclientnum'])
        room.handle_player_event('jumppad', player, message['jumppad'])

    def on_kick(self, client, room, message):
        # room.handle_client_event('kick', client, message['target_cn'], message['reason'])
        # TODO: not implemented
        pass

    def on_mapchange(self, client, room, message):
        # TODO: never called?
        # room.handle_client_event('map_vote', client, message['map_name'], message['mode_num'])
        pass

    def on_mapcrc(self, client: Client, room: Room, message: Dict[str, Union[str, int]]) -> None:
        # room.handle_client_event('map_crc', client, message['mapcrc'])
        # TODO: not implemented
        pass

    def on_mapvote(self, client: Client, room: Room, message: Dict[str, Union[str, int]]) -> None:
        client.role.handle_event('map_vote', room, client, message['map_name'], message['mode_num'])

    def on_newmap(self, client, room, message):
        # room.handle_client_event('edit_new_map', client, message['size'])
        # TODO: not implemented
        pass

    def on_paste(self, client, room, message):
        del message['aiclientnum']
        player = client.get_player()
        selection = Selection.from_message(message)
        room.handle_player_event('edit_paste', player, selection)

    def on_ping(self, client, room, message):
        with client.sendbuffer(1, False) as cds:
            swh.put_pong(cds, message['cmillis'])

    def on_pos(self, client: Client, room: Room, message: Dict[str, Union[int, List[int], bytes]]) -> None:
        assert isinstance(message['clientnum'], int)
        player = client.get_player(message['clientnum'])
        player.state.update_position(message['position'], message['raw_position'])

    def on_remip(self, client, room, message):
        # room.handle_client_event('edit_remip', client)
        # TODO: not implemented
        pass

    def on_repammo(self, client, room, message):
        player = client.get_player(message['aiclientnum'])
        room.handle_player_event('replenish_ammo', player)

    def on_replace(self, client, room, message):
        del message['aiclientnum']
        player = client.get_player()
        selection = Selection.from_message(message)
        texture = message['texture']
        new_texture = message['new_texture']
        in_selection = message['in_selection']
        room.handle_player_event('edit_replace', player, selection, texture, new_texture, in_selection)

    def on_rotate(self, client, room, message):
        del message['aiclientnum']
        player = client.get_player()
        selection = Selection.from_message(message)
        axis = message['axis']
        room.handle_player_event('edit_rotate', player, selection, axis)

    def on_sayteam(self, client: Client, room: Room, message: Dict[str, Union[str, int]]) -> None:
        player = client.get_player()
        room.handle_player_event('team_chat', player, message['text'])

    def on_servcmd(self, client, room, message):
        # room.handle_client_event('command', client, message['command'])
        # TODO: implement
        pass

    def on_setmaster(self, client, room, message):
        # room.handle_client_event('set_master', client, message['target_cn'], message['pwdhash'], message['value'])
        # TODO: not implemented
        pass

    def on_set_spectator(self, room, client, target_pn, spectate):
        player = room.get_player(target_pn)
        if player is None:
            raise UnknownPlayer(cn=target_pn)
        elif client == player.client:
            room._set_player_spectator(player, spectate)
        else:
            client.send_server_message(error("you can't spectate other players")) # TODO: make usage function

    def on_setteam(self, client, room, message):
        # team_name = filtertext(message['team'], False, MAXTEAMLEN)
        # room.handle_client_event('set_team', client, message['target_cn'], team_name)
        # TODO: not implemented
        pass

    def on_sound(self, client: Client, room: Room, message: Dict[str, int]) -> None:
        player = client.get_player(message['aiclientnum'])
        room.handle_player_event('sound', player, message['sound'])

    def on_spawn(self, client: Client, room: Room, message: Dict[str, int]) -> None:
        player = client.get_player(message['aiclientnum'])
        room.handle_player_event('spawn', player, message['lifesequence'], message['gunselect'])

    def on_spectator(self, client, room, message):
        # room.handle_client_event('set_spectator', client, message['target_cn'], bool(message['value']))
        # TODO: is it implemented???
        pass

    def on_suicide(self, client, room, message):
        player = client.get_player(message['aiclientnum'])
        room.handle_player_event('suicide', player)

    def on_switchmodel(self, client, room, message):
        player = client.get_player(message['aiclientnum'])
        room.handle_player_event('switch_model', player, message['playermodel'])

    def on_switchname(self, client, room, message):
        player = client.get_player(-1)
        name = filtertext(message['name'], False, MAXNAMELEN)
        if len(name) <= 0:
            name = "unnamed"
        room.handle_player_event('switch_name', player, name)

    def on_switchteam(self, client, room, message):
        player = client.get_player(-1)
        team_name = filtertext(message['team'], False, MAXTEAMLEN)
        room.handle_player_event('switch_team', player, team_name)

    def on_takeflag(self, client: Client, room: Room, message: Dict[str, int]) -> None:
        player = client.get_player(message['aiclientnum'])
        room.handle_player_event('take_flag', player, message['flag'], message['version'])

    def on_taunt(self, client, room, message):
        player = client.get_player()
        room.handle_player_event('taunt', player)

    def on_teleport(self, client, room, message):
        player = client.get_player(message['aiclientnum'])
        room.handle_player_event('teleport', player, message['teleport'], message['teledest'])

    def on_text(self, client: Client, room: Room, message: Dict[str, Union[str, int]]) -> None:
        player = client.get_player()
        room.handle_player_event('game_chat', player, message['text'])

    def on_trydropflag(self, client, room, message):
        player = client.get_player(message['aiclientnum'])
        room.handle_player_event('try_drop_flag', player)

    def on_tryspawn(self, client, room, message):
        player = client.get_player(message['aiclientnum'])
        room.handle_player_event('request_spawn', player)

    def on_getmap(client, room, message):
        # room.handle_client_event('edit_get_map', client)
        # TODO: not implemented
        pass

    def on_flip(client, room, message):
        del message['aiclientnum']
        player = client.get_player()
        selection = Selection.from_message(message)
        room.handle_player_event('edit_flip', player, selection)

class MasterRole(BaseRole):
    def __init__(self) -> None:
        super().__init__()
        self.privilege = privileges.PRIV_MASTER
        self.actions.update({
            'map_vote':         self.on_map_vote,
            'set_spectator':    self.on_set_spectator,
            'set_master':       self.on_set_master,
            'set_master_mode':  self.on_set_master_mode,
            'set_team':         self.on_set_team,
            'pause_game':       self.on_pause_game,

            'N_MASTERMODE':     self.on_mastermode,
            'N_PAUSEGAME':      self.on_pause_game,
            })

    def on_map_vote(self, room: Room, client: Client, map_name: str, mode_num: int) -> None:
        mode_name = get_mode_name_from_num(mode_num)
        map_name = resolve_map_name(room, map_name)
        room.change_map_mode(map_name, mode_name)

    def on_kick(self, room, player, args):
        target_client = room.get_target_client(args[0])
        if target_client is None:
            player.client.send_server_message(usage_error('Invalid client number'))
        else:
            expiry_time = time.time() + (4 * SECONDS_PER_HOUR)
            client._punitive_model.add_effect('ban', target_client.host, EffectInfo(TimedExpiryInfo(expiry_time)))
            target_client.disconnect(disconnect_types.DISC_KICK, error("You were kicked by {name#kicker}", kicker=target_client))

    def on_mastermode(self, client, room, message):
        self.handle_event('set_master_mode', room, client, message['mastermode'])
        client.send_server_message(info('Master mode changed'))

    def on_set_master(self, room, client, target_pn, *args):
        client_target = room.get_player(target_pn).client

        # if client_target is the same as client, the client is trying to relinquish his master
        if client_target == client:
            room.change_privilege(client, privileges.PRIV_NONE)
        else:
            room.change_privilege(client_target, privileges.PRIV_MASTER)

    def on_set_spectator(self, room, client, target_pn, spectate):
        print(target_pn)
        print(spectate)
        target_player = room.get_player(target_pn)

        if target_player is None:
            raise UnknownPlayer(cn=target_pn)
        elif isinstance(target_player.client.role, AdminRole):
            client.send_server_message(error('you can\'t spectate the masta admin!'))
        else:
            room._set_player_spectator(target_player, spectate)

    def on_set_master_mode(self, room, client, mastermode):
        if mastermode == mastermodes.MM_PRIVATE:
            raise GenericError("Mastermode private not allowed")
        if mastermode < mastermodes.MM_OPEN or mastermode > mastermodes.MM_PRIVATE:
            raise GenericError("Mastermode out of allowed range.")

        room.set_mastermode(mastermode)

    def on_set_team(self, room, client, target_pn, team_name):
        target_player = room.get_player(target_pn)
        if target_player is None:
            raise UnknownPlayer(cn=target_pn)
        elif isinstance(target_player.client.role, AdminRole):
            client.send_server_message(error('you can\'t change the team of the masta admin!'))
        else:
            room.gamemode.on_player_try_set_team(client.get_player(), target_player, target_player.teamname, team_name)

    def on_pause_game(self, room, client, pause):
        if pause:
            if room.is_paused and not room.is_resuming: raise StateError('The game is already paused.')
            room.pause()
            room._broadcaster.server_message(info(f"{client.get_player().name} has paused the game."))
        elif not pause:
            if not room.is_paused: raise StateError('The game is already resumed.')
            room.resume()
            room._broadcaster.server_message(info(f"{client.get_player().name} has resumed the game."))


class AdminRole(MasterRole):
    def __init__(self) -> None:
        super().__init__()
        self.privilege = privileges.PRIV_ADMIN
        self.actions.update({
            'set_master':     self.on_set_master,
            'set_spectator':  self.on_set_spectator,
            })

    def on_set_master(self, room, client, target_pn, *args):
        client_target = room.get_player(target_pn).client

        if client_target != client:
            if isinstance(client_target.role, MasterRole):
                room.change_privilege(client_target, privileges.PRIV_NONE)
            else:
                room.change_privilege(client_target, privileges.PRIV_MASTER)

    def on_set_spectator(self, room, client, target_pn, spectate):
        target_player = room.get_player(target_pn)

        if target_player is None:
            raise UnknownPlayer(cn=target_pn)

        room._set_player_spectator(target_player, spectate)
