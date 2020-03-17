from cube2protocol.cube_data_stream import CubeDataStream
from cube2common.constants import client_states
from cube2common.constants import weapon_types
from spyd.utils.constrain import constrain_range
from spyd.protocol import swh
from spyd.game.room.exceptions import UnknownEvent

class PlayerEventHandler(object):
    def __init__(self):
        self.actions = {
            'take_flag': self.on_take_flag,
            'replenish_ammo': self.on_replenish_ammo,
            'spawn': self.on_spawn,
            'edit_material': self.on_edit_material,
            'switch_model': self.on_switch_model,
            'explode': self.on_explode,
            'edit_paste': self.on_edit_paste,
            'pickup_item': self.on_pickup_item,
            'edit_flip': self.on_edit_flip,
            'edit_replace': self.on_edit_replace,
            'jumppad': self.on_jumppad,
            'taunt': self.on_taunt,
            'edit_copy': self.on_edit_copy,
            'edit_rotate': self.on_edit_rotate,
            'edit_texture': self.on_edit_texture,
            'teleport': self.on_teleport,
            'team_chat': self.on_team_chat,
            'edit_delete_cubes': self.on_edit_delete_cubes,
            'suicide': self.on_suicide,
            'try_drop_flag': self.on_try_drop_flag,
            'edit_entity': self.on_edit_entity,
            'edit_face': self.on_edit_face,
            'shoot': self.on_shoot,
            'switch_team': self.on_switch_team,
            'edit_mode': self.on_edit_mode,
            'gunselect': self.on_gunselect,
            'switch_name': self.on_switch_name,
            'sound': self.on_sound,
            'request_spawn': self.on_request_spawn,
            'game_chat': self.on_game_chat,
        }

    def handle_event(self, event_name, *args, **kwargs):
        action = self.actions.get(event_name, self.on_unknown_event)
        return action(*args, **kwargs)

    def on_unknown_event(self, ev_name, *args, **kwargs):
        print("===ERROR UnknownEvent:", *args, **kwargs)
        raise UnknownEvent('Event: '+ev_name+' Arguments: '+str(args) + str(kwargs))


    def on_take_flag(self, room, player, flag, version):
        room.gamemode.on_player_take_flag(player, flag, version)

    def on_replenish_ammo(self, room, player):
        pass

    def on_spawn(self, room, player, lifesequence, gunselect):
        constrain_range(gunselect, weapon_types.GUN_FIST, weapon_types.GUN_PISTOL, "weapon_types")
        player.state.on_respawn(lifesequence, gunselect)

    def on_edit_material(self, room, selection, material, material_filter):
        pass

    def on_switch_model(self, room, player, playermodel):
        constrain_range(playermodel, 0, 4, "playermodels")
        player.playermodel = playermodel
        swh.put_switchmodel(player.state.messages, playermodel)

    def on_explode(self, room, player, cmillis, gun, explode_id, hits):
        constrain_range(gun, weapon_types.GUN_FIST, weapon_types.GUN_PISTOL, "weapon_types")
        room.gamemode.on_player_explode(player, cmillis, gun, explode_id, hits)

    def on_edit_paste(self, room, selection):
        pass

    def on_pickup_item(self, room, player, item_index):
        room.gamemode.on_player_pickup_item(player, item_index)

    def on_edit_flip(self, room, selection):
        pass

    def on_edit_replace(self, room, selection, texture, new_texture, in_selection):
        pass

    def on_jumppad(self, room, player, jumppad):
        room._broadcaster.jumppad(player, jumppad)

    def on_taunt(self, room, player):
        room.gamemode.on_player_taunt(player)

    def on_edit_copy(self, room, selection):
        pass

    def on_edit_rotate(self, room, selection, axis):
        pass

    def on_edit_texture(self, room, selection, texture, all_faces):
        pass

    def on_teleport(self, room, player, teleport, teledest):
        room._broadcaster.teleport(player, teleport, teledest)

    def on_team_chat(self, room, player, text):
        if player.isai: return

        if player.state.is_spectator:
            clients = [c for c in room.clients if c.get_player().state.is_spectator]
        else:
            clients = [c for c in room.clients if c.get_player().team == player.team]

        with room.broadcastbuffer(1, True, [player.client], clients) as cds:
            swh.put_sayteam(cds, player.client, text)

            room.event_subscription_fulfiller.publish('spyd.game.player.chat', {'player': player.uuid, 'room': room.name, 'text': text, 'scope': 'team'})

    def on_edit_delete_cubes(self, room, selection):
        pass

    def on_suicide(self, room, player):
        player.state.state = client_states.CS_DEAD
        room.gamemode.on_player_death(player, player)
        room._broadcaster.player_died(player, player)

    def on_try_drop_flag(self, room, player):
        room.gamemode.on_player_try_drop_flag(player)

    def on_edit_entity(self, room, player, entity_id, entity_type, x, y, z, attrs):
        pass

    def on_edit_face(self, room, selection, direction, mode):
        pass

    def on_shoot(self, room, player, shot_id, gun, from_pos, to_pos, hits):
        constrain_range(gun, weapon_types.GUN_FIST, weapon_types.GUN_PISTOL, "weapon_types")
        room.gamemode.on_player_shoot(player, shot_id, gun, from_pos, to_pos, hits)

    def on_switch_team(self, room, player, team_name):
        room.gamemode.on_player_try_set_team(player, player, player.team.name, team_name)

    def on_edit_mode(self, room, player, editmode):
        with room.broadcastbuffer(1, True, [player]) as cds:
            tm = CubeDataStream()
            swh.put_editmode(tm, editmode)
            swh.put_clientdata(cds, player.client, str(tm))

    def on_gunselect(self, room, player, gunselect):
        constrain_range(gunselect, weapon_types.GUN_FIST, weapon_types.GUN_PISTOL, "weapon_types")
        player.state.gunselect = gunselect
        swh.put_gunselect(player.state.messages, gunselect)

    def on_switch_name(self, room, player, name):
        player.name = name
        swh.put_switchname(player.state.messages, name)
        # with room.broadcastbuffer(1, True) as cds:
        #    tm = CubeDataStream()
        #    swh.put_switchname(tm, "aaaaa")
        #    swh.put_clientdata(cds, player.client, str(tm))

    def on_sound(self, room, player, sound):
        swh.put_sound(player.state.messages, sound)

    def on_request_spawn(self, room, player):
        room.gamemode.on_player_request_spawn(player)

    def on_game_chat(self, room, player, text):
        if text[0] == "#":
            room.command_executer.execute(room, player.client, text)
        else:
            swh.put_text(player.state.messages, text)
            room.event_subscription_fulfiller.publish('spyd.game.player.chat', {'player': player.uuid, 'room': room.name, 'text': text, 'scope': 'room'})
