import time

from cube2common.constants import mastermodes, disconnect_types, privileges
from spyd.game.server_message_formatter import error
from spyd.punitive_effects.punitive_effect_info import TimedExpiryInfo, EffectInfo
from spyd.game.client.exceptions import InsufficientPermissions
from spyd.game.gamemode.gamemodes import get_mode_name_from_num
from spyd.game.map.resolve_map_name import resolve_map_name
from spyd.game.client.exceptions import InsufficientPermissions, StateError
from spyd.game.server_message_formatter import info, smf
from spyd.game.room.exceptions import UnknownEvent
from spyd.game.client.exceptions import *

class BaseRole(object):
    def __init__(self):
        self.privilege = privileges.PRIV_NONE

        self.actions = {
            'set_master': self.on_set_master,
            'check_maps': self.on_check_maps,
            'set_bot_limit': self.on_set_bot_limit,
            'item_list': self.on_item_list,
            'flag_list': self.on_flag_list,
            'edit_remip': self.on_edit_remip,
            'give_master': self.on_not_allowed,
            'delete_bot': self.on_delete_bot,
            'edit_new_map': self.on_edit_new_map,
            'set_master_mode': self.on_set_master_mode,
            'set_team': self.on_set_team,
            'list_demos': self.on_list_demos,
            'add_bot': self.on_add_bot,
            'set_spectator': self.on_set_spectator,
            'clear_demo': self.on_clear_demo,
            'base_list': self.on_base_list,
            'stop_demo_recording': self.on_stop_demo_recording,
            'pause_game': self.on_pause_game,
            'map_crc': self.on_map_crc,
            'kick': self.on_not_allowed,
            'map_vote': self.on_map_vote,
            'set_demo_recording': self.on_set_demo_recording,
            'auth_pass': self.on_auth,
            'clear_bans': self.on_clear_bans,
            'command': self.on_command,
            'set_bot_balance': self.on_set_bot_balance,
            'get_demo': self.on_get_demo,
            'set_game_speed': self.on_set_game_speed,
            'edit_get_map': self.on_edit_get_map,
        }

        self.text_actions = {
            'kick': self.on_not_allowed,
            'ban': self.on_not_allowed,
            'givemaster': self.on_not_allowed,
            'giveadmin': self.on_not_allowed,
            'relinquishmaster': self.on_not_allowed,
            'dropprivileges': self.on_not_allowed,
            'spectate': self.on_not_allowed,
            'changemap': self.on_not_allowed,
            'duel': self.on_not_allowed,
            # 'pm': self.on_pm, TODO implement this
            'auth': self.on_auth,
            'commands': self.on_commands,
            'info': self.on_info,
            'stats': self.on_stats,
        }


    def handle_event(self, event_name, room, *args, **kwargs):
        action = self.actions.get(event_name, self.on_unknown_event)
        return action(room, *args, **kwargs)

    # from game_event_handler
    def handle_text_event(self, text, room, player):
        def parse(text):
            text = text[1:].split(' ')
            return text[0], text[1:]

        cmd, args = parse(text)

        if not cmd in self.text_actions:
            client.server.message('Command has not exist. Type #commands for more info')

        return self.text_actions[cmd](room, player, args)

    def on_unknown_event(self, ev_name, *args, **kwargs):
        print("===ERROR UnknownEvent:", *args, **kwargs)
        raise UnknownEvent('Event: '+ev_name+' Arguments: '+str(args) + str(kwargs))

    def on_set_master(self, room, client, target_cn, password_hash, requested_privilege):
        target = room.get_client(target_cn)
        if target is None:
            raise UnknownPlayer(cn=target_cn)

        room._client_try_set_privilege(client, target, requested_privilege, password_hash)

    def on_check_maps(self, room, client):
        pass

    def on_set_bot_limit(self, room, client, limit):
        pass

    def on_item_list(self, room, client, item_list):
        room.gamemode.on_client_item_list(client, item_list)

    def on_flag_list(self, room, client, flag_list):
        room.gamemode.on_client_flag_list(client, flag_list)

    def on_edit_remip(self, room, client):
        pass

    # def on_give_master(self, room, client, client_target):
    #     room._client_change_privilege(client, client_target, 1)

    def on_delete_bot(self, room, client):
        pass

    def on_edit_new_map(self, room, client, size):
        pass

    def on_set_master_mode(self, room, client, mastermode):
        # allowed_set_mastermode = client.allowed(set_mastermode_functionality) or (room.temporary and client.allowed(temporary_set_mastermode_functionality))

        # if not allowed_set_mastermode:
        #     raise InsufficientPermissions('Insufficient permissions to change mastermode.')
        if mastermode == mastermodes.MM_PRIVATE:
            raise GenericError("Mastermode private not allowed")
        if mastermode < mastermodes.MM_OPEN or mastermode > mastermodes.MM_PRIVATE:
            raise GenericError("Mastermode out of allowed range.")

        room.set_mastermode(mastermode)

    def on_set_team(self, room, client, target_pn, team_name):
        player = room.get_player(target_pn)
        if player is None:
            raise UnknownPlayer(cn=target_pn)

        room.gamemode.on_player_try_set_team(client.get_player(), player, player.team.name, team_name)

    def on_list_demos(self, room, client):
        pass

    def on_add_bot(self, room, client, skill):
        pass

    def on_set_spectator(self, room, client, target_pn, spectate):
        player = room.get_player(target_pn)
        if player is None:
            raise UnknownPlayer(cn=target_pn)
        room._set_player_spectator(player, spectate)

    def on_clear_demo(self, room, client, demo_id):
        pass

    def on_base_list(self, room, client, base_list):
        room.gamemode.on_client_base_list(client, base_list)

    def on_stop_demo_recording(self, room, client):
        pass

    def on_pause_game(self, room, client, pause):
        if pause:
            if room.is_paused and not room.is_resuming: raise StateError('The game is already paused.')
            room.pause()
            room._broadcaster.server_message(info(f"{client.get_player().name} has paused the game."))
        elif not pause:
            if not room.is_paused: raise StateError('The game is already resumed.')
            room.resume()
            room._broadcaster.server_message(info(f"{client.get_player().name} has resumed the game."))

    def on_map_crc(self, room, client, crc):
        # TODO: Implement optional spectating of clients without valid map CRC's
        room.ready_up_controller.on_crc(client, crc)

    # def on_kick(self, room, client, target_pn, reason):
    #     # TODO: Permissions checks

    #     target_client = room.get_client(target_pn)

    #     expiry_time = time.time() + (4 * SECONDS_PER_HOUR)

    #     client._punitive_model.add_effect('ban', target_client.host, EffectInfo(TimedExpiryInfo(expiry_time)))

    #     target_client.disconnect(disconnect_types.DISC_KICK, error("You were kicked by {name#kicker}", kicker=target_client))

    def on_map_vote(self, room, client, map_name, mode_num):
        mode_name = get_mode_name_from_num(mode_num)
        map_name = yield resolve_map_name(room, map_name)
        room.change_map_mode(map_name, mode_name)

    def on_set_demo_recording(self, room, client, value):
        pass

    def on_auth(self, room, client, message):
        # passw = message[0]
        # admin_pass = config_loader('config.json')['room_bindings'][room._name.value]['adminpass']

        # if passw == admin_pass:
        #     room._client_change_privilege(client, client, 3)
        # else:
        #     raise WrongCredentials("Eheh, try again :)")
        pass

    def on_clear_bans(self, room, client):
        # TODO: Permissions checks
        client._punitive_model.clear_effects('ban')

    def on_command(self, room, client, command):
        pass

    def on_set_bot_balance(self, room, client, balance):
        pass

    def on_get_demo(self, room, client, demo_id):
        pass

    def on_set_game_speed(self, room, client, speed):
        pass

    def on_edit_get_map(self, room, client):
        pass

    def on_not_allowed(self, room, player, command, *args, **kwargs):
        message = 'You don\'t have the permission to execute command: ' + command
        player.client.send_server_message(message)

    def on_commands(self, room, player, *args, **kwargs):
        available_commands = self.text_actions.keys()
        formatted_command_list = list(map(lambda s: '#'+s, available_commands))
        player.client.send_server_message("\f7Commands: " + " | ".join(formatted_command_list))

    def on_info(self, *args, **kwargs):
        #TODO get info server
        # client.send_server_message(info(spyd_server.server_info_model.value))
        pass

    def on_stats(self, *args, **kwargs):
        #TODO statsss
        pass


class MasterRole(BaseRole):
    def __init__(self):
        super().__init__()
        self.privilege = privileges.PRIV_MASTER

        master_actions = {
            'kick': self.on_kick,
        #TODO finish
        #     'ban': self.on_ban,
        #     'givemaster': self.on_givemaster,
        #     'spectate': self.on_spectate,
        #     'changemap': self.on_changemap,
        #     'duel': self.on_duel,
        #     'dropprivileges': self.on_drop_privileges,
        }

        self.text_actions.update(master_actions)

    def get_target_client(self, room, player, target_pn):
        if not target_pn.is_digit():
            player.client.send_server_message('Invalid player number')
        else:
            target_client = room.get_client(int(target_pn))
            if target_client is None:
                player.client.send_server_message('Player doesn\'t exist')
            else:
                return target_client

        return None


    def on_kick(self, room, player, args):
        target_client = get_target_client(room, player, args[0])

        if target_client:
            expiry_time = time.time() + (4 * SECONDS_PER_HOUR)
            client._punitive_model.add_effect('ban', target_client.host, EffectInfo(TimedExpiryInfo(expiry_time)))
            target_client.disconnect(disconnect_types.DISC_KICK, error("You were kicked by {name#kicker}", kicker=target_client))

class AdminRole(MasterRole):
    pass
