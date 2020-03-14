

import cube2crypto

from txCascil.exceptions import AuthenticationHardFailure
from txCascil.registry_manager import register
from txCascil.utils.enum import enum


states = enum('PENDING_CONNECT', 'PENDING_CHALLENGE', 'PENDING_RESPONSE', 'AUTHENTICATED', 'DENIED')

@register('client_authentication_controller', 'cube2crypto')
class Cube2CryptoAuthenticationController(object):
    def __init__(self, config, protocol):
        self._protocol = protocol
        self._state = states.PENDING_CONNECT

        self._domain = config['domain']
        self._username = config['username']
        self._privkey = config['privkey']

    def send(self, message, respid=None):
        if respid is not None:
            message['respid'] = respid
        self._protocol.send(message)

    @property
    def is_authenticated(self):
        return self._state == states.AUTHENTICATED

    @property
    def _is_denied(self):
        return self._state == states.DENIED

    def connection_established(self):
        self.send({"msgtype": "connect", "username": self._username, "domain": self._domain})
        self._state = states.PENDING_CHALLENGE

    def receive(self, message):
        try:
            if self._is_denied: raise AuthenticationHardFailure()

            msg_type = message.get('msgtype')

            if msg_type == 'challenge':
                self._answer_challenge(message.get('challenge'))
            elif msg_type == 'status' and message.get('status') == 'success':
                self._state = states.AUTHENTICATED
            else:
                raise AuthenticationHardFailure()
        except:
            self._state = states.DENIED
            # traceback.print_exc()
            raise AuthenticationHardFailure()

    def _answer_challenge(self, challenge):
        answer = str(cube2crypto.answer_challenge(self._privkey, str(challenge)))
        self.send({'msgtype': 'answer', 'answer': answer})
        self._state = states.PENDING_RESPONSE
