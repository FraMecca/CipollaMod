
from txCascil.registry_manager import register
import clj

@register('packing', 'edn')
class EdnPacking(object):
    @staticmethod
    def pack(message):
        return clj.dumps(message)

    @staticmethod
    def unpack(data):
        return clj.loads(data)
