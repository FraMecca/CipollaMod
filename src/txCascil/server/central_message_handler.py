from txCascil.permissions.functionality import Functionality


class UnknownMessageType(Exception): pass
class PermissionDenied(Exception): pass


class UnknownMessageHandler(object):
    execute = Functionality('unknown_message')

    @staticmethod
    def handle_message(spyd_server, gep_client, message):
        raise UnknownMessageType(repr(message.get('msgtype', None)))

class CentralMessageHandler(object):
    def __init__(self, message_handlers):
        self._message_handlers = message_handlers

    def _get_message_handler(self, message):
        msgtype = message.get('msgtype')
        return self._message_handlers.get(msgtype, UnknownMessageHandler)

    def handle_message(self, context, client_controller, message):
        message_handler = self._get_message_handler(message)
        if hasattr(message_handler, 'execute') and hasattr(client_controller, 'allowed'):
            if not client_controller.allowed(message_handler.execute):
                raise PermissionDenied()
        message_handler.handle_message(context, client_controller, message)
