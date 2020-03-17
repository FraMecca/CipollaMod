from spyd.game.gamemode.coop import Coop
from spyd.game.gamemode.teamplay import Teamplay
from spyd.game.gamemode.free_for_all import FreeForAll
from spyd.game.gamemode.ctf import Ctf
from spyd.game.gamemode.effic import Effic
from spyd.game.gamemode.effic_ctf import EfficCtf
from spyd.game.gamemode.effic_team import EfficTeam
from spyd.game.gamemode.insta import Insta
from spyd.game.gamemode.insta_ctf import InstaCtf
from spyd.game.gamemode.insta_team import InstaTeam
from spyd.game.gamemode.tactics import Tactics
from spyd.game.gamemode.tactics_ctf import TacticsCtf
from spyd.game.gamemode.tactics_team import TacticsTeam


mode_nums = {}
gamemodes = {}

gamemode_objects = [Coop, Teamplay, FreeForAll, Ctf,
                    Effic, EfficCtf, EfficTeam,
                    Insta, InstaCtf, InstaTeam,
                    Tactics, TacticsCtf, TacticsTeam]

for gamemode_object in gamemode_objects:
    if gamemode_object.isbasemode:
        mode_nums[gamemode_object.clientmodenum] = gamemode_object.clientmodename

for gamemode_object in gamemode_objects:
    gamemodes[gamemode_object.clientmodename] = gamemode_object

def get_mode_name_from_num(mode_num):
    return mode_nums.get(mode_num, None)
