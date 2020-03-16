from spyd.registry_manager import register
from spyd.game.client.exceptions import GenericError

ADMIN_PASS = "test"


class WrongCredentials(GenericError):
    pass


@register('room_client_event_handler')
class GiveMasterHandler(object):
    event_type = 'give_master'

    @staticmethod
    def handle(room, client, client_target):
        room._client_change_privilege(client, client_target, 1)
