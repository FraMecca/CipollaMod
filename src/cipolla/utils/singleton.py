from typing import Dict, Callable

class Singleton(type):
    _instances: Dict[Callable, object] = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]
