import logging
import os
import shutil
import sys

from twisted.application.service import MultiService

from spyd.config_manager import *
from spyd.log import SpydLogger

logging.setLoggerClass(SpydLogger)
logger = logging.getLogger(__name__)

import spyd as spyd_root_module
from spyd.spyd_server import SpydServer


### TRACING ###
from spyd.utils.tracing import trace_class
from spyd.game.room.roles import BaseRole

### END TRACING ###


def fatal(msg):
    logger.critical(msg)
    sys.exit(1)

def success(msg):
    logger.info(msg)
    sys.exit(0)

class WrapperService(MultiService):
    def __init__(self, options):
        self._options = options
        MultiService.__init__(self)

    def startService(self):
        options = self._options

        server_directory = options.get('servdir') or 'my_spyd_server'
        server_directory = os.path.expanduser(server_directory)
        cfgfile = options.get('config-file') or 'spyd.cfg'

        if not len(logging._handlers):
            logging.basicConfig()

        if not os.path.exists(server_directory):
            fatal("The specified server directory, {!r}, does not exist. Use the -i flag to create it.".format(server_directory))

        os.chdir(server_directory)
        logger.info("Using server directory; {!r}".format(os.path.abspath(os.curdir)))
        ConfigManager(cfgfile)

        spyd = SpydServer()

        spyd.root_service.setServiceParent(self)

        MultiService.startService(self)

        logger.spyd_event("Server started.")
