from txCascil.exceptions import AuthenticationHardFailure
from txCascil.events import SubscriptionError


class ClientController(object):
    def __init__(self, context, client_addr, protocol, authentication_controller, central_message_handler, permission_resolver, event_subscription_fulfiller):
        self._context = context
        self._client_addr = client_addr
        self._protocol = protocol
        self._authentication_controller = authentication_controller
        self._central_message_handler = central_message_handler
        self._event_subscription_fulfiller = event_subscription_fulfiller
        self._permission_resolver = permission_resolver

        self._event_subscriptions = {}

    def send(self, message, respid=None):
        if respid is not None:
            message['respid'] = respid
        self._protocol.send(message)

    @property
    def is_authenticated(self):
        return self._authentication_controller.is_authenticated

    def get_group_names(self):
        return self._authentication_controller.groups

    def allowed(self, functionality):
        group_names = self.get_group_names()
        return self._permission_resolver.groups_allow(group_names, functionality)

    def connection_established(self):
        pass

    def receive(self, message):
        if self.is_authenticated:
            self._receive_authenticated(message)
        else:
            self._receive_not_authenticated(message)

    def disconnected(self):
        for event_subscription in self._event_subscriptions.values():
            event_subscription.unsubscribe()

    def _receive_not_authenticated(self, message):
        try:
            self._authentication_controller.receive(message)
        except AuthenticationHardFailure:
            self.send({"msgtype": "error", "message": "Authentication failure"}, message.get('reqid', None))
            self._protocol.disconnect()

    def _receive_authenticated(self, message):
        try:
            msgtype = message.get('msgtype')
            if msgtype == 'subscribe':
                self._receive_subscribe_message(message)
            elif msgtype == 'unsubscribe':
                self._receive_unsubscribe_message(message)
            else:
                self._central_message_handler.handle_message(self._context, self, message)
        except Exception as e:
            self.send({"msgtype": "error", "message": e.message}, message.get('reqid', None))
            
    def _receive_subscribe_message(self, message):
        self.subscribe(message.get('event_stream'))
        self.send({"msgtype": "status", "status": "success"}, message.get('reqid'))

    def _receive_unsubscribe_message(self, message):
        self.unsubscribe(message.get('event_stream'))
        self.send({"msgtype": "status", "status": "success"}, message.get('reqid'))

    def subscribe(self, event_stream):
        if event_stream in self._event_subscriptions: raise SubscriptionError("Already subscribed")
        event_subscription = self._event_subscription_fulfiller.subscribe(event_stream, self._on_subscribed_event)
        self._event_subscriptions[event_stream] = event_subscription

    def unsubscribe(self, event_stream):
        event_subscription = self._event_subscriptions.pop(event_stream, None)
        if event_subscription is None: raise SubscriptionError("Not subscribed")
        event_subscription.unsubscribe()

    def _on_subscribed_event(self, event_stream, data):
        self.send({"msgtype": "event", "event_stream": event_stream, "event_data": data})
