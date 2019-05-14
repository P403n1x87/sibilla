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

from sibilla import DatabaseError, sql_identifier
from sibilla.caching import Cached, cachedmethod


# ---- Exceptions -------------------------------------------------------------


class SchemaError(DatabaseError):
    """Database schema error.

    Raised when unable to reference a schema.
    """
    pass


# -----------------------------------------------------------------------------


class Schema(Cached):
    """Database schema class."""

    def __init__(self, db, schema):
        super().__init__()

        schema = sql_identifier(schema)

        self._user = db.fetch_one("""
            select *
            from   all_users
            where  username = :schema
        """,
        schema=schema)

        if not self._user:
            raise SchemaError(f"No such schema: {schema}")

        self._db = db

    @cachedmethod
    def __getattr__(self, name):
        return getattr(self._db, self._user.username + "." + name)

    @property
    def name(self):
        """The schema name."""
        return self._user.username
