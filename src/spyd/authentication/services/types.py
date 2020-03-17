from spyd.authentication.services.vanilla_service import VanillaMasterClientService
from spyd.authentication.services.maestro_service import MaestroMasterClientService
from spyd.authentication.services.no_op import NoOpMasterClientService

types = {
    'no_op': NoOpMasterClientService,
    'vanilla': VanillaMasterClientService,
    'maestro': MaestroMasterClientService
}
