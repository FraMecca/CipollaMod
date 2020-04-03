from twisted.internet import reactor # type: ignore


class RateLimiter(object):

    clock = reactor

    def __init__(self, limit: int) -> None:
        self._limit = limit
        self._this_sec = -1
        self._count_this_sec = 0

    def check_drop(self) -> bool:
        curr_sec = int(self.clock.seconds())
        if self._this_sec != curr_sec:
            self._this_sec = curr_sec
            self._count_this_sec = 0

        self._count_this_sec += 1

        return self._count_this_sec > self._limit
