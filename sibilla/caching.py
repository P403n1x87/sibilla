# This file is part of "sibilla" which is released under GPL.
#
# See file LICENCE or go to http://www.gnu.org/licenses/ for full license
# details.
#
# Sibilla is a Python ORM for the Oracle Database.
#
# Copyright (c) 2019 Gabriele N. Tornetta <phoenix1987@gmail.com>.
# All rights reserved.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

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

    def __init__(self, cache=None):
        """
        Initialise the instance with a ``cache`` attribute.

        Optionally, a cache object can be passed that will be used instead of
        the default one.

        Call ``flush`` on ``cache`` to force a flush of the cache.
        """
        self.cache = cache or SynchronizedTTLCache()
