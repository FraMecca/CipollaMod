from cube2common.constants import armor_types
from spyd.game.gamemode.bases.tactics_base import TacticsBase
from spyd.registry_manager import register


# @register('gamemode')
class Tactics(TacticsBase):
    isbasemode = True
    clientmodename = 'tactics'
    clientmodenum = 7
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
