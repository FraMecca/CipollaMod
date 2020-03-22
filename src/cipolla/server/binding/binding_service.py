import traceback

from twisted.application import service
from twisted.internet import reactor, task

from cipolla.server.binding.binding import Binding


class BindingService(service.Service):
    def __init__(self, client_protocol_factory):
        self.bindings = set()

        self.client_protocol_factory = client_protocol_factory

        reactor.addSystemEventTrigger('during', 'flush_bindings', self.flush_all)
        self.flush_looping_call = task.LoopingCall(reactor.fireSystemEvent, 'flush_bindings')

    def startService(self):
        for binding in self.bindings:
            binding.listen(self.client_protocol_factory)

        self.flush_looping_call.start(0.033)

        service.Service.startService(self)

    def stopService(self):
        self.flush_looping_call.stop()
        service.Service.stopService(self)

    def add_binding(self, interface, port, maxclients, maxdown, maxup, max_duplicate_peers):
        binding = Binding(reactor, interface, port, maxclients=maxclients, channels=2, maxdown=maxdown, maxup=maxup, max_duplicate_peers=max_duplicate_peers)
        self.bindings.add(binding)

    def flush_all(self):
        reactor.callLater(0, reactor.addSystemEventTrigger, 'during', 'flush_bindings', self.flush_all)
        try:
            for binding in self.bindings:
                binding.flush()
        except:
            traceback.print_exc()
