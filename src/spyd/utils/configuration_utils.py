from itertools import repeat

from spyd.config_manager import ConfigurationError, ConfigurationFileError

def asint(key, value):
    if value.isdigit() and int(value) >= 0:
        return int(value)
    else:
        raise ConfigurationError(f'{key} should be a positive integer')

def asstr(key, value):
    return value

def asjsonobj(key, value):
    from json import loads as jloads
    from os.path import exists
    if exists(value):
        try:
            with open(value, 'r') as f:
                jloads(f.read())
        except:
            raise ConfigurationError(f"{value} is not a valid json")
    else:
        raise ConfigurationError(f"{value} can't be found on disk. Check path.")

def asbool(key, value):
    from distutils import util
    try:
        return util.strtobool(value)
    except:
        raise ConfigurationError(f'{key} should be a boolean')


def missing_keys(keys, obj):
    return set(keys) - set(obj)

def validate_message_file(filename):
    from configparser import ConfigParser
    cfg = ConfigParser()
    try:
        cfg.read(filename)
        msgs = cfg['Room Messages']
        return dict(map(lambda k: (k, msgs.get(k, raw=True)),
                        ['player_connect', 'player_disconnect', 'server_welcome', 'server_goodbye']))
    except:
        raise ConfigurationError(f'Invalid message file: {filename}.')
