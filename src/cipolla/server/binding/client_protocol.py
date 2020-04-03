import traceback

from twisted.internet import reactor # type: ignore
from twisted.internet.protocol import connectionDone # type: ignore

from cube2common.constants import disconnect_types # type: ignore
from cipolla.utils.rate_limiter import RateLimiter # type: ignore
from txENet.enet_client_protocol import ENetClientProtocol # type: ignore
import enet # type: ignore


class ClientProtocol(ENetClientProtocol):
    def __init__(self, client_factory, message_processor, message_rate_limit):
        self._client_factory = client_factory
        self._message_processor = message_processor

        self._message_rate_limiter = RateLimiter(message_rate_limit)

        self._client = None
        self._disconnecting_later = None

    def connectionMade(self):
        self._client = self._client_factory.build_client(self, self.transport.connected_port)
        self.factory.protocol_connected(self)
        self._client.connected()

    def receiveEventReceived(self, event):
        if event.packet.flags & enet.PACKET_FLAG_UNSEQUENCED: return
        self.dataReceived(event.channelID, event.packet.data)

    def dataReceived(self, channel, data):
        try:
            processed_messages = self._message_processor.process(channel, data)
        except:
            print("Error processing messages from {}:{}".format(self._client.host, self._client.port))
            traceback.print_exc()
            self.disconnect(disconnect_types.DISC_MSGERR)
            return

        for processed_message in processed_messages:
            if not self._message_rate_limiter.check_drop():
                self._client._message_received(*processed_message)
            else:
                self.disconnect(disconnect_types.DISC_OVERFLOW)

    def connectionLost(self, reason=connectionDone):
        self.factory.protocol_disconnected(self)
        self._client.disconnected()
        ENetClientProtocol.connectionLost(self, reason=reason)
        if self._disconnecting_later is not None:
            self._disconnecting_later.cancel()

    def disconnect(self, disconnect_type):
        if self._disconnecting_later is not None:
            self._disconnecting_later = None
        self.transport.disconnect(disconnect_type)

    def disconnect_with_message(self, disconnect_type, message=None, timeout=3.0):
        if self._client is not None:
            self._client.send_server_message(message or 'Goodbye')
        self._disconnecting_later = reactor.callLater(timeout, self.disconnect, disconnect_type)

    def send(self, channel, data, reliable, no_allocate=False):
        return self.transport.send(channel, data, reliable, no_allocate)
