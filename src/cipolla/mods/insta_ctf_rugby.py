from cube2common.constants import armor_types, weapon_types
from cipolla.game.gamemode.gamemodes import gamemodes
from cipolla.game.gamemode.insta_ctf import InstaCtf
from cipolla.game.server_message_formatter import red, yellow
from cipolla.protocol import swh
from cipolla.mods.abstract_mod import AbstractMod

class InstaCtfRugbyMod(AbstractMod):
    name = "rugby"
    canLoad = True

    def can_attach(self, room):
        return isinstance(room.gamemode, InstaCtf)

    def setup(self, room):
        for name, mode in gamemodes.items():
            print(name, mode, name == 'instactf')
            if name == 'instactf':
                gamemodes['instactf'] = InstaCtfRugby
                return
        # TODO log error
        assert False, "No instactf???"

    def teardown(self, room):
        for name, mode in gamemodes.items():
            if name == 'instactf':
                gamemodes['instactf'] = InstaCtf
        # TODO log error
        assert False, "No instactfrugby???"


class InstaCtfRugby(InstaCtf):
    def on_player_hit(self, player, gun, target_cn, lifesequence, distance, rays, dx, dy, dz):
        target = self.room.get_player(target_cn)
        if target is None: return

        ownsflag, flag = self.owns_flag(player)
        print('-----------------')
        print(ownsflag , target.team is player.team)
        print('-----------------')
        if ownsflag and target.team is player.team:
            flag.owner = target
            with self.room.broadcastbuffer(1, True) as cds:
                swh.put_takeflag(cds, target, flag)
            
            self.room.server_message(f'{yellow(player.name)} passed the flag to ' +
                        f'{yellow(target.name)}: {red(float(distance)/100)} ogro feet')
        else:
            # self.original_method(player, gun, target_cn, lifesequence, distance, rays, dx, dy, dz)
            super().on_player_hit(player, gun, target_cn, lifesequence, distance, rays, dx, dy, dz)
    
