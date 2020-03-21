from collections import namedtuple

from spyd.utils.singleton import Singleton


class ConfigurationError(Exception): pass
class ConfigurationFileError(Exception): pass

from spyd.utils.configuration_utils import *

game_modes = ['ffa', 'insta', 'effic', 'coop', 'ctf', 'efficctf', 'instactf']

class ConfigManager(metaclass=Singleton):
    def __init__(self, cfgfile):
        from configparser import ConfigParser

        cfg = ConfigParser()
        cfg.read(cfgfile)

        self.server, self.maps, self.rooms = {}, {}, {}
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
            'SERVER': { 'name': asstr, 'info': asstr, 'packages': asstr, 'shutdowncountdown': asint },
            'MAPS': dict(zip(game_modes, repeat(asjsonobj)))
        }

        # later, class attributes will become named tuples
        Server = namedtuple('Server', list(sections['SERVER'].keys()) + ['available_maps'])
        Maps = namedtuple('Maps', list(sections['MAPS'].keys()) + ['mode_indexes'])
        Room = namedtuple('Room', roomKeys.keys())

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
                def to_tuple(key):
                    return key, validators[key](key, cfg[section][key])
                setattr(self, section.lower(), dict(map(to_tuple, section_keys)))
        possible_rooms = list(filter(lambda s: s not in set(sections.keys()), cfg.sections()))
        for room in possible_rooms:
            if missing_keys(roomKeys.keys(), cfg[room].keys()):
                err = f"Missing configuration values in room: [{room}]: " + \
                    f"{missing_keys(roomKeys.keys(), cfg[room].keys())}"
                raise ConfigurationFileError(err)
            else:
                def to_tuple(tp):
                    key, value = tp
                    return key, roomKeys[key](key, value) # key to value transformed
                self.rooms[room] = dict(map(to_tuple, cfg[room].items()))

            self.rooms[room]['messages'] = validate_message_file(self.rooms[room]['messages'])
            if self.rooms[room]['gamemode'] not in game_modes:
                msg = f"Invalid gamemode. Possible choices: {','.join(game_modes)}."
                raise ConfigurationError(msg)

            # check master url is fine
            announce = self.rooms[room]['announce']
            if announce != "":
                announce = announce.split(':')
                if len(announce) == 2 and announce[-1].isdigit():
                    self.rooms[room]['announce'] = (announce[0], int(announce[1]))
                    continue
            # else
            if self.rooms[room]['public']:
                raise ConfigurationFileError('Incorrect announce url:port : {announce}')

        # transform to named tuples
        for rname, room in self.rooms.items():
            self.rooms[rname] = Room(*room.values())
        self.server = Server(*self.server.values(),
                             available_maps=get_available_maps(self.server['packages']))
        self.maps = Maps(*self.maps.values(),
                         mode_indexes=dict(map(lambda r: (r[1], r[0]), enumerate(game_modes))))

    def get_rotation_dict(self):
        return {
            'rotations': {
                'instactf': self.maps.instactf,
                'ffa': self.maps.ffa,
                'effic': self.maps.effic,
                'ccop': self.maps.coop,
                'insta': self.maps.insta,
                'ctf': self.maps.ctf,
                'efficctf': self.maps.efficctf,
            },
            'modes': game_modes
        }
