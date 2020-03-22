from cipolla.game.gamemode.coop import Coop
from cipolla.game.gamemode.teamplay import Teamplay
from cipolla.game.gamemode.free_for_all import FreeForAll
from cipolla.game.gamemode.ctf import Ctf
from cipolla.game.gamemode.effic import Effic
from cipolla.game.gamemode.effic_ctf import EfficCtf
from cipolla.game.gamemode.effic_team import EfficTeam
from cipolla.game.gamemode.insta import Insta
from cipolla.game.gamemode.insta_ctf import InstaCtf
from cipolla.game.gamemode.insta_team import InstaTeam
from cipolla.game.gamemode.tactics import Tactics
from cipolla.game.gamemode.tactics_ctf import TacticsCtf
from cipolla.game.gamemode.tactics_team import TacticsTeam


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
