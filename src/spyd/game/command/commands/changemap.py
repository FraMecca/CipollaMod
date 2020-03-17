from spyd.game.client.exceptions import InsufficientPermissions
from spyd.game.command.command_base import CommandBase
from spyd.game.gamemode import gamemodes
from spyd.permissions.functionality import Functionality
from spyd.registry_manager import register
from twisted.internet import defer
from spyd.game.map.resolve_map_name import resolve_map_name


@register("command")
class ChangeMapCommand(CommandBase):
    name = "<mode>"
    functionality = Functionality("spyd.game.commands.resume.execute", "You do not have permission to execute {action#command}", command=name)
    usage = "<map>"
    description = "Change the mode and map."

    @classmethod
    def handles(cls, room, client, command_string):
        return command_string in gamemodes

    @classmethod
    @defer.inlineCallbacks
    def execute(cls, spyd_server, room, client, command_string, arguments, raw_args):
        mode_name = command_string
        map_name = arguments[0]

        map_name = yield resolve_map_name(room, map_name)

        room.change_map_mode(map_name, mode_name)
