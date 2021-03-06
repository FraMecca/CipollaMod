import logging
import os

from twisted.application import service # type: ignore
from twisted.internet import reactor, defer # type: ignore

from cube2common.constants import disconnect_types # type: ignore
from cube2protocol.sauerbraten.collect.server_read_message_processor import ServerReadMessageProcessor # type: ignore
from .server.lan_info.lan_info_service import LanInfoService
from cipolla.authentication.auth_world_view_factory import AuthWorldViewFactory, ANY
from cipolla.authentication.master_client_service_factory import MasterClientServiceFactory
from cipolla.game.client.client_factory import ClientFactory
from cipolla.game.client.client_number_provider import get_client_number_handle_provider
from cipolla.game.map.async_map_meta_data_accessor import AsyncMapMetaDataAccessor
from cipolla.game.room.room_bindings import RoomBindings
from cipolla.game.room.room import Room
from cipolla.game.server_message_formatter import notice
from cipolla.mods.mods_manager import ModsManager
from cipolla.punitive_effects.punitive_model import PunitiveModel
from cipolla.server.binding.binding_service import BindingService
from cipolla.server.binding.client_protocol_factory import ClientProtocolFactory
from cipolla.config_manager import ConfigManager


logger = logging.getLogger(__name__)

class CipollaServer(object):
    def __init__(self):
        self.root_service = service.MultiService()

        self.server_name = ConfigManager().server.name
        self.server_info = ConfigManager().server.info

        sauerbraten_package_dir = ConfigManager().server.packages
        self.map_meta_data_accessor = AsyncMapMetaDataAccessor(sauerbraten_package_dir)
        print("Using package directory; {!r}".format(sauerbraten_package_dir))

        self.room_bindings = RoomBindings()

        self.punitive_model = PunitiveModel()
        self.auth_world_view_factory = AuthWorldViewFactory()

        self.message_processor = ServerReadMessageProcessor()

        self.connect_auth_domain = '' # TODO understand how to remove this
        self.master_client_service_factory = MasterClientServiceFactory(self.punitive_model)

        client_number_handle_provider = get_client_number_handle_provider()
        self.client_factory = ClientFactory(client_number_handle_provider, self.room_bindings, self.auth_world_view_factory, self.connect_auth_domain, self.punitive_model)

        # 200 is client message rate limit
        self.client_protocol_factory = ClientProtocolFactory(self.client_factory, self.message_processor, 200)

        self.binding_service = BindingService(self.client_protocol_factory)
        self.binding_service.setServiceParent(self.root_service)

        self.lan_info_service = LanInfoService(True)
        self.lan_info_service.setServiceParent(self.root_service)

        self._initialize_rooms()
        self._initialize_master_clients()

        reactor.addSystemEventTrigger("before", "shutdown", self._before_shutdown, None)

    def _initialize_rooms(self):
        for rname, roomCfg in ConfigManager().rooms.items():
            interface = roomCfg.interface
            port = roomCfg.port
            maxclients = roomCfg.maxclients
            maxdown = roomCfg.maxdown
            maxup = roomCfg.maxup
            gamemode = roomCfg.gamemode
            room = Room(room_name=rname,
                        map_meta_data_accessor=self.map_meta_data_accessor,
                        defaultGameMode=gamemode)
            if roomCfg.public:
                # port is the port of the room that needs to be registered in the master server
                master_url = roomCfg.announce[0]
                master_port = roomCfg.announce[1]

            max_duplicate_peers = 10
            self.binding_service.add_binding(interface, port, maxclients, maxdown, maxup, max_duplicate_peers)
            self.room_bindings.add_room(port, room, False)
            self.lan_info_service.add_lan_info_for_room(room, interface, port)

            #TODO better validation of room
            for mod_name in filter(lambda s: s != '""', roomCfg.mods_enabled.split(',')):
                if ModsManager().enable(mod_name, room):
                    logger.info('enabled mod: ' + mod_name)
                else:
                    logger.warning("Can't enable: "+mod_name)

    def _before_shutdown(self, config):
        shutdown_countdown = ConfigManager().server.shutdowncountdown

        reactor.callLater(0.1, logger.cipolla_event, "Shutting down in {} seconds to allow clients to disconnect.".format(shutdown_countdown))
        self.client_protocol_factory.disconnect_all(disconnect_type=disconnect_types.DISC_NONE, message=notice("Server going down. Please come back when it is back up."))

        for i in range(shutdown_countdown):
            reactor.callLater(shutdown_countdown - i, logger.cipolla_event, "{}...".format(i))
        d = defer.Deferred()
        reactor.callLater(shutdown_countdown + 0.1, d.callback, 1)
        return d

    def _initialize_master_clients(self):
        # for master_server_config in config['master_servers']:
        #     register_port = master_server_config.get('register_port', ANY)
        #     master_client_service = self.master_client_service_factory.build_master_client_service(master_server_config)
        #     self.auth_world_view_factory.register_auth_service(master_client_service, register_port)
        #     master_client_service.setServiceParent(self.root_service)

        for rname, roomCfg in ConfigManager().rooms.items():
            if roomCfg.public:
                # port is the port of the room that needs to be registered in the master server
                master_url = roomCfg.announce[0]
                master_port = roomCfg.announce[1]
                register_port = roomCfg.port
                master_client_service = self.master_client_service_factory.build_master_client_service(master_url, master_port, register_port)
                self.auth_world_view_factory.register_auth_service(master_client_service, register_port)
                # master_client_service.setServiceParent(self.root_service, master_url, master_port, register_port)
                master_client_service.setServiceParent(self.root_service)
