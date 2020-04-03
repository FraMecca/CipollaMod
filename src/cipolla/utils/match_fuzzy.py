import Levenshtein # type: ignore

from typing import Tuple, Optional

def match_fuzzy(identifier: str, possibility_list: Tuple, allow_ci_check: bool = True) -> Optional[str]:
        "Returns the nearest match to the text of identifier from a list of possibilities."
        if not len(possibility_list): return None
        threshold = len(identifier) - 1

        closest_match = min(possibility_list, key=lambda m: Levenshtein.distance(m, identifier))
        distance = Levenshtein.distance(closest_match, identifier)

        if distance <= threshold: return closest_match

        if not allow_ci_check: return None

        identifier = identifier.lower()

        closest_match = min(possibility_list, key=lambda m: Levenshtein.distance(m.lower(), identifier))
        distance = Levenshtein.distance(closest_match.lower(), identifier)

        if distance <= threshold: return closest_match

        return None
