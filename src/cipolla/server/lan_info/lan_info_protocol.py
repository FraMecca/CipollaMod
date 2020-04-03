from twisted.internet.protocol import DatagramProtocol # type: ignore

from cube2protocol.read_cube_data_stream import ReadCubeDataStream # type: ignore
from cipolla.server.lan_info.lan_info_responder import LanInfoResponder

from typing import List

class LanInfoProtocol(DatagramProtocol):
    def __init__(self, multicast: bool = False, ext_info_enabled: bool = True) -> None:
        self.lan_info_responders: List[LanInfoResponder] = []
        self.multicast = multicast
        self.ext_info_enabled = ext_info_enabled
        
    def startProtocol(self) -> None:
        if self.multicast:
            self.transport.setTTL(255)

    def add_responder(self, lan_info_responder: LanInfoResponder) -> None:
        self.lan_info_responders.append(lan_info_responder)

    def datagramReceived(self, data, address):
        rcds = ReadCubeDataStream(data)
        millis = rcds.getint()
        if millis != 0:
            for lan_info_responder in self.lan_info_responders:
                lan_info_responder.info_request(address, millis)
        elif self.ext_info_enabled:
            for lan_info_responder in self.lan_info_responders:
                lan_info_responder.ext_info_request(address, rcds.copy())

    def send(self, data, address):
        self.transport.write(data, address)
