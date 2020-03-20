from collections import namedtuple

from spyd.utils.singleton import Singleton


class ConfigurationError(Exception): pass
class ConfigurationFileError(Exception): pass

from spyd.utils.configuration_utils import *

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
            'resetwhenempty': asbool,
            'timeout': asint,
            'maxclients': asint,
            'maxplayers': asint,
            'port': asint,
            'interface': asstr,
            'maxdown': asint,
            'maxup': asint,
            'mods_enabled': asstr,
            'mods_disabled': asstr,
            'messages': asstr,
        }
        sections = {
            'SERVER': { 'name': asstr, 'info': asstr, 'packages': asstr, 'shutdowncountdown': asint },
            'MAPS': dict(zip(('ctf', 'instactf', 'efficctf', 'effic', 'ffa', 'insta'), repeat(asjsonobj)))
        }

        # later, class attributes will become named tuples
        Server = namedtuple('Server', sections['SERVER'].keys())
        Maps = namedtuple('Maps', sections['MAPS'].keys())
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
        self.server = Server(*self.server.values())
        self.maps = Maps(*self.maps.values())
