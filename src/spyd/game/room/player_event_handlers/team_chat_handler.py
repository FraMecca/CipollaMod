from spyd.protocol import swh
from spyd.registry_manager import register


@register('room_player_event_handler')
class TeamChatHandler(object):
    event_type = 'team_chat'

    @staticmethod
    def handle(room, player, text):
        if player.isai: return

        if player.state.is_spectator:
            clients = [c for c in room.clients if c.get_player().state.is_spectator]
        else:
            clients = [c for c in room.clients if c.get_player().team == player.team]

        with room.broadcastbuffer(1, True, [player.client], clients) as cds:
            swh.put_sayteam(cds, player.client, text)

        room.event_subscription_fulfiller.publish('spyd.game.player.chat', {'player': player.uuid, 'room': room.name, 'text': text, 'scope': 'team'})
