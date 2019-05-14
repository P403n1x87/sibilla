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

from sibilla.callable import CallableFactory
from sibilla.caching import Cached, cachedmethod
from sibilla.object import OracleObject, ObjectType
# from .record import Record, PLSQLRecordError


# ---- Exceptions -------------------------------------------------------------


class PackageAttributeError(DatabaseError):
    """Package attribute error.

    Raised when unable to resolve the requested attribute from a package.
    """
    pass


# -----------------------------------------------------------------------------


class Package(OracleObject, Cached):
    """Oracle package class.

    This class models a stored Oracle package, providing access to functions
    and procedures.
    """

    __slots__ = []

    def __init__(self, db, name, schema):
        super().__init__(db, name, ObjectType.PACKAGE, schema)
        Cached.__init__(self)

        self.func = CallableFactory(
            self.db.__lookup__.get_class(ObjectType.FUNCTION),
            schema,
            self
        )

        self.proc = CallableFactory(
            self.db.__lookup__.get_class(ObjectType.PROCEDURE),
            schema,
            self
        )

    @cachedmethod
    def __getattr__(self, name):
        name = self.renaming(name)

        # No of procedures and functions
        tot, = self.db.fetch_one("""
            select count(*)
            from   {}_procedures
            where  object_name    = upper(:pkg_name)
               and procedure_name = upper(:name)
               {}
        """.format(
            "all" if self.__schema__ else self.db.__scope__,
            ("and owner= '"+self.__schema__+"'") if self.__schema__ else ""
        ),
            name=name,
            pkg_name=self.name
        )

        if not tot:
            # Look for records
            # try:
            #     return Record(self.db, "{}.{}".format(self.name, name))
            # except PLSQLRecordError:
            #     raise PackageAttributeError("No object '{}' within package '{}'".format(name, self.name))
            raise PackageAttributeError("No callable {} within {}".format(
                name, self
            ))

        # This reliably returns functions
        res = self.db.fetch_all("""
            select pls_type
            from   {}_arguments
            where  object_name  = upper(:name)
               and package_name = upper(:pkg_name)
               and position     = 0
               and defaulted    = 'N'
               {}
        """.format(
            "all" if self.__schema__ else self.db.__scope__,
            ("and owner= '"+self.__schema__+"'") if self.__schema__ else ""
        ), name=name, pkg_name=self.name)

        funcs = len(set(res))
        procs = tot - len(list(res))

        callable_class = self.db.__lookup__.get_class(
            ObjectType.FUNCTION if funcs else ObjectType.PROCEDURE
        )
        return callable_class(self.db, name, self.__schema__, self)
