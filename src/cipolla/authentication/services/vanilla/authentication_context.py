from twisted.internet import defer # type: ignore
from zope.interface import implementer # type: ignore

from cipolla.authentication.interfaces import IAuthChallenge
from cipolla.authentication.services.vanilla.constants import authentication_states


class AuthChallenge(object):
    implementer(IAuthChallenge)

    def __init__(self, auth_id, auth_domain, challenge):
        self.auth_id = auth_id
        self.auth_domain = auth_domain
        self.challenge = challenge

class AuthenticationContext(object):
    def __init__(self, auth_id, auth_domain, auth_name):
        self.auth_id = auth_id
        self.auth_domain = auth_domain
        self.auth_name = auth_name
        self.state = authentication_states.PENDING_CHALLENGE
        self.deferred = defer.Deferred()
        self.timeout_deferred = None
