from cube2common.constants import armor_types, weapon_types
from spyd.game.gamemode.bases.item_base import ItemBase
from spyd.registry_manager import register


# @register('gamemode')
class FreeForAll(ItemBase):
    isbasemode = True
    clientmodename = 'ffa'
    clientmodenum = 0
    timed = True
    timeout = 600
    hasitems = True
    hasflags = False
    hasteams = False
    spawnarmour = 25
    spawnarmourtype = armor_types.A_BLUE
    spawnhealth = 100
    spawndelay = 0
    hasbases = False

    @property
    def spawnammo(self):
        ammo = [0] * weapon_types.NUMGUNS
        ammo[weapon_types.GUN_FIST] = 1
        ammo[weapon_types.GUN_GL] = 1
        ammo[weapon_types.GUN_PISTOL] = 40
        return ammo

    spawngunselect = weapon_types.GUN_PISTOL
