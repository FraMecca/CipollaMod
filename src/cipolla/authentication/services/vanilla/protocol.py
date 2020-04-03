import logging

from twisted.protocols import basic # type: ignore
from cipolla.authentication.services.vanilla.constants import possible_commands


logger = logging.getLogger(__name__)
logger.setLevel(level=logging.WARN)


class MasterClientProtocol(basic.LineReceiver):
    delimiter = b"\n"

    def lineReceived(self, line: bytes) -> None:
        line = line.strip(b'\r')
        logger.debug("Received master server command: {!r}".format(line))
        args = line.split(b' ')
        if not len(args): return
        cmd = args[0]
        if not cmd in possible_commands: return
        handler_name = "master_cmd_{}".format(cmd) # type: ignore
        if hasattr(self.factory, handler_name):
            handler = getattr(self.factory, handler_name)
            handler(args)
        else:
            logger.error("Error no handler for master server command: {!r}".format(cmd))

    def sendLine(self, line: str) -> None:
        logger.debug("Sending master server command: {!r}".format(line))
        return basic.LineReceiver.sendLine(self, line.encode('utf-8'))

    def connectionMade(self) -> None:
        basic.LineReceiver.connectionMade(self)
        self.factory.connectionMade(self)

    def send_regserv(self, port: int) -> None:
        request = "regserv {}".format(port)
        self.sendLine(request)
        
    def send_reqauth(self, auth_id, auth_name):
        request = "reqauth {auth_id} {auth_name:.100s}".format(auth_id=auth_id, auth_name=auth_name)
        self.sendLine(request)
        
    def send_confauth(self, auth_id, answer):
        request = "confauth {auth_id} {answer:.100s}".format(auth_id=auth_id, answer=answer)
        self.sendLine(request)
