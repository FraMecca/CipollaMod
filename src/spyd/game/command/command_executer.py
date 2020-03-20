import re
import shlex

from spyd.game.client.exceptions import GenericError, InsufficientPermissions
from spyd.game.command.command_finder import CommandFinder
from twisted.internet import defer


command_pattern = re.compile("^#(?P<command_string>[\w-]+)(\s(?P<arg_string>.*))?$")

class CommandExecuter(object):
    def __init__(self, spyd_server):
        self._command_finder = CommandFinder()
        self._spyd_server = spyd_server

    def execute(self, room, client, raw_command_string):
        command_match = command_pattern.match(raw_command_string)

        if command_match is None:
            raise GenericError("Invalid command input.")

        command_string = command_match.group('command_string')
        arg_string = command_match.group('arg_string') or ""

        if command_string is None:
            raise GenericError("Invalid command input.")

        command_handler = self._command_finder.find(room, client, command_string)

        if command_handler is None:
            raise GenericError("Unknown command.")

        execute_functionality = command_handler.functionality

        if not client.allowed(execute_functionality):
            raise InsufficientPermissions(execute_functionality.denied_message)

        try:
            args = shlex.split(arg_string)
        except ValueError as e:
            raise GenericError("Invalid input: {error}", error=e.message)

        d = defer.maybeDeferred(command_handler.execute, self._spyd_server, room, client, command_string, args, arg_string)
        d.addErrback(client.handle_exception)

    def get_available_commands(self, client):
        command_list = self._command_finder.get_command_list()
        command_list = [c for c in command_list if client.allowed(c.functionality)]
        return command_list
