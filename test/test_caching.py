from sibilla.caching import cachedmethod, Cached


class CachedClass(Cached):
    def __init__(self):
        super().__init__()
        self.call_count = 0

    @cachedmethod
    def cached_method(self, name):
        self.call_count += 1

        return name

    def test_cached_method(self):
        assert self.call_count == 0

        assert self.cached_method("first") == "first"
        assert self.call_count == 1

        [self.cached_method("first") for _ in range(10)]
        assert self.call_count == 1

        assert self.cached_method("second") == "second"
        assert self.call_count == 2

        [self.cached_method("second") for _ in range(10)]
        assert self.call_count == 2


class TestCached:
    def test_cached_method(self):
        CachedClass().test_cached_method()
