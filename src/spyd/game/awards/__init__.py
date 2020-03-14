from cube2common.colors import colors
from spyd.game.server_message_formatter import smf, info, wrapper_function
from spyd.registry_manager import RegistryManager
from spyd.utils.import_all import import_all


import_all(__file__, 'spyd.game.awards', ['__init__'])


def format_name(client):
    return smf.format("{name#client}", client=client)

def format_names(clients):
    names = list(map(format_name, clients))

    if len(names) == 1:
        return names[0]

    if len(names) > 2:
        names = [', '.join(names[:-1]), names[-1]]

    return ', and '.join(names)

def format_award(award, names, value):
    award_text = award.award_text
    names = format_names(names)
    value = award.format_stat(value)
    return smf.format("{award_text}: {winners} ({value#value})", award_text=award_text, winners=names, value=value)

class AwardInstance(object):
    def __init__(self, award, clients_iter):
        self.award = award
        self.clients_iter = clients_iter

        self.eligible_clients = [c for c in clients_iter() if award.is_client_eligible(c)]

        self.left_weight = award.left_weight

    def get_winners(self, winning_stat_value):
        winners = [c for c in self.clients_iter() if self.award.get_stat_from_client(c) == winning_stat_value]
        return winners

    def get_winning_stat_value(self):
        one_winner = max(self.clients_iter(), key=lambda c: self.award.get_stat_from_client(c))
        winning_stat_value = self.award.get_stat_from_client(one_winner)
        return winning_stat_value

    @property
    def has_winner(self):
        return len(self.eligible_clients) > 0

    def get_formatted(self):
        winning_stat_value = self.get_winning_stat_value()
        winners = self.get_winners(winning_stat_value)
        return format_award(self.award, winners, winning_stat_value)

awards_wrapper = wrapper_function('info', 'Awards')

def display_awards(room):
    awards = [a.registered_object for a in RegistryManager.get_registrations('award')]

    mode_name = room.gamemode.clientmodename

    awards = [a for a in awards if a.is_valid_mode(mode_name)]

    awards = [AwardInstance(a, room._players.to_iterator) for a in awards]

    awards = [a for a in awards if a.has_winner]

    if awards:
        awards = sorted(awards, key=lambda a: a.left_weight, reverse=True)

        awards = [a.get_formatted() for a in awards]

        award_string = " | ".join(awards)
        room.server_message(awards_wrapper("{awards}", awards=award_string))
