from cube2common.constants import armor_types
from spyd.game.gamemode.bases.mode_base import make_multidispatch, extract_public_methods
from spyd.game.gamemode.bases.tactics_base import TacticsBase
from spyd.game.gamemode.bases.teamplay_base import TeamplayBase
from spyd.registry_manager import register


# @register('gamemode')
class TacticsTeam(TacticsBase, TeamplayBase):
    isbasemode = True
    clientmodename = 'tacteam'
    clientmodenum = 8
    timed = True
    timeout = 600
    hasitems = False
    hasflags = False
    hasteams = True
    spawnarmour = 100
    spawnarmourtype = armor_types.A_GREEN
    spawnhealth = 100
    spawndelay = 0
    hasbases = False

    def __init__(self, room, map_meta_data):
        self.teamBase = TeamplayBase(room, map_meta_data)
        self.tacticsBase = TacticsBase(room, map_meta_data)

        dispatch = make_multidispatch(self.teamBase, self.tacticsBase)
        methods = extract_public_methods(self.teamBase).union(extract_public_methods(self.tacticsBase))
        for meth in methods:
            setattr(self, meth, dispatch(meth))
