from cube2common.constants import armor_types, weapon_types
from sauerpyd.gamemode.bases.fighting_base import FightingBase
from sauerpyd.gamemode.bases.item_base import ItemBase
from sauerpyd.gamemode.bases.mode_base import ModeBase
from sauerpyd.gamemode.bases.spawning_base import SpawningBase
from sauerpyd.registry_manager import register


@register('gamemode')
class Coop(ModeBase, ItemBase, FightingBase, SpawningBase):
    isbasemode = True
    clientmodename = 'coop'
    clientmodenum = 1
    timed = False
    timeout = None
    hasitems = True
    hasflags = True
    hasteams = True
    hasbases = False
    spawnarmour = 50
    spawnarmourtype = armor_types.A_BLUE
    spawnhealth = 100
    spawndelay = 0

    @property
    def spawnammo(self):
        ammo = [0] * weapon_types.NUMGUNS
        ammo[weapon_types.GUN_FIST] = 1
        ammo[weapon_types.GUN_GL] = 1
        ammo[weapon_types.GUN_PISTOL] = 40
        return ammo

    spawngunselect = weapon_types.GUN_PISTOL
