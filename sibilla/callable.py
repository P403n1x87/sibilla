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

from sibilla import DatabaseError
from sibilla.caching import Cached, cachedmethod
from sibilla.object import OracleObject
# from sibilla.record import RecordInstance as RecordI


# ---- Exceptions -------------------------------------------------------------


class CallableError(DatabaseError):
    """Database stored callable error."""
    pass


# -----------------------------------------------------------------------------


class CallableFactory(Cached):
    """Create a Python callable for a database stored callable.

    This class should be considered as private as it is used internally to
    allow calling an object as a function or a procedure explicitly.
    """

    __slots__ = []

    def __init__(self, callable_class, schema, package=None):
        """Callable factory constructor."""
        super().__init__(package.cache if package else None)

        self.__class = callable_class
        self.__package = package
        self.__schema = schema

    @cachedmethod
    def __getattr__(self, name):
        return self.__class(
            self.__package.db, name, self.__schema, self.__package
        )

# -----------------------------------------------------------------------------
# TODO: Record support is still incomplete
# -----------------------------------------------------------------------------
# def has_record_args(args, kwargs):
#     return has_arg_of_type(RecordI, args, kwargs)
#
#
# def record_args(args, kwargs):
#     rec_args = [x for x in args if type(x) == RecordI]
#     rec_kwargs = {k: v for k, v in kwargs.items() if type(v) == RecordI}
#
#     if not rec_args and not rec_kwargs:
#         return "", ""
#
#     declare = []
#     block = []
#
#     if rec_args:
#         for i, e in enumerate(rec_args):
#             declare.append("l_rec_arg{} {};".format(i, e.type))
#             field_assignment(e, block, "l_rec_arg{}".format(i))
#
#     if rec_kwargs:
#         for i, key in enumerate(rec_kwargs):
#             e = kwargs[key]
#             declare.append("l_rec_kwarg{} {};".format(i, e.type))
#             field_assignment(e, block, "l_rec_kwarg{}".format(i))
#
#     return "\n".join(declare), "\n".join(block)
# -----------------------------------------------------------------------------


class Callable(OracleObject):
    """Base class for Procedures and Functions."""

    def __init__(self, db, name, type, schema, package=None):
        """Callable constructor.

        If a package is specified, it implies that the requested callable is
        stored inside it.
        """
        super().__init__(db, name, type, schema)

        self.package = package
        self.callable_name = (
            package.name + "." + self.name if package else self.name
        )

    def __repr__(self):
        return "<{} '{}'{}>".format(
            self.object_type.lower(),
            self.name,
            " from " + repr(self.package) if self.package else ""
        )
