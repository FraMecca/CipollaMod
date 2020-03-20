from twisted.application import service
from twisted.internet import defer
from zope.interface import implementer

from spyd.authentication.exceptions import AuthFailedException
from spyd.authentication.interfaces import IAuthService


class NoOpMasterClientService(service.Service):
    implementer(IAuthService)
    
    def handles_domain(self, auth_domain):
        return True
    
    def try_authenticate(self, auth_domain, auth_name):
        return defer.fail(AuthFailedException("Could not determine which master server to send your request to."))

    def answer_challenge(self, auth_domain, auth_id, answer):
        return defer.fail(AuthFailedException("Could not determine which master server to send your request to."))
