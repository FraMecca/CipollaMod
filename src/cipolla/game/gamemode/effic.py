from cube2common.constants import weapon_types, armor_types
from cipolla.game.gamemode.bases.mode_base import ModeBase

class Effic(ModeBase):
    isbasemode = True
    clientmodename = 'effic'
    clientmodenum = 5
    timed = True
    timeout = 600
    hasitems = False
    hasflags = False
    hasteams = False
    spawnarmour = 100
    spawnarmourtype = armor_types.A_GREEN
    spawnhealth = 100
    spawndelay = 0
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
