import time
from cube2common.constants import privileges, disconnect_types
from cipolla.config_manager import ConfigManager
from cipolla.mods.abstract_mod import AbstractMod
from cipolla.mods.mods_manager import ModsManager
from cipolla.game.server_message_formatter import *


class CommandsMod(AbstractMod):
    canLoad = True # specify that mod can be loaded at runtime
    name = 'commands'

    def __init__(self):
        self.admin_pass = ConfigManager().server.adminpass
        self.actions = {
            # 'ban':                self.deny,
            # 'spectate':           self.deny,
            # 'changemap':          self.deny,
            # 'duel':               self.deny,
            # 'skip':               self.deny,
            'auth':               self.auth,
            'giveadmin':          self.give_admin,
            'givemaster':         self.give_master,
            'relinquish':         self.relinquish_privileges,
            'kick':               self.kick,
            'mod':                self.manage_mod,
            'pm':                 self.pm,
            'help':               self.help,
            'info':               self.info,
            'stats':              self.stats,
        }


    def setup(self, room):
        method_name = 'game_chat'
        target = room._player_event_handler
        self.old_method = target.actions[method_name]
        target.actions[method_name] = self.on_text_event
        self.old_methods = [(target, method_name, self.old_method)]

    def can_attach(self, room):
        return True

    def exec_command(self, room, player, text):
        args = text.split(' ')
        cmd = args[0]
        text = text[len(cmd)+1:]

        if cmd not in self.actions:
            player.client.send_server_message(usage_error('Command does not exist'))
        else:
            self.actions[cmd](room, player, text)

    def on_text_event(self, room, player, text):
        if text[0] == '#':
            self.exec_command(room, player, text[1:])
        else:
            self.old_method(room, player, text)

    def get_client_number(self, cn):
        try:
            target_cn = int(cn)
            return target_cn
        except:
            return None

    def deny(self, player, *args, **kwargs):
        player.client.send_server_message(denied('You don\'t have the permission to do that'))

    def manage_mod(self, room, player, args):
        mod_actions = {
            'on': Mod.on,
            'off': Mod.off,
            'reload': Mod.reload,
            'list': Mod.list
        }

        args = args.split(' ')
        mod_name = args[-2] if len(args) > 1 else ''
        action = args[-1]

        if not player.privilege == privileges.PRIV_ADMIN:
            self.deny(player)
        else:
            if action != 'list' and mod_actions[action](mod_name, room):
                player.client.send_server_message(info(f'mod [{mod_name}] {action}'))
            elif action == 'list':
                mods_list = mod_actions[action](mod_name, room)
                message = ' | '.join(map(orange, mods_list))
                player.client.send_server_message(info('Mods available:'))
                player.client.send_server_message(message)
            else:
                player.client.send_server_message(usage_error(f'mod [{mod_name}] does not exist'))

    def auth(self, room, player, args):
        passw = args
        if args == self.admin_pass:
            client = player.client
            room.change_privilege(client, privileges.PRIV_ADMIN)
            player.client.send_server_message(info('Now you are the masta admin'))
        else:
            player.client.send_server_message(info('Wrong password :)'))

    def give_master(self, room, player, args):
        target_cn = self.get_client_number(args)
        client = player.client

        if not player.privilege >= privileges.PRIV_MASTER:
            self.deny(player)
        elif target_cn is None:
            player.client.send_server_message(error('Cannot get client number!'))
            return
        else:
            target_client = room.get_client(target_cn)
            if target_client:
                room.change_privilege(target_client, privileges.PRIV_MASTER)
                target_client.send_server_message(info('You are Master :)'))
            else:
                player.client.send_server_message(error('Client number does not exist'))

    def give_admin(self, room, player, args):
        target_cn = self.get_client_number(args)
        client = player.client

        if not player.privilege >= privileges.PRIV_ADMIN:
            self.deny(player)
        elif target_cn is None:
            player.client.send_server_message(error('Cannot get client number!'))
            return
        else:
            target_client = room.get_client(target_cn)
            if target_client:
                room.change_privilege(target_client, privileges.PRIV_ADMIN)
                target_client.send_server_message(info('You are Admin :)'))
            else:
                player.client.send_server_message(error('Client number does not exist'))

    def relinquish_privileges(self, room, player, args):
        target_cn = self.get_client_number(args)
        client = player.client

        if not player.privilege >= privileges.PRIV_ADMIN:
            self.deny(player)
        elif target_cn is None:
            player.client.send_server_message(error('Cannot get client number!'))
            return
        else:
            target_client = room.get_client(target_cn)
            if target_client:
                room.change_privilege(target_client, privileges.PRIV_NONE)
                target_client.send_server_message(info('You are a normal user'))
            else:
                player.client.send_server_message(error('Client number does not exist'))

    def pm(self, room, player, args):
        args = args.split(' ')
        target_name = args[0]
        message = ' '.join(args[1:])
        target_player = room.get_player_by_name(target_name)
        if not target_player:
            player.client.send_server_message(error('Player not found'))
        else:
            message = format_cfg_message(message, room, player)
            print(message)
            player.client.send_server_message(info('PM sent'))
            target_player.client.send_server_message(notice(f'{player.name} send you a pm:'))
            target_player.client.send_server_message(message)

    def kick(self, room, player, args):
        target_cn = self.get_client_number(args)
        client = player.client
        target_player = room.get_player(target_cn)

        if not target_player:
            player.client.send_server_message(error(f'Client number [{target_cn}] does not exist'))
        elif not player.privilege >= privileges.PRIV_MASTER or player.privilege < target_player.privilege:
            self.deny(player)
        elif not target_player:
            player.client.send_server_message(error('Client number does not exist'))
        elif target_cn is None:
            player.client.send_server_message(error('Invalid client number'))
        else:
            target_client = room.get_client(target_cn)
            target_client.disconnect(disconnect_types.DISC_KICK, error("You were kicked by {name#kicker}", kicker=client))

    def help(self, room, player, args):
        available_commands = self.actions.keys()
        formatted_command_list = list(map(lambda s: '#'+s, available_commands))
        player.client.send_server_message("\f7Commands: " + " | ".join(map(yellow, formatted_command_list)))

    def info(self, room, player, args):
        player.client.send_server_message(info(ConfigManager().server.info))

    def stats(self, *args, **kwargs):
        #TODO statsss
        pass

class Mod:
    @staticmethod
    def on(mod_name, room):
        if room.is_mod_active(mod_name):
            return False
        ModsManager().enable(mod_name, room)
        return True

    @staticmethod
    def off(mod_name, room):
        if not room.is_mod_active(mod_name):
            return False
        ModsManager().disable(mod_name, room)
        return True

    @staticmethod
    def reload(mod_name, room):
        if not room.is_mod_active(mod_name):
            return False
        ModsManager().reload(mod_name, room)
        return True

    @staticmethod
    def list(*args, **kwargs):
        return ModsManager().list_mods()
