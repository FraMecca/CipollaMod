from glob import glob
from inspect import getmembers, isclass
from importlib import import_module, reload
import importlib.util
from pathlib import Path

from spyd.utils.tuple_utils import snd
from spyd.mods.abstract_mod import AbstractMod


class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class ModsManager(metaclass=Singleton):
    def __init__(self):

        self.mods = {}
        self.module_map = {}

        self.mods_folder = Path(__file__).parent
        for pyfile in glob(str(self.mods_folder)+'/*.py'):
            module = self.load_pythonfile(pyfile)

            classes = self.load_mod(getmembers(module))
            for cls_name in classes:
                self.module_map[cls_name] = module

    def load_mod(self, pymodule):
            filemods = dict(map(lambda cls: (cls.name, cls),
                                filter(lambda cls: cls.canLoad,
                                       filter(lambda cls: isclass(cls) and issubclass(cls, AbstractMod),
                                              map(snd, pymodule)))))
            self.mods.update(filemods)
            return filemods.keys()

    def load_pythonfile(self, pyfile):
        '''Return module object from python file'''
        module_name = ''.join(set(pyfile[:-3].split('/')) - set(self.mods_folder.parts))
        spec = importlib.util.spec_from_file_location(module_name, pyfile)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def reload_python_file(self, mod_name):
        pymodule = self.module_map[mod_name]
        newmodule = self.load_pythonfile(pymodule.__file__)
        self.load_mod(getmembers(newmodule))

    def enable(self, mod_name, room):
        modCls = self.mods[mod_name] # is a class, must be instantiated
        mod = modCls()
        if mod.can_attach(room):
            mod.setup(room)
            room.add_mod(mod)
            return True
        else:
            return False

    def disable(self, mod_name, room):
        if room.is_mod_active(mod_name):
            mod = room.get_mod(mod_name)
            mod.teardown(room)
            room.del_mod(mod)
    
    def reload(self, mod_name, room):
        if room.is_mod_active(mod_name):
            mod = room.get_mod(mod_name)
            mod.teardown(room)

        self.reload_python_file(mod_name)
        return self.enable(mod_name, room)

    def list_mods(self):
        return tuple(self.mods.keys())

from spyd.utils.tracing import trace_class
trace_class(ModsManager)
