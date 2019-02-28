from time import sleep

from sibilla.caching import cachedmethod, Cached, set_ttl, set_maxsize


TTL=1
MAXSIZE = 2


class CachedClass(Cached):
    def __init__(self):
        super().__init__()
        self.call_count = 0

    @cachedmethod
    def cached_method(self, name):
        self.call_count += 1

        return name

    def test_cached_method(self):
        assert self.cache.maxsize == MAXSIZE
        assert self.call_count == 0

        [self.cached_method("first") for _ in range(3)]
        assert self.call_count == 1

        [self.cached_method("second") for _ in range(3)]
        assert self.call_count == 2

        [self.cached_method("third") for _ in range(3)]
        assert self.call_count == 3

        [self.cached_method("fourth") for _ in range(3)]
        assert self.call_count == 4

        [self.cached_method("first") for _ in range(3)]
        assert self.call_count == 5

        assert self.cache.currsize == MAXSIZE

        sleep(TTL + 1)

        assert self.cache.currsize == 0

        [self.cached_method("first") for _ in range(3)]
        assert self.call_count == 6


class TestCached:
    def test_cached_method(self):
        set_ttl(TTL)
        set_maxsize(MAXSIZE)

        CachedClass().test_cached_method()
