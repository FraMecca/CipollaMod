from txCascil.client.client_controller import ClientController
from txCascil.server.central_message_handler import CentralMessageHandler


class ClientControllerFactory(object):
    def __init__(self, context, message_handlers):
        self._context = context
        self._message_handlers = message_handlers

    def build(self, client_addr, protocol, authentication_controller, request_queue):
        central_message_handler = CentralMessageHandler(self._message_handlers)
        return ClientController(self._context, client_addr, protocol, central_message_handler, authentication_controller, request_queue)
