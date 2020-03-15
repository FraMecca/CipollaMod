from cube2common.constants import armor_types
from spyd.game.gamemode.bases.ctf_base import CtfBase
from spyd.game.gamemode.bases.tactics_base import TacticsBase
from spyd.game.gamemode.bases.mode_base import make_multidispatch, extract_public_methods
from spyd.registry_manager import register

# @register('gamemode')
class TacticsCtf(object):
    isbasemode = False
    clientmodename = 'tacctf'
    clientmodenum = 17
    timed = True
    timeout = 600
    hasitems = False
    hasflags = True
    hasteams = True
    spawnarmour = 100
    spawnarmourtype = armor_types.A_GREEN
    spawnhealth = 100
    spawndelay = 5
    hasbases = False

    def make_multidispatch(a, am, b, bm):
        # a: class, am: methods of class
        class Multi:
            def __new__(cls, funct):
                if funct in am and funct not in bm:
                    return a.__getattribute__(funct)
                elif funct in bm and funct not in am:
                    return b.__getattribute__(funct)
                else:
                    # present in both
                    def call(*args, **kwargs):
                        rb = b.__getattribute__(funct)(*args, **kwargs)
                        ra = a.__getattribute__(funct)(*args, **kwargs)
                        return (ra, rb)
                    return call
        return Multi
                
    def __init__(self, room, map_meta_data):
        self.ctfBase = CtfBase(room, map_meta_data)
        self.tacticsBase = TacticsBase(room, map_meta_data)

        dispatch = make_multidispatch(self.ctfBase, self.tacticsBase)
        methods = extract_public_methods(self.ctfBase).union(extract_public_methods(self.tacticsBase))
        for meth in methods:
            setattr(self, meth, dispatch(meth))
