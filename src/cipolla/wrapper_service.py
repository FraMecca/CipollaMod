import logging
import os
import shutil
import sys

from twisted.application.service import MultiService # type: ignore

from cipolla.config_manager import *
from cipolla.log import CipollaLogger

from cipolla.options import Options
logging.setLoggerClass(CipollaLogger)
logger = logging.getLogger(__name__)

import cipolla as cipolla_root_module
from cipolla.cipolla_server import CipollaServer


### TRACING ###
from cipolla.utils.tracing import trace_class
from cipolla.game.room.roles import BaseRole
from cipolla.game.room.roles import AdminRole
from cipolla.game.room.room_map_mode_state import RoomMapModeState
from cipolla.game.timing.game_clock import GameClock
from cipolla.mods.mods_manager import ModsManager
from cipolla.mods.commands_mod import CommandsMod
from cipolla.game.gamemode.bases.mode_base import ModeBase # type: ignore
from cipolla.game.gamemode.bases.ctf_base import CtfBase # type: ignore
from cipolla.game.room.room import Room
from cipolla.game.player.player import Player
from cipolla.game.player.player_state import PlayerState
from cipolla.game.timing.game_clock import GameClock

### END TRACING ###


def fatal(msg):
    logger.critical(msg)
    sys.exit(1)

def success(msg):
    logger.info(msg)
    sys.exit(0)

class WrapperService(MultiService):
    def __init__(self, options: Options) -> None:
        self._options = options
        MultiService.__init__(self)

    def startService(self) -> None:
        options = self._options

        server_directory = options.get('servdir') or 'my_cipolla_server'
        server_directory = os.path.expanduser(server_directory)
        cfgfile = options.get('config-file') or 'cipolla.cfg'

        # if not len(logging._handlers):
        #     logging.basicConfig()
        if not os.path.exists(server_directory):
            fatal("The specified server directory, {!r}, does not exist. Use the -i flag to create it.".format(server_directory))

        os.chdir(server_directory)
        logger.info("Using server directory; {!r}".format(os.path.abspath(os.curdir)))
        ConfigManager(cfgfile)

        cipolla = CipollaServer()

        cipolla.root_service.setServiceParent(self)

        MultiService.startService(self)

        logger.cipolla_event("Server started.") # type: ignore
