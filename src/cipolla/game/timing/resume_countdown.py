from twisted.internet import reactor # type: ignore

from cube2common.utils.enum import enum


states = enum('NOT_STARTED', 'RUNNING', 'ENDED')


class StateError(Exception): pass

class ResumeCountdown(object):

    clock = reactor

    def __init__(self, seconds, tick_callback, ended_callback):
        self._seconds = seconds
        self._tick_callback = tick_callback
        self._ended_callback = ended_callback
        self._delayed_calls = []
        self._state = states.NOT_STARTED

    def start(self):
        if self._state != states.NOT_STARTED:
            raise StateError()
        for seconds_left in range(1, int(self._seconds)):
            self._delayed_calls.append(self.clock.callLater(self._seconds - seconds_left, self._tick, seconds_left))
        self._delayed_calls.append(self.clock.callLater(self._seconds, self._ended))
        self._state = states.RUNNING

    def cancel(self):
        if self._state != states.RUNNING:
            raise StateError()
        for delayed_call in self._delayed_calls:
            if not delayed_call.called:
                delayed_call.cancel()
        self._delayed_calls = []
        self._state = states.ENDED

    def _tick(self, seconds_left):
        self._tick_callback.call(seconds_left)

    def _ended(self):
        self._ended_callback.call()
        self._state = states.ENDED
