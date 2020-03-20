from twisted.application import service
from twisted.application.internet import TCPClient
from zope.interface import implementer

from spyd.authentication.interfaces import IAuthService
from spyd.authentication.services.vanilla.protocol_factory import MasterClientProtocolFactory
from spyd.authentication.services.vanilla.punitive_model_adapter import PunitiveModelAdapter

class VanillaMasterClientService(service.MultiService):
    implementer(IAuthService)

    @staticmethod
    def build(punitive_model, host, port, register_port):
        # host = "master.sauerbraten.org" #config.get('host')
        # port = 28787 #config.get('port')
        # register_port = 28785# config.get('register_port')
        domains = ["localhost", ""]

        punitive_model_adapter = PunitiveModelAdapter(punitive_model)

        protocol_factory = MasterClientProtocolFactory(punitive_model_adapter, host, register_port)

        return VanillaMasterClientService(port, protocol_factory, interface=host, domains=domains)

    def __init__(self, port, factory, interface='', domains=[]):
        service.MultiService.__init__(self)

        self._protocol_factory = factory
        self._domains = domains

        self._child_service = TCPClient(interface, port, factory)
        self._child_service.setServiceParent(self)

    def handles_domain(self, auth_domain):
        return auth_domain in self._domains

    def try_authenticate(self, auth_domain, auth_name):
        return self._protocol_factory.try_auth(auth_domain, auth_name)

    def answer_challenge(self, auth_domain, auth_id, answer):
        return self._protocol_factory.answer_challenge(auth_id, answer)
