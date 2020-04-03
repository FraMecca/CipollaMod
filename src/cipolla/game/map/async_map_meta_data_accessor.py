import pickle
import os.path
import sys

from twisted.internet import defer, utils # type: ignore
from twisted.internet.defer import Deferred # type: ignore

from cipolla.utils.list_to_unicode import list_to_unicode

from typing import List
map_data_reader_filename = os.path.join(os.path.dirname(__file__), 'map_data_reader_process.py')

def run_map_data_reader_process(args: List[str]) -> Deferred:
    args.insert(0, map_data_reader_filename)
    deferred = utils.getProcessOutput(sys.executable, args, env={'PYTHONPATH': os.environ.get('PYTHONPATH', '')})
    deferred.addCallback(pickle.loads)
    return deferred

def get_map_names(map_glob_expression):
    return run_map_data_reader_process(['-l', map_glob_expression])

def get_map_data(map_path: str) -> Deferred:
    return run_map_data_reader_process(['-d', map_path])

class AsyncMapMetaDataAccessor(object):
    def __init__(self, package_dir: str) -> None:
        self.package_dir = package_dir

        self._cached_map_meta = {} # type: ignore
        self._map_name_cache = None

    def get_map_path(self, map_name: str) -> str:
        map_filename = "{}.ogz".format(map_name)
        return os.path.join(self.package_dir, "base", map_filename)

    def get_map_data(self, map_name: str, default: None = None) -> Deferred:
        if map_name in self._cached_map_meta:
            return defer.succeed(self._cached_map_meta.get(map_name))
        else:
            def cache_map_meta(map_meta_data):
                self._cached_map_meta[map_name] = map_meta_data
                return map_meta_data

            deferred = get_map_data(self.get_map_path(map_name))
            deferred.addCallback(cache_map_meta)

            return deferred

    def get_map_names(self):
        if self._map_name_cache is not None:
            return defer.succeed(self._map_name_cache)
        else:
            def cache_map_names(map_names):
                self._map_name_cache = map_names
                return self._map_name_cache

            map_glob_expression = os.path.join(self.package_dir, "base", "*.ogz")

            deferred = get_map_names(map_glob_expression)
            deferred.addCallback(cache_map_names)

            return deferred
