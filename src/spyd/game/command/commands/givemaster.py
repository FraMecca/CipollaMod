from spyd.registry_manager import register
from spyd.permissions.functionality import Functionality
from spyd.game.command.command_base import CommandBase
from spyd.game.client.exceptions import UsageError, GenericError


@register("command")
class GiveMasterCommand(CommandBase):
    name = "givemaster"
    description = "Give master to a client"
    functionality = Functionality("spyd.game.commands.givemaster.execute", "You do not have permission to execute {action#command}", command=name)

    @classmethod
    def execute(cls, spyd_server, room, client, command_string, arguments, raw_args):
        player_name = arguments[0] if arguments else ''
        players = dict(map(lambda player: (player.name, player.client), room.players))

        if not player_name:
            raise UsageError("You must provide a player")

        if player_name not in players.keys():
            raise GenericError('The player doesn\'t exist')

        room.handle_client_event('give_master', client, players[player_name])
