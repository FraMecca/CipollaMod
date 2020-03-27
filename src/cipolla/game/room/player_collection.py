class PlayerCollection(object):
    def __init__(self):
        #pn: player
        self._players = {}

    def add(self, player):
        self._players[player.pn] = player

    def remove(self, player):
        del self._players[player.pn]

    @property
    def count(self):
        return len(self._players)

    def to_list(self):
        return list(self._players.values())

    def to_iterator(self):
        return iter(self._players.values())

    def by_team(self, allteams):
        from itertools import groupby
        from cipolla.utils.groupby_utils import unroll_group

        team_of = lambda p: allteams[p.teamname]

        return dict(map(unroll_group,
                        groupby(sorted(filter(lambda p: p.teamname != '',
                                              self.to_iterator()),
                                       key=lambda p: p.teamname),
                                key=team_of)))

    def by_pn(self, pn):
        return self._players.get(pn, None)

    def is_name_duplicate(self, name):
        name_count = 0
        for player in self._players.values():
            if player.name == name:
                name_count += 1
                if name_count > 1:
                    return True
        return False
