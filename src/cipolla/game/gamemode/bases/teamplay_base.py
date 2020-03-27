from random import choice as random_choice

from cipolla.game.map.team import Team
from cipolla.protocol import swh
from cipolla.game.gamemode.bases.mode_base import ModeBase
from cipolla.utils.tuple_utils import fst, snd
from cube2common.constants import client_states

base_teams = {'good': Team(0, 'good'), 'evil': Team(1, 'evil')}

class TeamplayBase(ModeBase):
    def __init__(self, room, map_meta_data, teams=None):
        super().__init__(room, map_meta_data)
        if teams is None:
            self.teams = {}
            for team_name in base_teams:
                self._get_team(team_name)
        else:
            assert isinstance(teams, dict)
            self.teams = teams

    def _get_team(self, name):
        if not name in self.teams:
            self.teams[name] = Team(len(self.teams), name)
        return self.teams[name]

    def initialize_player(self, cds, player):
        if player.state.state == client_states.CS_SPECTATOR: return
        possible_teams = self.room.teams_size
        if len(possible_teams) > 0:
            smallest_team = min(possible_teams.values(), key=fst)
            player._team = snd(smallest_team).name
        else:
            player._team = random_choice(tuple(base_teams.values())).name
        super().initialize_player(cds, player)
        swh.put_setteam(cds, player, -1)
        swh.put_teaminfo(cds, self.teams.values())

    def on_player_connected(self, player):
        super().on_player_connected(player)

    def on_player_disconnected(self, player):
        super().on_player_disconnected(player)
        if player.teamname:
            player.team = ""

    def on_player_try_set_team(self, player, target, old_team_name, new_team_name):
        if new_team_name == "": return
        super().on_player_try_set_team(player, target, old_team_name, new_team_name)
        team = self._get_team(new_team_name)
        if team is None: return
        if team.name is target.teamname: return

        self._teamswitch_suicide(target)
        with self.room.broadcastbuffer(1, True) as cds:
            if player is None or player.state.is_spectator:
                reason = -1
            elif player == target:
                reason = 0
            else:
                reason = 1
            target.teamname = team.name
            swh.put_setteam(cds, target, reason)

    def on_player_death(self, player, killer):
        super().on_player_death(player, killer)
        if player is killer:
            self.teams[player.teamname].frags -= 1

    def _teamswitch_suicide(self, player):
        super()._teamswitch_suicide(player)
        if not player.state.is_alive: return
        player.state.suicide()
        with self.room.broadcastbuffer(1, True) as cds:
            swh.put_died(cds, player, player, self.teams)
        self.on_player_death(player, player)
