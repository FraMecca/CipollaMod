from twisted.internet import defer # type: ignore
from twisted.internet.defer import Deferred # type: ignore

from cube2common.constants import INTERMISSIONLEN # type: ignore

from cipolla.game.client.exceptions import GenericError
from cipolla.game.map.map_rotation import MapRotation
from cipolla.protocol import swh
from cipolla.game.map.async_map_meta_data_accessor import AsyncMapMetaDataAccessor
from cipolla.game.timing.game_clock import GameClock
# TODO: fix these
from cipolla.game.gamemode.insta import Insta # type: ignore
from cipolla.game.gamemode.gamemodes import gamemodes # type: ignore

from typing import Iterator, Optional, List, Dict


class RoomMapModeState(object):
    def __init__(self, room, map_rotation: Optional[MapRotation] = None, map_meta_data_accessor: Optional[AsyncMapMetaDataAccessor] = None, game_clock: Optional[GameClock] = None) -> None:
        from cipolla.game.room.room import Room
        self.room: Room = room
        self._map_name = ""
        self._gamemode = None
        self._map_meta_data_accessor = map_meta_data_accessor
        self._map_rotation = map_rotation
        self._game_clock = game_clock
        self._initialized = False
        self._initializing = False
        self._initializing_deferreds: List = []

    @property
    def initialized(self) -> bool:
        return self._initialized

    @property
    def map_name(self) -> str:
        assert self._map_rotation is not None
        if self.gamemode is None:
            map_name, _ = self._map_rotation.next_map_mode(peek=True)
            return map_name
        return self._map_name

    @property
    def gamemode(self): # return basemode
        return self._gamemode

    @property
    def mode_num(self) -> int:
        assert self._map_rotation is not None
        if self.gamemode is None:
            _, mode_name = self._map_rotation.next_map_mode(peek=True)
            return gamemodes[mode_name].clientmodenum
        return self.gamemode.clientmodenum

    @property
    def mode_name(self):
        assert self._map_rotation is not None
        if self.gamemode is None:
            _, mode_name = self._map_rotation.next_map_mode(peek=True)
            return gamemodes[mode_name].clientmodename
        return self.gamemode.clientmodename

    def get_map_names(self):
        return self._map_meta_data_accessor.get_map_names()

    @property
    def rotate_on_first_player(self) -> bool:
        assert self._map_rotation is not None
        return self._map_rotation.rotate_on_first_player

    @defer.inlineCallbacks
    def await_map_mode_initialized(self, player_count: int) -> Iterator[Deferred]:
        if self._initializing:
            deferred = defer.Deferred()
            self._initializing_deferreds.append(deferred)
            yield deferred
        else:
            if not self.initialized or (self.rotate_on_first_player and player_count == 0):
                self._initializing = True
                map_meta_data = yield self.rotate_map_mode()
                self._initializing = False

                while len(self._initializing_deferreds):
                    deferred = self._initializing_deferreds.pop()
                    deferred.callback(map_meta_data)

                defer.returnValue(map_meta_data)

    def rotate_map_mode(self) -> Deferred:
        assert self._map_rotation is not None
        map_name, mode_name = self._map_rotation.next_map_mode(peek=False)
        return self.change_map_mode(map_name, mode_name)

    @defer.inlineCallbacks
    def change_map_mode(self, map_name: str, mode_name: str) -> Iterator[Deferred]:
        assert self._map_meta_data_accessor is not None
        if mode_name not in gamemodes:
            raise GenericError("Unsupported game mode.")

        self._map_name = map_name

        map_meta_data = yield self._map_meta_data_accessor.get_map_data(self._map_name)

        self._gamemode = gamemodes[mode_name](room=self.room, map_meta_data=map_meta_data)
        self._initialized = True
        self._new_map_mode_initialize()

        defer.returnValue(map_meta_data)

    def _new_map_mode_initialize(self) -> None:
        assert self._game_clock is not None
        with self.room.broadcastbuffer(1, True) as cds:
            swh.put_mapchange(cds, self.map_name, self.gamemode.clientmodenum, hasitems=False)

            if self.gamemode.timed:
                self._game_clock.start(self.gamemode.timeout, INTERMISSIONLEN)
            else:
                self._game_clock.start_untimed()

            for player in self.room.players:
                self.gamemode.initialize_player(cds, player)
        self.room.resume()
        # TODO: remove deferred from map initialization
        # and avoid aving room pause/resume continuosly

        for player in self.room.players:
            player.state.map_change_reset()
            player.state.respawn()
            player._team = ""
            self.gamemode.spawn_loadout(player)

        if self.room.is_teammode:
            self.init_teams()

        for client in self.room.clients:
            with client.sendbuffer(1, True) as cds:

                if self.gamemode.timed and self.room.timeleft is not None:
                    swh.put_timeup(cds, self.room.timeleft)

                if self.room.is_paused:
                    swh.put_pausegame(cds, 1)

                for player in client.player_iter():
                    if not player.state.is_spectator:
                        swh.put_spawnstate(cds, player)

    def init_teams(self) -> None:
        from random import randint
        from itertools import chain
        from math import floor, ceil

        allplayers = list(self.room.players)
        nplayers = len(allplayers)
        decreasing_list = list(range(nplayers))

        to_int = (ceil, floor)[randint(0, 1)]
        for i in range(to_int(nplayers/2)):
            idx = randint(0, len(decreasing_list)-1)
            choice = decreasing_list.pop(idx)
            allplayers[choice]._team = 'evil'

        # rest
        for i in decreasing_list:
            allplayers[i]._team = 'good'
        for player in self.room.players:
            self.room.gamemode.on_player_try_set_team(player, player, player._team, player._team)
