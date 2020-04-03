from cipolla.authentication.auth_world_view import AuthWorldView

from cipolla.authentication.services.vanilla_service import VanillaMasterClientService
ANY = -1

from typing import List, Dict

class AuthWorldViewFactory(object):
    '''Creates AuthWorldView objects given the port that the client connected to.'''
    def __init__(self) -> None:
        # port: []
        self._registered_port_specific_auth_services: Dict = {}
        self._registered_general_auth_services: List = []

    def build_auth_world_view(self, port: int) -> AuthWorldView:
        auth_services = []
        auth_services.extend(self._registered_port_specific_auth_services.get(port, []))
        auth_services.extend(self._registered_general_auth_services)
        return AuthWorldView(auth_services)

    def register_auth_service(self, auth_service: VanillaMasterClientService, port: int = ANY) -> None:
        if port == ANY:
            self._registered_general_auth_services.insert(0, auth_service)
        else:
            if not port in self._registered_port_specific_auth_services:
                self._registered_port_specific_auth_services[port] = []
            self._registered_port_specific_auth_services[port].insert(0, auth_service)
