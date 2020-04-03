from collections import namedtuple
import os.path

from cipolla.utils.singleton import Singleton

from typing import Dict, List, Union

class ConfigurationError(Exception): pass
class ConfigurationFileError(Exception): pass

from cipolla.utils.configuration_utils import *

from typing import Union, Dict, List, NamedTuple, Optional

game_modes = ['ffa', 'insta', 'effic', 'coop', 'ctf', 'efficctf', 'instactf']

class ConfigManager(metaclass=Singleton):
    def __init__(self, cfgfile: Optional[str] = None) -> None:
        from configparser import ConfigParser

        assert cfgfile is not None

        cfg = ConfigParser()
        cfg.read(cfgfile)

        # hold it as dict for now
        self_server: Dict[str, Union[int, str]] = {}
        self_maps: Dict[str, List[str]] = {}
        Messages = Dict[str, str]
        Url = Tuple[str, int]
        self_rooms: Dict[str, Dict[str, Union[int, str, Messages, Url]]] = {}
        roomKeys = {
            'public': asstr,
            'lan': asbool,
            'announce': asstr,
            'resetwhenempty': asbool, # TODO: implement reset when empty
            'timeout': asint,
            'gamemode': asstr,
            'maxclients': asint,
            'maxplayers': asint,
            'port': asint,
            'interface': asstr,
            'maxdown': asint,
            'maxup': asint,
            'mods_enabled': asstr,
            'messages': asstr,
        }
        sections = {
            'SERVER': { 'name': asstr, 'info': asstr, 'packages': asstr, 'shutdowncountdown': asint, 'adminpass': asstr },
            'MAPS': dict(zip(game_modes, repeat(asjsonobj)))
        }

        # later, class attributes will become named tuples
        Server = namedtuple('Server', ('name', 'info', 'packages', 'shutdowncountdown', 'adminpass', 'available_maps'))
        Maps = namedtuple('Maps', ['ffa', 'insta', 'effic', 'coop', 'ctf', 'efficctf', 'instactf', 'mode_indexes'])
        Room = namedtuple('Room', ['public', 'lan', 'announce', 'resetwhenempty', 'timeout', 'gamemode',
                                   'maxclients', 'maxplayers', 'port', 'interface', 'maxdown', 'maxup', 'mods_enabled', 'messages'])
        # sanity checks
        for section, validators in sections.items():
            section_keys = validators.keys()
            if section not in cfg:
                raise ConfigurationFileError(f"no [{section}] section in configuration file")
            elif missing_keys(section_keys, cfg[section].keys()):
                err = f"Missing configuration values in [{section}] section: " + \
                    f"{missing_keys(section_keys, cfg[section].keys())}"
                raise ConfigurationFileError(err)
            else:
                # assign to self.<section>
                def mfun1(key):
                    return key, validators[key](key, cfg[section][key])
                if section == 'SERVER':
                    self_server = dict(map(mfun1, section_keys))
                elif section == 'MAPS':
                    self_maps = dict(map(mfun1, section_keys))
                else:
                    assert False

        possible_rooms = list(filter(lambda s: s not in set(sections.keys()), cfg.sections()))
        for room in possible_rooms:
            if missing_keys(roomKeys.keys(), cfg[room].keys()):
                err = f"Missing configuration values in room: [{room}]: " + \
                    f"{missing_keys(roomKeys.keys(), cfg[room].keys())}"
                raise ConfigurationFileError(err)
            else:
                def mfun2(tp):
                    key, value = tp
                    return key, roomKeys[key](key, value) # key to value transformed
                self_rooms[room] = dict(map(mfun2, cfg[room].items()))


            # validate messagefile
            msgfile = self_rooms[room]['messages'] 
            assert isinstance(msgfile, str)
            if not os.path.exists(msgfile):
                raise ConfigurationError(f"File: '{msgfile}' does not exist")
            self_rooms[room]['messages'] = validate_message_file(msgfile)

            if self_rooms[room]['gamemode'] not in game_modes:
                msg = f"Invalid gamemode. Possible choices: {','.join(game_modes)}."
                raise ConfigurationError(msg)

            # check master url is fine
            announce = self_rooms[room]['announce']
            if announce != "":
                assert isinstance(announce, str)
                announce_l = announce.split(':')
                if len(announce_l) == 2 and announce_l[-1].isdigit():
                    self_rooms[room]['announce'] = (announce_l[0], int(announce_l[1]))
                    continue
            # else
            if self_rooms[room]['public']:
                raise ConfigurationFileError('Incorrect announce url:port : {announce}')

        # transform to named tuples
        self.rooms: Dict[str, Room] = {}
        for rname, room_map in self_rooms.items():
            self.rooms[rname] = Room(*room_map.values())
        self.server = Server(*self_server.values(), # type: ignore
                             available_maps=get_available_maps(self_server['packages'])) # type: ignore
        self.maps: Maps = Maps(*self_maps.values(), # type: ignore
                         mode_indexes=dict(map(lambda r: (r[1], r[0]), enumerate(game_modes)))) # type: ignore

    def get_rotation_dict(self) -> Tuple[Dict[str, List[str]], List[str]]:
        return (
            {  #'rotations':
                'instactf': self.maps.instactf,
                'ffa': self.maps.ffa,
                'effic': self.maps.effic,
                'ccop': self.maps.coop,
                'insta': self.maps.insta,
                'ctf': self.maps.ctf,
                'efficctf': self.maps.efficctf,
            },
            game_modes  # modes
        )
