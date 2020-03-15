from cube2common.constants import game_entity_types, RESETFLAGTIME, DMF
from spyd.game.timing.expiry import Expiry
from cube2common.vec import vec
from spyd.game.map.flag import Flag
from spyd.game.map.team import Team
from spyd.protocol import swh
from spyd.game.gamemode.bases.teamplay_base import TeamplayBase, base_teams


class CtfBase(TeamplayBase):
    def __init__(self, room, map_meta_data):
        
        self.teams = base_teams
        super().__init__(room, map_meta_data, self.teams)

        self.room = room
        self._game_clock = room._game_clock
        
        
        self.flags = None

        self.scores = [0, 0]
        
        if map_meta_data is not None:
            flag_list = []
            for ent in map_meta_data.get('ents', []):
                if ent['type'] == game_entity_types.FLAG:
                    flag_list.append({'x': int(ent['x']*DMF), 'y': int(ent['y']*DMF), 'z': int(ent['z']*DMF), 'team': ent['attrs'][1]})
    
            self._load_flag_list(flag_list)

    @property
    def got_flags(self):
        return self.flags is not None
    
    def on_player_connected(self, player):
        super().on_player_connected(player)
        if not player.isai:
            with player.sendbuffer(1, True) as cds:
                swh.put_initflags(cds, self.scores, self.flags or ())
    
    def on_player_disconnected(self, player):
        super().on_player_disconnected(player)
        self.on_player_try_drop_flag(player)
        if player.team is not None:
            player.team = None
        
    def _get_team(self, name):
        return self.teams.get(name, None)
        
    def _score_flag(self, player, goal_flag, relay_flag):
        self.scores[goal_flag.id] += 1
        player.team.score += 1
        
        relay_flag.version += 1
        relay_flag.reset()
        
        player.state.flags += 1
        
        with self.room.broadcastbuffer(1, True) as cds:
            swh.put_scoreflag(cds, player, relay_flag, goal_flag)
            
        if player.team.score >= 10:
            self.room.end_match()
            
    def _reset_flag(self, flag):
        if flag.owner is not None: return
        flag.version += 1
        flag.reset()
        with self.room.broadcastbuffer(1, True) as cds:
            swh.put_resetflag(cds, flag, flag.team)
            
    def _return_flag(self, player, flag):
        flag.version += 1
        flag.reset()
        
        player.state.flag_returns += 1
        
        with self.room.broadcastbuffer(1, True) as cds:
            swh.put_returnflag(cds, player, flag)
            
    def get_flag(self, flag_index):
        for flag in self.flags or ():
            if flag.id == flag_index:
                return flag
    
    def on_player_take_flag(self, player, flag_index, version):
        super().on_player_take_flag(player, flag_index, version)
        if player.state.is_spectator: return
        if not player.state.is_alive: return
        
        if self.flags is None:
            return
        
        if flag_index < 0 or flag_index >= len(self.flags):
            return
            
        flag = self.get_flag(flag_index)
        
        if flag.owner is not None:
            return
            
        if flag.version != version:
            return

        if flag.team is player.team:
            # if the flag was dropped, then return it
            if flag.dropped:
                self._return_flag(player, flag)
                return
            # check if you are a flag carrier if so score
            for other_flag in self.flags or ():
                if other_flag != flag and other_flag.owner == player:
                    self._score_flag(player, flag, other_flag)
                    break
            return
            
        # Implement 1 drop and pickup rule
        if flag.dropper is player and flag.drop_count >= 2:
            return
        
        flag.version += 1
        flag.owner = player
        flag.drop_time = None
            
        with self.room.broadcastbuffer(1, True) as cds:
            swh.put_takeflag(cds, player, flag)
        
        return True
    
    def on_player_try_drop_flag(self, player):
        super().on_player_try_drop_flag(player)
        for flag in self.flags or ():
            if flag.owner is player:
                flag.drop(player.state.pos.copy(), RESETFLAGTIME / 1000.0)
                flag.return_scheduled_callback_wrapper.add_timeup_callback(self._reset_flag, flag)
                with self.room.broadcastbuffer(1, True) as cds:
                    swh.put_dropflag(cds, player, flag)
        return True

    def owns_flag(self, player):
        for flag in self.flags or ():
            if flag.owner is player:
                return True, flag
        return False, None
        
    def on_player_death(self, player, killer):
        hasflag, flag = self.owns_flag(killer)
        print(hasflag)
        # if  hasflag and player is not killer and player._team is killer._team:
        #     print('rugby')
        #     self.on_player_try_drop_flag(killer)
        #     flag.owner = player
        #     with self.room.broadcastbuffer(1, True) as cds:
        #         swh.put_takeflag(cds, player, flag)
        #     # import IPython; IPython.embed()
        # else:
        if True:
            self.on_player_try_drop_flag(player)
            super().on_player_death(player, killer)
        print('done')
        
    def _teamswitch_suicide(self, player):
        super()._teamswitch_suicide(player)
        if not player.state.is_alive: return
        player.state.suicide()
        with self.room.broadcastbuffer(1, True) as cds:
            swh.put_died(cds, player, player)
        self.on_player_death(player, player)

    def on_player_flag_list(self, player, flag_list):
        super().on_player_flag_list(player, flag_list)
        if not self.got_flags:
            self._load_flag_list(flag_list)
    
    def _load_flag_list(self, flag_list):
        fid = 0
        self.flags = []
        for flag_dict in flag_list:
            team = list(self.teams.values())[flag_dict['team']-1]
            spawn_loc = vec(flag_dict['x'], flag_dict['y'], flag_dict['z'])
            flag = Flag(game_clock=self.room._game_clock, fid=fid, spawn_loc=spawn_loc, team=team)
            fid += 1
            self.flags.append(flag)
    
    def on_player_try_set_team(self, player, target, old_team_name, new_team_name):
        super().on_player_try_set_team(player, target, old_team_name, new_team_name)
        team = self._get_team(new_team_name)
        if team is None: return
        
        if team is target.team: return
        
        self._teamswitch_suicide(target)
        with self.room.broadcastbuffer(1, True) as cds:
            if player is None or target.state.is_spectator:
                reason = -1
            elif player == target:
                reason = 0
            else:
                reason = 1
            target.team = team
            swh.put_setteam(cds, target, reason)

from spyd.utils.tracing import trace_class
trace_class(CtfBase)
