from cipolla.authentication.services.vanilla_service import VanillaMasterClientService
from cipolla.punitive_effects.punitive_model import PunitiveModel
from cipolla.utils.configuration_utils import ConfigurationError

class MasterClientServiceFactory(object):
    def __init__(self, punitive_model: PunitiveModel) -> None:
        from cipolla.authentication.services.types import types as service_types
        self._punitive_model = punitive_model

        self._service_types = service_types

    def build_master_client_service(self, host: str, port: int, register_port: int) -> VanillaMasterClientService:
        master_client_type = 'vanilla'
        if master_client_type is None:
            raise ConfigurationError("Master client type was not specified or was null, please specify a valid 'type' parameter.")

        if master_client_type not in self._service_types:
            raise ConfigurationError("Master client type was not a known value. Allowed types are {!r}".format(list(self._service_types.keys())))

        master_client_class = self._service_types[master_client_type]

        return master_client_class.build(self._punitive_model, host, port, register_port)
