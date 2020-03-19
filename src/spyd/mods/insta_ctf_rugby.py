from cube2common.constants import armor_types, weapon_types
from spyd.game.gamemode.insta_ctf import InstaCtf
from spyd.game.server_message_formatter import red, yellow
from spyd.protocol import swh
from spyd.mods.abstract_mod import AbstractMod


class InstaCtfRugby(AbstractMod):
    name = "rugby"
    canLoad = True

    def can_attach(self, room):
        return isinstance(room.gamemode, InstaCtf)

    def setup(self, room):
        mode = room.gamemode
        method_name = 'on_player_hit'

        self.original_method = getattr(mode, method_name)
        self.room = room
        self.owns_flag = getattr(mode, 'owns_flag')

        self.old_methods = [(mode, method_name, self.original_method)]
        setattr(mode, 'on_player_hit', self.on_player_hit)

    def on_player_hit(self, player, gun, target_cn, lifesequence, distance, rays, dx, dy, dz):
        target = self.room.get_player(target_cn)
        if target is None: return

        ownsflag, flag = self.owns_flag(player)
        if ownsflag and target.team is player.team:
            flag.owner = target
            with self.room.broadcastbuffer(1, True) as cds:
                swh.put_takeflag(cds, target, flag)
            
            self.room.server_message(f'{yellow(player.name)} passed the flag to ' +
                        f'{yellow(target.name)}: {red(float(distance)/100)} ogro feet')
        else:
            self.original_method(player, gun, target_cn, lifesequence, distance, rays, dx, dy, dz)
