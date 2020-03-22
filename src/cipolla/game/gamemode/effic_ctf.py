from cube2common.constants import armor_types, weapon_types
from cipolla.game.gamemode.bases.ctf_base import CtfBase

class EfficCtf(CtfBase):
    isbasemode = True
    clientmodename = 'efficctf'
    clientmodenum = 17
    timed = True
    timeout = 600
    hasitems = False
    hasflags = True
    hasteams = True
    spawnarmour = 100
    spawnarmourtype = armor_types.A_GREEN
    spawnhealth = 100
    spawndelay = 5
    hasbases = False

    @property
    def spawnammo(self):
        ammo = [0] * weapon_types.NUMGUNS
        ammo[weapon_types.GUN_CG] = 20
        ammo[weapon_types.GUN_SG] = 20
        ammo[weapon_types.GUN_GL] = 20
        ammo[weapon_types.GUN_RL] = 10
        ammo[weapon_types.GUN_RIFLE] = 10
        return ammo

    spawngunselect = weapon_types.GUN_CG
