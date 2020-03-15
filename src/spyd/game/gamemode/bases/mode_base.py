from cube2common.constants import DMF, weapon_types, guns, EXP_DISTSCALE, EXP_SELFDAMDIV, DNF, client_states, \
    DEATHMILLIS
from cube2common.vec import vec
from spyd.game.timing.expiry import Expiry
from spyd.protocol import swh

# def multidispatched(func):
#     base_func = func
#     func_name = func.__name__
#     def multidispatcher(self, *args, **kwargs):
#         for base in self.__class__.__bases__:
#             if base != ModeBase and hasattr(base, func_name):
#                 func = getattr(base, func_name)
#                 func(self, *args, **kwargs)
#         base_func(self, *args, **kwargs)
#     return multidispatcher
def extract_public_methods(obj):
    return set(filter(lambda t: t[0][0] != '_', dir(obj)))

def make_multidispatch(a,  b):
    # a: class, am: methods of class
    class Multi:
        def __new__(cls, funct):
            am = extract_public_methods(a)
            bm = extract_public_methods(b)
            if funct in am and funct not in bm:
                return a.__getattribute__(funct)
            elif funct in bm and funct not in am:
                return b.__getattribute__(funct)
            else:
                # present in both
                def call(*args, **kwargs):
                    rb = b.__getattribute__(funct)(*args, **kwargs)
                    ra = a.__getattribute__(funct)(*args, **kwargs)
                    return (ra, rb)
                return call
    return Multi


class ModeBase(object):
    # TODO: read about __slots__ and use it
    def __init__(self, room, map_meta_data):
        self.initialized = False
        self.room = room
        self._broadcaster = room._broadcaster
        self._game_clock = room._game_clock
    
    
    def initialize(self):
        self.initialized = True
    
    
    def on_player_connected(self, player):
        pass
    
    
    def initialize_player(self, cds, player):
        pass
    
    
    def on_player_disconnected(self, player):
        pass
    
    
    def on_player_shoot(self, player, shot_id, gun, from_pos, to_pos, hits):
        print('shoot')
        if self.room.is_paused: return
        if self.room.is_intermission: return

        pfrom = from_pos.copy().div(DMF)
        pto = to_pos.copy().div(DMF)

        if not player.state.check_alive(threshold=DEATHMILLIS): return
        if gun < weapon_types.GUN_FIST or gun > weapon_types.GUN_PISTOL: return
        if player.state.ammo[gun] <= 0: return
        if guns[gun].range and (pfrom.dist(pto) > guns[gun].range + 1): return

        if gun != weapon_types.GUN_FIST:
            player.state.ammo[gun] -= 1

        player.state.shotwait = Expiry(self._game_clock, float(guns[gun].attackdelay) / 1000.0)

        self._broadcaster.shotfx(player, gun, shot_id, from_pos, to_pos)

        player.state.damage_spent += guns[gun].damage * player.state.quad_multiplier * guns[gun].rays

        if gun == weapon_types.GUN_RL:
            player.state.rockets[shot_id] = gun
        elif gun == weapon_types.GUN_GL:
            player.state.grenades[shot_id] = gun
        else:
            total_rays = 0
            max_rays = guns[gun].rays
            for hit in hits:
                total_rays += hit['rays']
                if total_rays > max_rays: return
                self.on_player_hit(player, gun, **hit)


    def on_player_damaged(self, target, player, damage, gun, dx, dy, dz):
        v = vec(dx, dy, dz).div(DMF).rescale(DNF)
        target.state.receive_damage(damage)

        with self.room.broadcastbuffer(1, True) as cds:
            swh.put_damage(cds, target, player, damage)

            if target == player:
                pass
            elif not v.iszero():
                if target.state.health <= 0:
                    swh.put_hitpush(cds, target, gun, damage, v)
                else:
                    with target.sendbuffer(1, True) as cds:
                        swh.put_hitpush(cds, target, gun, damage, v)

            if target.state.health < 1:
                target.state.state = client_states.CS_DEAD

                target.state.deaths += 1
                if player == target:
                    player.state.suicides += 1
                if self.hasteams and player.team == target.team:
                    player.state.teamkills += 1
                if player == target or self.hasteams and player.team == target.team:
                    mod = -1
                else:
                    mod = 1

                player.state.frags += mod
                if self.hasteams:
                    player.team.frags += mod

                swh.put_died(cds, target, player)
                self.on_player_death(target, player)

                
    def on_player_hit(self, player, gun, target_cn, lifesequence, distance, rays, dx, dy, dz):
        target = self.room.get_player(target_cn)
        if target is None: return

        damage = guns[gun].damage
        if not gun in [weapon_types.GUN_RL, weapon_types.GUN_GL]:
            damage *= rays
        damage *= player.state.quad_multiplier
        if gun in (weapon_types.GUN_RL, weapon_types.GUN_GL):
            damage *= (1.0 - ((distance / DMF) / EXP_DISTSCALE) / guns[gun].exprad)
            if target == player:
                damage /= EXP_SELFDAMDIV

        player.state.damage_dealt += int(damage)
        self.on_player_damaged(target, player, damage, gun, dx, dy, dz)
    
    
    def on_player_explode(self, player, cmillis, gun, explode_id, hits):
        if gun == weapon_types.GUN_RL:
            if not explode_id in list(player.state.rockets.keys()): return
            del player.state.rockets[explode_id]
        elif gun == weapon_types.GUN_GL:
            if not explode_id in list(player.state.grenades.keys()): return
            del player.state.grenades[explode_id]

        self._broadcaster.explodefx(player, gun, explode_id)

        for hit in hits:
            self.on_player_hit(player, gun, **hit)


    def on_player_death(self, player, killer):
        player.state.spawnwait = Expiry(self.room._game_clock, self.spawndelay)
        player.state.died()
    
    
    def on_player_taunt(self, player):
        swh.put_taunt(player.state.messages)


    def _spectate_suicide(self, cds, player):
        if not player.state.is_alive: return
        self.on_player_death(player, player)


    def on_player_spectate(self, player):
        with self.room.broadcastbuffer(1, True) as cds:
            self._spectate_suicide(cds, player)
            player.state.is_spectator = True
            swh.put_spectator(cds, player)

        if player.client.cn == player.pn:
            self.room.ready_up_controller.on_client_spectated(player.client)


    def on_player_unspectate(self, player):
        with self.room.broadcastbuffer(1, True) as cds:
            player.state.is_spectator = False
            self.initialize_player(cds, player)
            self.on_player_connected(player)
            swh.put_spectator(cds, player)


    def initialize_player(self, cds, player):
        pass


    def on_player_disconnected(self, player):
        pass


    def on_player_try_set_team(self, player, target, old_team_name, new_team_name):
        pass


    def on_player_take_flag(self, player, flag_index, version):
        pass


    def _teamswitch_suicide(self, player):
        pass

    
    def on_player_try_drop_flag(self, player):
        pass


    def on_player_flag_list(self, player, flag_list):
        pass

    def _get_team(self, name):
        pass


    def on_player_request_spawn(self, player):
        if player.state.can_spawn:
            player.state.respawn()
            self.spawn_loadout(player)
            with player.sendbuffer(1, True) as cds:
                swh.put_spawnstate(cds, player)


    def spawn_loadout(self, player):
        player.state.health = self.spawnhealth
        player.state.armour = self.spawnarmour
        player.state.armourtype = self.spawnarmourtype
        player.state.gunselect = self.spawngunselect
        player.state.ammo = self.spawnammo

from spyd.utils.tracing import trace_class
trace_class(ModeBase)
