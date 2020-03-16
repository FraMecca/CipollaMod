from spyd.registry_manager import register
from spyd.game.client.exceptions import GenericError
from spyd.config_loader import config_loader


class WrongCredentials(GenericError):
    pass


@register('room_client_event_handler')
class AuthPassHandler(object):
    event_type = 'auth_pass'

    @staticmethod
    def handle(room, client, message):
        passw = message[0]
        admin_pass = config_loader('config.json')['room_bindings'][room._name.value]['adminpass']

        if passw == admin_pass:
            room._client_change_privilege(client, client, 3)
        else:
            raise WrongCredentials("Eheh, try again :)")

