import spyd.authentication.services  # @UnusedImport
from spyd.config_loader import ConfigurationError


class MasterClientServiceFactory(object):
    def __init__(self, punitive_model):
        from spyd.authentication.services.types import types as service_types
        self._punitive_model = punitive_model

        self._service_types = service_types

    def build_master_client_service(self, config):
        master_client_type = config.get('type', None)
        if master_client_type is None:
            raise ConfigurationError("Master client type was not specified or was null, please specify a valid 'type' parameter.")

        if master_client_type not in self._service_types:
            raise ConfigurationError("Master client type was not a known value. Allowed types are {!r}".format(list(self._service_types.keys())))

        master_client_class = self._service_types[master_client_type]

        return master_client_class.build(self._punitive_model, config)
