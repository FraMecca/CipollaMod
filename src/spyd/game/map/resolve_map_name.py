from twisted.internet import defer

from spyd.config_manager import ConfigManager
from spyd.game.client.exceptions import GenericError
from spyd.utils.match_fuzzy import match_fuzzy


def resolve_map_name(room, map_name):
    valid_map_names = ConfigManager().server.available_maps
    map_name_match = match_fuzzy(map_name, valid_map_names)

    if map_name_match is None:
        raise GenericError('Could not resolve map name {value#map_name} to valid map. Please try again.', map_name=map_name)
    return map_name_match
