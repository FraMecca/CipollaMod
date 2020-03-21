from cube2common.vec import vec
from cube2common.constants import *
from spyd.protocol import swh
from spyd.utils.filtertext import filtertext
from spyd.utils.dictionary_get import dictget
from spyd.game.edit.selection import Selection
from spyd.game.client.exceptions import *
from spyd.game.server_message_formatter import *

from spyd.utils.tracing import tracer


class ClientMessageHandler(object):

    def __init__(self):
        self.actions = {
            # map message_type to actions for handling
            # *args = client, room, message
            'N_SHOOT': self.on_shoot,
            'N_ADDBOT': self.on_addbot,
            'N_DELBOT': self.on_delbot,
            'N_AUTHANS': self.on_nauthans,
            'N_AUTHKICK': self.on_authkick,
            'N_AUTHTRY': self.on_authtry,
            'N_BASES': self.on_bases,
            'N_BOTBALANCE': self.on_botbalance,
            'N_BOTLIMIT': self.on_botlimit,
            'N_CHECKMAPS': self.on_checkmaps,
            'N_CLEARBANS': self.on_clearbans,
            'N_CLEARDEMOS': self.on_disabled,
            'N_CLIENTPING': self.on_clientping,
            'N_CLIPBOARD': self.on_clipboard,
            'N_CONNECT': self.on_connect,
            'N_COPY': self.on_copy,
            'N_DELCUBE': self.on_delcube,
            'N_EDITENT': self.on_editent,
            'N_EDITF': self.on_editf,
            'N_EDITMODE': self.on_editmode,
            'N_EDITM': self.on_editm,
            'N_EDITT': self.on_editt,
            'N_EDITVAR': self.on_editvar,
            'N_EXPLODE': self.on_explode,
            'N_FORCEINTERMISSION': self.on_forceintermission,
            'N_GAMESPEED': self.on_gamespeed,
            'N_GETDEMO': self.on_disabled,
            'N_GETMAP': self.on_getmap,
            'N_GUNSELECT': self.on_gunselect,
            'N_INITFLAGS': self.on_initflags,
            'N_ONFLIP': self.on_flip,
            'N_ITEMLIST': self.on_itemlist,
            'N_ITEMPICKUP': self.on_itempickup,
            'N_JUMPPAD': self.on_jumppad,
            'N_KICK': self.on_kick,
            'N_LISTDEMOS': self.on_disabled,
            'N_MAPCHANGE': self.on_mapchange,
            'N_MAPCRC': self.on_mapcrc,
            'N_MAPVOTE': self.on_mapvote,
            'N_NEWMAP': self.on_newmap,
            'N_MASTERMODE': self.on_mastermode,
            'N_PASTE': self.on_paste,
            'N_PAUSEGAME': self.on_pausegame,
            'N_PING': self.on_ping,
            'N_POS': self.on_pos,
            'N_POS': self.on_pos,
            'N_RECORDDEMO': self.on_disabled,
            'N_REMIP': self.on_remip,
            'N_REPAMMO': self.on_repammo,
            'N_REPLACE': self.on_replace,
            'N_ROTATE': self.on_rotate,
            'N_SAYTEAM': self.on_sayteam,
            'N_SERVCMD': self.on_servcmd,
            'authpass': self.on_authpass,
            'N_SETMASTER': self.on_setmaster,
            'N_SETTEAM': self.on_setteam,
            'N_SOUND': self.on_sound,
            'N_SPAWN': self.on_spawn,
            'N_SPECTATOR': self.on_spectator,
            'N_STOPDEMO': self.on_disabled,
            'N_SUICIDE': self.on_suicide,
            'N_SWITCHMODEL': self.on_switchmodel,
            'N_SWITCHNAME': self.on_switchname,
            'N_SWITCHTEAM': self.on_switchteam,
            'N_TAKEFLAG': self.on_takeflag,
            'N_TAUNT': self.on_taunt,
            'N_TELEPORT': self.on_teleport,
            'N_TEXT': self.on_text,
            'N_TRYDROPFLAG': self.on_trydropflag,
            'N_TRYSPAWN': self.on_tryspawn,
        }

    def handle_message(self, client, room, message_type, message):
        action = self.actions.get(message_type, self.on_unknown_message)
        return action(client, room, message)

    def on_unknown_message(self, client, room, message):
        print("===ERROR UnknownMessage:", message)
        raise UnknownMessage(message)

    def on_disabled(self, client, *a, **kw):
        client.send_server_message(red('Command disabled'))

    def on_shoot(self, client, room, message):
        player = client.get_player(message['aiclientnum'])
        shot_id = message['shot_id']
        gun = message['gun']
        from_pos = vec(*dictget(message, 'fx', 'fy', 'fz'))
        to_pos = vec(*dictget(message, 'tx', 'ty', 'tz'))
        hits = message['hits']
        room.handle_player_event('shoot', player, shot_id, gun, from_pos, to_pos, hits)

    def on_addbot(self, client, room, message):
        room.handle_client_event('add_bot', client, message['skill'])

    def on_nauthans(self, client, room, message):
        authdomain = message['authdomain']
        authid = message['authid']
        answer = message['answer']
        client.answer_auth_challenge(authdomain, authid, answer)

    def on_authkick(self, client, room, message):
        authdomain = message['authdomain']
        authname = message['authname']
        target_pn = message['target_cn']
        reason = message['reason']

        deferred = client.auth(authdomain, authname)
        callback = lambda r: room.handle_client_event('kick', client, target_pn, reason)
        deferred.addCallbacks(callback, callback)

    def on_authtry(self, client, room, message):
        authdomain = message['authdomain']
        authname = message['authname']
        deferred = client.auth(authdomain, authname)

    def on_bases(self, client, room, message):
        room.handle_client_event('base_list', client, message['bases'])

    def on_botbalance(self, client, room, message):
        room.handle_client_event('set_bot_balance', client, message['balance'])

    def on_botlimit(self, client, room, message):
        room.handle_client_event('set_bot_limit', client, message['limit'])

    def on_checkmaps(self, client, room, message):
        room.handle_client_event('check_maps', client)

    def on_clearbans(self, client, room, message):
        room.handle_client_event('clear_bans', client)

    def on_clientping(self, client, room, message):
        ping = message['ping']
        client.ping_buffer.add(ping)
        player = client.get_player()
        swh.put_clientping(player.state.messages, ping)

    def on_clipboard(self, client, room, message):
        pass

    def on_connect(self, client, room, message):
        if not client.is_connected:
            client.connect_received(message)

    def on_copy(self, client, room, message):
        del message['aiclientnum']
        player = client.get_player()
        selection = Selection.from_message(message)
        room.handle_player_event('edit_copy', player, selection)

    def on_delbot(self, client, room, message):
        room.handle_client_event('delete_bot', client)

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
        room.handle_client_event('set_game_speed', client, message['value'])

    def on_gunselect(self, client, room, message):
        player = client.get_player(message['aiclientnum'])
        room.handle_player_event('gunselect', player, message['gunselect'])

    def on_initflags(self, client, room, message):
        room.handle_client_event('flag_list', client, message['flags'])

    def on_itemlist(self, client, room, message):
        room.handle_client_event('item_list', client, message['items'])

    def on_itempickup(self, client, room, message):
        player = client.get_player(message['aiclientnum'])
        room.handle_player_event('pickup_item', player, message['item_index'])


    def on_jumppad(self, client, room, message):
        player = client.get_player(message['aiclientnum'])
        room.handle_player_event('jumppad', player, message['jumppad'])

    def on_kick(self, client, room, message):
        room.handle_client_event('kick', client, message['target_cn'], message['reason'])

    def on_mapchange(self, client, room, message):
        # TODO: never called?
        # room.handle_client_event('map_vote', client, message['map_name'], message['mode_num'])
        pass

    def on_mapcrc(self, client, room, message):
        room.handle_client_event('map_crc', client, message['mapcrc'])

    @tracer
    def on_mapvote(self, client, room, message):
        client.role.handle_event('map_vote', room, client, message['map_name'], message['mode_num'])

    def on_mastermode(self, client, room, message):
        room.handle_client_event('set_master_mode', client, message['mastermode'])

    def on_newmap(self, client, room, message):
        room.handle_client_event('edit_new_map', client, message['size'])

    def on_paste(self, client, room, message):
        del message['aiclientnum']
        player = client.get_player()
        selection = Selection.from_message(message)
        room.handle_player_event('edit_paste', player, selection)

    def on_pausegame(self, client, room, message):
        room.handle_client_event('pause_game', client, message['value'])

    def on_ping(self, client, room, message):
        with client.sendbuffer(1, False) as cds:
            swh.put_pong(cds, message['cmillis'])

    def on_pos(self, client, room, message):
        player = client.get_player(message['clientnum'])
        player.state.update_position(message['position'], message['raw_position'])

    def on_remip(self, client, room, message):
        room.handle_client_event('edit_remip', client)

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

    def on_sayteam(self, client, room, message):
        player = client.get_player()
        room.handle_player_event('team_chat', player, message['text'])

    def on_servcmd(self, client, room, message):
        room.handle_client_event('command', client, message['command'])

    def on_authpass(self, client, room, message):
        print(message)
        room.handle_client_event('auth_pass', client, message)

    def on_setmaster(self, client, room, message):
        room.handle_client_event('set_master', client, message['target_cn'], message['pwdhash'], message['value'])

    def on_setteam(self, client, room, message):
        team_name = filtertext(message['team'], False, MAXTEAMLEN)
        room.handle_client_event('set_team', client, message['target_cn'], team_name)

    def on_sound(self, client, room, message):
        player = client.get_player(message['aiclientnum'])
        room.handle_player_event('sound', player, message['sound'])

    def on_spawn(self, client, room, message):
        player = client.get_player(message['aiclientnum'])
        room.handle_player_event('spawn', player, message['lifesequence'], message['gunselect'])

    def on_spectator(self, client, room, message):
        room.handle_client_event('set_spectator', client, message['target_cn'], bool(message['value']))

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

    def on_takeflag(self, client, room, message):
        player = client.get_player(message['aiclientnum'])
        room.handle_player_event('take_flag', player, message['flag'], message['version'])

    def on_taunt(self, client, room, message):
        player = client.get_player()
        room.handle_player_event('taunt', player)

    def on_teleport(self, client, room, message):
        player = client.get_player(message['aiclientnum'])
        room.handle_player_event('teleport', player, message['teleport'], message['teledest'])

    def on_text(self, client, room, message):
        player = client.get_player()
        room.handle_player_event('game_chat', player, message['text'])

    def on_trydropflag(self, client, room, message):
        player = client.get_player(message['aiclientnum'])
        room.handle_player_event('try_drop_flag', player)
        
    def on_tryspawn(self, client, room, message):
        player = client.get_player(message['aiclientnum'])
        room.handle_player_event('request_spawn', player)

    def on_getmap(client, room, message):
        room.handle_client_event('edit_get_map', client)

    def on_flip(client, room, message):
        del message['aiclientnum']
        player = client.get_player()
        selection = Selection.from_message(message)
        room.handle_player_event('edit_flip', player, selection)
