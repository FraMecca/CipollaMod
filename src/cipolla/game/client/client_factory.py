from cipolla.game.client.client import Client
from cipolla.server.binding.client_protocol import ClientProtocol

class ClientFactory(object):
    def __init__(self, client_number_handle_provider, room_bindings, auth_world_view_factory, servinfo_domain, punitive_model):
        self.client_number_handle_provider = client_number_handle_provider
        self.room_bindings = room_bindings
        self.auth_world_view_factory = auth_world_view_factory
        self.servinfo_domain = servinfo_domain
        self.punitive_model = punitive_model

    def build_client(self, client_protocol: ClientProtocol, binding_port: int) -> Client:
        clientnum_handle = self.client_number_handle_provider.acquire_cn_handle()

        room = self.room_bindings.get_room(binding_port)

        auth_world_view = self.auth_world_view_factory.build_auth_world_view(binding_port)

        return Client(client_protocol, clientnum_handle, room, auth_world_view, self.servinfo_domain, self.punitive_model)
