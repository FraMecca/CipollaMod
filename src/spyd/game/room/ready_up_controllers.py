import time

from twisted.internet import reactor

from spyd.game.server_message_formatter import smf
from spyd.utils.listjoin import listjoin


class NoOpReadyUpController(object):
    def __init__(self, room):
        room.resume()

    def on_crc(self, player, crc):
        pass

    def on_client_spectated(self, client):
        pass

    def on_client_leave(self, client):
        pass

    def on_request_spawn(self, client):
        pass
