from typing import Dict, List, Union, Any
# TODO: remove
def dictget(dictionary: Dict[str, Union[int, List[Any]]], *keys) -> List[Any]:
    return [dictionary[key] for key in keys]
