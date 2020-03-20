import unittest

from twisted.internet import task

from spyd.utils.rate_limiter import RateLimiter


class TestRateLimiter(unittest.TestCase):
    def setUp(self):
        self.clock = task.Clock()
        RateLimiter.clock = self.clock
        self.rate_limiter = RateLimiter(5)

    def test_check_drop_first_second(self):
        self.assertFalse(any([self.rate_limiter.check_drop() for _ in range(5)]))
        self.assertTrue(all([self.rate_limiter.check_drop() for _ in range(5)]))

    def test_check_drop_two_seconds(self):
        self.assertFalse(any([self.rate_limiter.check_drop() for _ in range(5)]))
        self.assertTrue(all([self.rate_limiter.check_drop() for _ in range(5)]))
        self.clock.advance(1)
        self.assertFalse(any([self.rate_limiter.check_drop() for _ in range(5)]))
        self.assertTrue(all([self.rate_limiter.check_drop() for _ in range(5)]))
