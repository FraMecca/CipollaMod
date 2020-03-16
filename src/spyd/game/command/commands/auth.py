from spyd.registry_manager import register
from spyd.permissions.functionality import Functionality
from spyd.game.command.command_base import CommandBase
from spyd.game.client.exceptions import UsageError


@register("command")
class AuthCommand(CommandBase):
    name = "auth"
    description = "Authenticate as admin"
    functionality = Functionality("spyd.game.commands.authpass.execute", "You do not have permission to execute {action#command}", command=name)

    @classmethod
    def execute(cls, spyd_server, room, client, command_string, arguments, raw_args):
        if not arguments:
            raise UsageError("You must provide a password")

        room.handle_client_event('auth_pass', client, arguments)
