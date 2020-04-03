from cipolla.game.client.client import Client
class RoomEntryContext(object):
    def __init__(self, client: Client) -> None:
        self.client = client
