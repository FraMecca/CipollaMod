import itertools
import traceback

from twisted.internet import defer
from twisted.internet.error import ConnectionLost

from txCascil.exceptions import AuthenticationHardFailure


class ClientController(object):
    def __init__(self, context, client_addr, protocol, central_message_handler, authentication_controller, request_queue):
        self._context = context
        self._client_addr = client_addr
        self._protocol = protocol
        self._authentication_controller = authentication_controller
        self._central_message_handler = central_message_handler
        self._request_id_counter = itertools.count()
        self._pending_requests = {}
        self._request_queue = request_queue

    def send(self, message, respid=None):
        if respid is not None:
            message['respid'] = respid
        self._protocol.send(message)
        
    def request(self, message, d=None):
        if d is None:
            d = defer.Deferred()
        reqid = next(self._request_id_counter)
        message['reqid'] = reqid
        self._pending_requests[reqid] = d
        self.send(message)
        return d

    @property
    def is_authenticated(self):
        return self._authentication_controller.is_authenticated

    def receive(self, message):
        if self.is_authenticated:
            self._receive_authenticated(message)
        else:
            self._receive_not_authenticated(message)

    def connection_established(self):
        self._authentication_controller.connection_established()

    def disconnected(self):
        self._request_queue.detach()
        pending_requests = self._pending_requests
        self._pending_requests = None
        for request_deferred in pending_requests.values():
            request_deferred.errback(ConnectionLost())

    def _receive_not_authenticated(self, message):
        try:
            self._authentication_controller.receive(message)
            if self.is_authenticated:
                self._request_queue.attach(self)
                self._receive_authenticated({'msgtype': 'authenticated'})
        except AuthenticationHardFailure as e:
            self.send({"msgtype": "error", 'type': e.type, "message": "Authentication failure"}, message.get('reqid', None))
            self._protocol.disconnect()

    def _receive_authenticated(self, message):
        try:
            respid = message.pop('respid', None)
            request_deferred = self._pending_requests.pop(respid, None)
            if request_deferred is not None:
                request_deferred.callback(message)
        except:
            traceback.print_exc()

        try:
            self._central_message_handler.handle_message(self._context, self, message)
        except:
            traceback.print_exc()
