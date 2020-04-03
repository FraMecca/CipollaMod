from itertools import repeat

from cipolla.config_manager import ConfigurationError, ConfigurationFileError

from typing import Dict, Tuple

from typing import Union, Dict, Any

def asint(key: str, value: str) -> int:
    if value.isdigit() and int(value) >= 0:
        return int(value)
    else:
        raise ConfigurationError(f'{key} should be a positive integer')

def asstr(key: str, value: str) -> str:
    return value

def asjsonobj(key: str, value: str) -> Any:
    from json import loads as jloads
    from os.path import exists
    if exists(value):
        try:
            with open(value, 'r') as f:
                return jloads(f.read())
        except:
            raise ConfigurationError(f"{value} is not a valid json")
    else:
        raise ConfigurationError(f"{value} can't be found on disk. Check path.")

def asbool(key: str, value: str) -> int:
    from distutils import util
    try:
        return util.strtobool(value)
    except:
        raise ConfigurationError(f'{key} should be a boolean')


def missing_keys(keys, obj):
    return set(keys) - set(obj)

def validate_message_file(filename: str) -> Dict[str, str]:
    from configparser import ConfigParser
    cfg = ConfigParser()
    try:
        cfg.read(filename)
        msgs = cfg['Room Messages']
        return dict(map(lambda k: (k, msgs.get(k, raw=True)),
                        ['player_connect', 'player_disconnect', 'server_welcome', 'server_goodbye']))
    except:
        raise ConfigurationError(f'Invalid message file: {filename}.')

def get_available_maps(package_dir: str) -> Tuple:
    def get(package_dir):
        import glob
        package_dir += 'base/' if package_dir == '/' else '/base/'
        for path in glob.glob(package_dir+'*.ogz'):
            yield path.split('/')[-1][:-4] # remove .ogz
    return tuple(get(package_dir))
