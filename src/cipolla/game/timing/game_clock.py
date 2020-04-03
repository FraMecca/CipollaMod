from twisted.internet import reactor # type: ignore

from cube2common.utils.enum import enum
from cipolla.game.timing.callback import Callback, call_all
from cipolla.game.timing.resume_countdown import ResumeCountdown
from cipolla.game.timing.scheduled_callback_wrapper import ScheduledCallbackWrapper, resume_all, pause_all


from typing import Callable, List, Optional

states = enum('NOT_STARTED', 'RUNNING', 'PAUSED', 'RESUMING', 'INTERMISSION', 'ENDED')

class GameClock(object):
    
    clock = reactor
    
    def __init__(self) -> None:
        self._state = states.NOT_STARTED
        
        self._last_resume_time: Optional[int] = None
        self._time_elapsed = 0.0
        
        self._intermission_duration_seconds = 0
        
        self._intermission_start_scheduled_callback_wrapper: Optional[ScheduledCallbackWrapper] = None
        self._intermission_end_scheduled_callback_wrapper: Optional[ScheduledCallbackWrapper] = None
        self._resume_countdown: Optional[ScheduledCallbackWrapper] = None
        
        self._timed = True
        
        self._paused_callbacks: List[Callback] = []
        self._resumed_callbacks: List[Callback] = []
        self._resume_countdown_tick_callbacks: List[Callback] = []
        self._timeleft_altered_callbacks: List[Callback] = []
        self._intermission_started_callbacks: List[Callback] = []
        self._intermission_ended_callbacks: List[Callback] = []
        
        self._scheduled_callback_wrappers: List[ScheduledCallbackWrapper] = []
        
    def _cancel_existing_scheduled_events(self) -> None:
        if self._intermission_end_scheduled_callback_wrapper is not None:
            self._intermission_end_scheduled_callback_wrapper.cancel()
            self._intermission_end_scheduled_callback_wrapper = None
            
        if self._intermission_start_scheduled_callback_wrapper is not None:
            self._intermission_start_scheduled_callback_wrapper.cancel()
            self._intermission_start_scheduled_callback_wrapper = None

        for scheduled_callback_wrapper in list(self._scheduled_callback_wrappers):
            scheduled_callback_wrapper.cancel()

    def cancel(self) -> None:
        '''Cancel the current game that is timed and start a new one.'''
        self._cancel_existing_scheduled_events()
        self._state = states.ENDED

    def _assert_not_started(self) -> None:
        assert(self._intermission_start_scheduled_callback_wrapper is None)
        assert(self._intermission_end_scheduled_callback_wrapper is None)
        assert(not self.is_started)
    
    def start(self, game_duration_seconds: int, intermission_duration_seconds: int) -> None:
        '''Set the game clock. If a game is currently underway, this will reset the time elapsed and set the amount of time left as specified.'''
        self._assert_not_started()

        self._timed = True
            
        self._intermission_duration_seconds = intermission_duration_seconds
        self._intermission_start_scheduled_callback_wrapper = ScheduledCallbackWrapper(game_duration_seconds)
        self._intermission_start_scheduled_callback_wrapper.add_timeup_callback(self._intermission_started)
        
        self._intermission_end_scheduled_callback_wrapper = ScheduledCallbackWrapper(game_duration_seconds+intermission_duration_seconds)
        self._intermission_end_scheduled_callback_wrapper.add_timeup_callback(self._intermission_ended)
        
        self._time_elapsed = 0.0
        
    def start_untimed(self):
        self._assert_not_started()

        self._state = states.PAUSED
        self._timed = False
        self._time_elapsed = 0.0
    
    def add_paused_callback(self, f: Callable, *args, **kwargs) -> None:
        '''Add a callback function which will be called with the specified arguments each time the game is paused.'''
        self._paused_callbacks.append(Callback(f, args, kwargs))

    def add_resumed_callback(self, f: Callable, *args, **kwargs) -> None:
        '''Add a callback function which will be called with the specified arguments each time the game is resumed.'''
        self._resumed_callbacks.append(Callback(f, args, kwargs))
    
    def add_resume_countdown_tick_callback(self, f: Callable, *args, **kwargs) -> None:
        '''Add a callback function which will be called with the specified arguments following the number of seconds until the game resumes each second until it does.'''
        self._resume_countdown_tick_callbacks.append(Callback(f, args, kwargs))
    
    def add_timeleft_altered_callback(self, f: Callable, *args, **kwargs) -> None:
        '''Add a callback which will be called with the specified arguments following the time left each time the amount of time in the game is altered.'''
        self._timeleft_altered_callbacks.append(Callback(f, args, kwargs))
    
    def add_intermission_started_callback(self, f: Callable, *args, **kwargs) -> None:
        '''Add a callback which will be called with the specified arguments each time the game clock enters intermission.'''
        self._intermission_started_callbacks.append(Callback(f, args, kwargs))
    
    def add_intermission_ended_callback(self, f: Callable, *args, **kwargs) -> None:
        '''Add a callback which will be called with the specified arguments each the time game clock leaves intermission.'''
        self._intermission_ended_callbacks.append(Callback(f, args, kwargs))

    def set_resuming_state(self):
        self._state = states.RESUMING
    
    def resume(self, delay: None = None) -> None:
        '''Resume the clock. If a delay is specified, the timer will resume after that number of seconds.'''
        if self.is_resuming:
            if self._resume_countdown is not None:
                self._resume_countdown.cancel()
                self._resume_countdown = None
        elif not self.is_started:
            pass
        elif not self.is_paused:
            return

        if delay is not None:
            self._state = states.RESUMING
            self._resume_countdown = ResumeCountdown(delay, Callback(self._resume_countdown_tick), Callback(self._resumed))
            self._resume_countdown.start()
        else:
            self._resumed()
    
    def pause(self):
        '''Pause the clock.'''
        if self.is_resuming:
            self._resume_countdown.cancel()
            self._resume_countdown = None
            self._state = states.PAUSED
        elif not self.is_paused:
            self._paused()

    def _remove_scheduled_callback_wrapper(self, scheduled_callback_wrapper):
        if scheduled_callback_wrapper in self._scheduled_callback_wrappers:
            self._scheduled_callback_wrappers.remove(scheduled_callback_wrapper)
    
    def schedule_callback(self, seconds):
        '''Schedule a callback after the specified number of seconds on the game clock. Returns a deferred.'''
        scheduled_callback_wrapper = ScheduledCallbackWrapper(seconds)
        scheduled_callback_wrapper.add_finished_callback(self._remove_scheduled_callback_wrapper, scheduled_callback_wrapper)
        self._scheduled_callback_wrappers.append(scheduled_callback_wrapper)
        if not self.is_paused:
            scheduled_callback_wrapper.resume()
        return scheduled_callback_wrapper
    
    @property
    def is_started(self) -> bool:
        return self._state not in (states.NOT_STARTED, states.ENDED)
    
    @property
    def is_paused(self) -> bool:
        '''Is the game clock currently paused.'''
        return self._state in (states.NOT_STARTED, states.PAUSED, states.RESUMING)
    
    @property
    def is_resuming(self) -> bool:
        '''Is there a resume countdown currently in progress.'''
        return self._state == states.RESUMING

    @property
    def is_game(self):
        '''Returns whether the game is started and not yet in intermission.'''
        return self._state in (states.RUNNING, states.PAUSED, states.RESUMING)

    @property
    def is_intermission(self) -> bool:
        '''Is the game clock currently in intermission.'''
        return self._state == states.INTERMISSION

    @property
    def timeleft(self):
        '''How much time left on the game clock.'''
        if self._intermission_start_scheduled_callback_wrapper is not None:
            return self._intermission_start_scheduled_callback_wrapper.timeleft
        else:
            return 0.0

    @timeleft.setter
    def timeleft(self, seconds):
        '''Set how many seconds are left on the game clock.'''
        if seconds > 0.0:
            self._intermission_start_scheduled_callback_wrapper.timeleft = seconds
            self._intermission_end_scheduled_callback_wrapper.timeleft = seconds + self._intermission_duration_seconds
            self._timeleft_altered()
        else:
            self._cancel_existing_scheduled_events()
            self._intermission_end_scheduled_callback_wrapper = ScheduledCallbackWrapper(self._intermission_duration_seconds)
            self._intermission_end_scheduled_callback_wrapper.add_timeup_callback(self._intermission_ended)
            self._timeleft_altered()

    @property
    def intermission_timeleft(self):
        '''How many seconds are left in the intermission.'''
        if self.is_intermission:
            return self._intermission_end_scheduled_callback_wrapper.timeleft
        else:
            return 0.0

    @property
    def time_elapsed(self) -> float:
        '''Return how many seconds this game has been going for.'''
        if self.is_paused:
            return self._time_elapsed
        else:
            time_elapsed = self._time_elapsed
            last_resume_time = self._last_resume_time or self.clock.seconds()
            return time_elapsed + (self.clock.seconds() - last_resume_time)

    def _paused(self):
        self._state = states.PAUSED
        self._time_elapsed += self.clock.seconds() - self._last_resume_time
        self._last_resume_time = None
        if self._timed:
            self._intermission_start_scheduled_callback_wrapper.pause()
            self._intermission_end_scheduled_callback_wrapper.pause()
        pause_all(self._scheduled_callback_wrappers)
        call_all(self._paused_callbacks)

    def _resumed(self) -> None:
        self._state = states.RUNNING
        self._last_resume_time = self.clock.seconds()
        self._resume_countdown = None
        if self._timed:
            if self._intermission_end_scheduled_callback_wrapper:
                self._intermission_end_scheduled_callback_wrapper.resume()
            if self._intermission_start_scheduled_callback_wrapper:
                self._intermission_start_scheduled_callback_wrapper.resume()

            resume_all(self._scheduled_callback_wrappers)

        call_all(self._resumed_callbacks)
        
    def _resume_countdown_tick(self, seconds):
        call_all(self._resume_countdown_tick_callbacks, seconds)

    def _intermission_started(self, *args, **kwargs):
        self._state = states.INTERMISSION
        call_all(self._intermission_started_callbacks)

    def _intermission_ended(self, *args, **kwargs):
        self._state = states.ENDED
        call_all(self._intermission_ended_callbacks)

    def _timeleft_altered(self):
        call_all(self._timeleft_altered_callbacks, self.timeleft)
