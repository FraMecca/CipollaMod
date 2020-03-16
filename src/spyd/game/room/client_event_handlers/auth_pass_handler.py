from spyd.registry_manager import register
from spyd.game.client.exceptions import GenericError

ADMIN_PASS = "test"


class WrongCredentials(GenericError):
    pass


@register('room_client_event_handler')
class AuthPassHandler(object):
    event_type = 'auth_pass'

    @staticmethod
    def handle(room, client, message):
        assert len(message) == 1

        passw = message[0]

        if passw == ADMIN_PASS:
            room._client_change_privilege(client, client, 3)
        else:
            raise WrongCredentials("Eheh, try again :)")

