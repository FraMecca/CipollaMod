from cube2common.constants import armor_types, weapon_types
from spyd.game.gamemode.bases.item_base import ItemBase
from spyd.game.gamemode.bases.teamplay_base import TeamplayBase
from spyd.registry_manager import register


# @register('gamemode')
class Teamplay(ItemBase, TeamplayBase):
    isbasemode = True
    clientmodename = 'teamplay'
    clientmodenum = 2
    timed = True
    timeout = 600
    hasitems = True
    hasflags = False
    hasteams = True
    hasbases = False
    spawnarmour = 25
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

    def __init__(self, room, map_meta_data):
        self.teamBase = TeamplayBase(room, map_meta_data)
        self.itemBase = ItemBase(room, map_meta_data)

        dispatch = make_multidispatch(self.teamBase, self.itemBase)
        methods = extract_public_methods(self.teamBase).union(extract_public_methods(self.itemBase))
        for meth in methods:
            setattr(self, meth, dispatch(meth))
