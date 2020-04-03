from cipolla.utils.net import dottedQuadToLong, simpleMaskedIpToLongIpAndMask

from typing import Optional, Dict, Any


class PunitiveModel(object):
    # effect_type: {mask: {masked_ip: effect_info}}
    punitive_effects: Dict[str, Any] = {} # TODO: figure out effect_info or rework this class

    def __init__(self) -> None:
        self.clear_effects()

    def clear_effects(self, effect_type: Optional[str] = None) -> None:
        if effect_type is None:
            self.punitive_effects = {}
        else:
            self.punitive_effects[effect_type] = {}

    def get_effect(self, effect_type: str, _client_ip: str) -> None:
        client_ip = dottedQuadToLong(_client_ip)
        effects_of_type = self.punitive_effects.get(effect_type, {})
        for mask, effects in effects_of_type.items():
            masked_ip = mask & client_ip
            if masked_ip in effects:
                return effects[masked_ip]
        return None

    def add_effect(self, effect_type, effect_desc, effect_info):
        if type(effect_desc) is tuple:
            if type(effect_desc[0]) == str:
                effect_desc = list(map(dottedQuadToLong, effect_desc))
            long_ip, long_mask = effect_desc
        else:
            long_ip, long_mask = simpleMaskedIpToLongIpAndMask(effect_desc)

        if effect_type not in self.punitive_effects:
            self.punitive_effects[effect_type] = {}

        if long_mask not in self.punitive_effects[effect_type]:
            self.punitive_effects[effect_type][long_mask] = {}

        masked_ip = long_ip & long_mask

        self.punitive_effects[effect_type][long_mask][masked_ip] = effect_info
