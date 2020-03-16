from spyd.registry_manager import register


@register('client_message_handler')
class AuthPassHandler(object):
    message_type = 'authpass'

    @staticmethod
    def handle(client, room, message):
        print(message)
        room.handle_client_event('auth_pass', client, message)
