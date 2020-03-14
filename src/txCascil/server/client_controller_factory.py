from txCascil.server.central_message_handler import CentralMessageHandler
from txCascil.server.client_controller import ClientController


class ClientControllerFactory(object):
    def __init__(self, context, message_handlers, permission_resolver, event_subscription_fulfiller):
        self._context = context
        self._message_handlers = message_handlers
        self._permission_resolver = permission_resolver
        self._event_subscription_fulfiller = event_subscription_fulfiller

    def build(self, client_addr, protocol, authentication_controller):
        central_message_handler = CentralMessageHandler(self._message_handlers)
        return ClientController(self._context, client_addr, protocol, authentication_controller, central_message_handler, self._permission_resolver, self._event_subscription_fulfiller)
