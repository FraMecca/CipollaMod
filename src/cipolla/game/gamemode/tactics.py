from cube2common.constants import armor_types
from cipolla.game.gamemode.bases.tactics_base import TacticsBase

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
