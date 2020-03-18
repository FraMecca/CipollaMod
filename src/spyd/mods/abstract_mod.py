class AbstractMod(object):
    canLoad = False # specify that mod can be loaded at runtime
    @property
    def name(self):
        raise NotImplementedError

    def setup(self, room):
        self.old_methods = []
        pass

    def teardown(self, room):
        for obj, method_name, old_method in self.old_methods:
            setattr(obj, method_name, old_method)

    def can_attach(self, room):
        '''
        Checks if mod can be used in current room.
        Mod developers need to check that attributes of the room
        (gamemode, players, etc...) are compatible with this mode.
        E.g.: Rugby mode checks that isinstance(room.gamemode, Ctf)
        '''
        pass
