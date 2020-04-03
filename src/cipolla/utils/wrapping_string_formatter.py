import string

from typing import Any, Callable, Dict, List, Tuple, Optional, Sequence, Mapping

class WrappingStringFormatter(string.Formatter):
    def __init__(self, global_fields: Optional[Dict[str, str]] = None) -> None:
        self.wrappers: Dict[str, Callable] = {}
        self.global_fields = global_fields or {}

    def get_field(self, field_name: str, args: Sequence[Any], kwargs: Mapping[str, str]) -> Tuple[str, str]:
        if '#' in field_name:
            wrapper_name, field_name = field_name.split('#', 1)
            wrapper = self.wrappers[wrapper_name]
            obj, used_key = string.Formatter.get_field(self, field_name, args, kwargs)
            obj = wrapper(obj)
        else:
            assert isinstance(kwargs, dict)
            kwargs.update(self.global_fields)
            obj, used_key = string.Formatter.get_field(self, field_name, args, kwargs)
        return obj, used_key
    
    def register_wrapper(self, wrapper_name: str, wrapper: Callable) -> None:
        self.wrappers[wrapper_name] = wrapper
