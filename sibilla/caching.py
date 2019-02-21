import threading

import cachetools

# Default cache parameters
_ttl = 60 * 60 * 24  # 1 day
_max_size = 1024


def set_ttl(ttl):
    """Set the TTL value to use when creating Cached objects."""
    global _ttl
    _ttl = ttl


def set_maxsize(size):
    """Set the maximum cache size when creating Cached objects."""
    global _max_size
    _max_size = size


def cachedmethod(f):
    """Caching decorator for class and instance methods."""
    return cachetools.cachedmethod(
        cache=lambda s: s.cache,
        lock=lambda s: s.cache._lock
    )(f)


class SynchronizedTTLCache(cachetools.TTLCache):
    """Implement a synchronised TTL cache."""

    def __init__(self):
        """Initialise the synchronised cache with the set parameters.

        The TTL and maximum size parameters are set at the module level and
        can be changed with the provided setters.
        """
        super().__init__(maxsize=_max_size, ttl=_ttl)

        self._lock = threading.RLock()

    def flush(self):
        """Flush the cache."""
        with self._lock:
            self.clear()


class Cached:
    """Cache mixin for adding synchronised TTL caching support to objects."""

    def __init__(self):
        """
        Initialise the instance with a ``cache`` attribute.

        Call ``flush`` on ``cache`` to force a flush of the cache.
        """
        self.cache = SynchronizedTTLCache()
