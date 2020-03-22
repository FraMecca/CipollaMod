from cube2common.constants import armor_types, weapon_types
from cipolla.game.gamemode.bases.ctf_base import CtfBase

class Ctf(CtfBase):
    isbasemode = True
    clientmodename = 'ctf'
    clientmodenum = 11
    timed = True
    timeout = 600
    hasitems = True
    hasflags = True
    hasteams = True
    spawnarmour = 50
    spawnarmourtype = armor_types.A_BLUE
    spawnhealth = 100
    spawndelay = 5
    hasbases = False

    @property
    def spawnammo(self):
        ammo = [0] * weapon_types.NUMGUNS
        ammo[weapon_types.GUN_FIST] = 1
        ammo[weapon_types.GUN_GL] = 1
        ammo[weapon_types.GUN_PISTOL] = 40
        return ammo

    spawngunselect = weapon_types.GUN_PISTOL
