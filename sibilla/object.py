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

from abc import ABC

import sibilla

from sibilla.caching import Cached, cachedmethod


class ObjectType(type):
    """Supported Oracle object types.

    Their main purpose is to allow changing the default class used to wrap
    Oracle object with Python objects by :class:`ObjectLookup`.
    """

    TABLE = "TABLE"
    VIEW = "VIEW"
    PACKAGE = "PACKAGE"
    PROCEDURE = "PROCEDURE"
    FUNCTION = "FUNCTION"
    RECORD = "RECORD"


class OracleObject(ABC):
    """Base Oracle object.

    This abstract class represents a generic stored Oracle object and makes the
    base for concrete objects, like :class:`sibilla.table.Table`,
    :class:`sibilla.package.Package` etc....
    """

    def __init__(self, db, object_name, object_type, schema):
        self.__db = db
        self.__name = sibilla.sql_identifier(self.renaming(object_name))
        self.__type = object_type
        self.__schema = schema

    def renaming(self, name):
        return name

    @property
    def db(self):
        return self.__db

    @property
    def name(self):
        return self.__name

    @property
    def object_type(self):
        return self.__type

    @property
    def __schema__(self):
        return self.__schema

    def __repr__(self):
        return "<{} '{}'{}>".format(
            self.__type.lower(),
            self.__name,
            " from schema '" + self.__schema + "'" if self.__schema else ""
        )


# ---- Exceptions -------------------------------------------------------------


class ObjectError(sibilla.DatabaseError):
    """Oracle object error.

    Defines an error specific to object lookup within the Oracle database
    associated to an Database object.
    """
    pass


class ObjectLookupError(ObjectError):
    """Raised when an object look-up fails."""
    pass


class ObjectTypeError(ObjectError):
    """Problems with Oracle object types."""
    pass


# -----------------------------------------------------------------------------


from sibilla.function import Function
from sibilla.package import Package
from sibilla.procedure import Procedure
from sibilla.schema import Schema, SchemaError
from sibilla.table import Table
from sibilla.view import View


_type_mapping = {
    ObjectType.TABLE: Table,
    ObjectType.VIEW: View,
    ObjectType.PROCEDURE: Procedure,
    ObjectType.FUNCTION: Function,
    ObjectType.PACKAGE: Package,
}

# -----------------------------------------------------------------------------


class ObjectLookup(Cached):
    """Oracle object look-up.

    Instances of this class allow customising the way objects (e.g. tables,
    views, packages, ...) are looked up from the Oracle database.

    Every instance of Database comes with a default ObjectLookup instance
    accessible through the read-only property ``__lookup__``. This can be
    used to specify the custom classes to handle general Oracle object, as well
    as specific items, like individual tables, packages, etc...

    Example:
        Assume that the database we are connected to has families of tables
        with a certain prefix, say ``DATA_``, that can be treated as a sort of
        namespace. One might want to be able to access such tables (e.g. the
        ``DATA_CUSTOMER`` table) with an attribute access on a Database object
        as::

            >>> from sibilla import Database
            >>> db = Database("username", "password", "dsn")
            >>> db.data.customer

        This can be achieved as shown below. First of all, one should subclass
        ``ObjectLookup`` and override the ``renaming`` method::

            from sibilla import ObjectLookup


            class DataLookup(ObjectLookup):

                def renaming(self, name):
                    return "data_" + name

        Then, one either assigns a new instance of ``DataLookup`` to
        ``db.data``::

            >>> db.data = DataLookup()

        or one subclasses Database and initializes ``data`` as an object
        attribute::

            class MyDB(Database):
                def __init__(self, *args, **kwargs):
                    super(MyDB, self).__init__(*args, **kwargs)
                    self.data = DataLookup(self)


            db = MyDB("username", "password", "dsn")

        Thus, ``db.data.customer`` becomes equivalent to ``db.data_customer``.

        By default, the look-up will create an object of type ``Table`` from
        ``sibilla`` for the table accessed as ``db.data_customer``. To change
        this behaviour, subclass ``Table`` and pass the class to the
        ``replace`` method as a dictionary:

            from sibilla import ObjectType, Table


            MyTable(Table):
                pass


            db.__lookup__.replace({ObjectType.TABLE: MyTable})

        Custom table classes can also be assigned to general attributes of a
        Database object by passing the attribute name as key in the dictionary:

            >>> db.__lookup__.replace({"customer": MyTable})

        This way, the custom table class ``MyTable`` is used only when
        accessing the attribite ``customer`` from ``db`` rather than for every
        table. Observe that this is **not** the same as assigning ``MyTable``
        directly to the attribute ``customer`` of ``db``.
    """

    __custom_objects__ = {}

    def __init__(self, db):
        super().__init__()

        self.__db = db

    def renaming(self, name: str) -> str:
        """Rename attribute before performing the look-up.

        This methods offers a customisation interface for implementing naming
        patterns and character substitution in look-ups. Any attribute accessed
        on an :class:`ObjectLookup` object is preprocessed by this method. This
        can be useful when database objects have characters which are not
        allowed in Python to appear in identifiers. For example,
        ``my_package#`` is a valid Oracle package name, however
        ``db.my_package#`` does not produce the desired result in Python. To
        overcome this situation one can subclass :class:`ObjectLookup` with an
        overridden method ``renaming`` that does a suitable conversion.

        Example:
            To access the Oracle package ``my_package#`` from Python, one could
            use the convention of replacing any occurrence of # with __.

                from sibilla import ObjectLookup


                class MyLookup(ObjectLookup):
                    def renaming(self, name):
                        return name.replace('__', '#')

            Any access to the attribute ``my_package__`` from a ``MyLookup``
            object is translated into ``my_package#`` before being actually
            looked up from the database.

        Args:
            name (str): The attribute accessed on an instance of the class.

        Returns:
            str: The translated attribute for lookup on the database.
        """

        return name

    @cachedmethod
    def __getattr__(self, name):
        qual_name = sibilla.sql_identifier(self.renaming(name)).strip('"')

        # Check for schema
        try:
            schema, name = qual_name.split('.')
        except ValueError:
            schema = None
            name = qual_name

        # Look through custom objects first
        try:
            object_class = self.__custom_objects__[name]

        except KeyError:  # Return standard object
            _, object_type = self.__db._fetch_many(
                """
                select object_type
                from   {scope}_objects
                where  object_name = :object_name
                   and object_type not in ('SYNONYM', 'PACKAGE BODY')
                   and subobject_name is null
                   {owner}
                """.format(
                    scope="all" if schema else self.__db.__scope__,
                    owner=("and owner = '" + schema + "'") if schema else ""
                ),
                n=2,
                object_name=name
            )

            if not object_type:
                try:
                    return Schema(self.__db, name)
                except SchemaError as e:
                    raise ObjectLookupError(
                        "No such object or schema: '{}'".format(name)
                    ) from e

            if len(object_type) != 1:
                # TODO: handle with disambiguator?
                raise ObjectLookupError(
                    "Multiple objects returned for name '{}'".format(name)
                )

            object_class = self.get_class(object_type[0][0])

        return object_class(self.__db, name, schema)

    def get_class(self, type_name):
        """The class assigned to an Oracle object type.

        Returns the class associated with the given type or attribute.

        Args:
            type_name (str): The type name to whose associated class is to be
                retrieved. This is meant to be either one of the values exposed
                by the ``ObjectType`` class, or a custom attribute.

        Returns:
            class: The class associated with the given type/attribute.
        """
        try:
            return self.__custom_objects__.get(
                type_name,
                _type_mapping[type_name]
            )
        except KeyError:
            raise ObjectTypeError(
                'Object type not supported: {}.'.format(type_name)
            )

    def replace(self, types: dict):
        """Replace Python classes for Oracle objects.

        Overrides the classes used to handle types/attributes on the lookup
        instance.

        Args:
            types (dict): A dictionary of key-value pairs where the key
                indicates the type/attribute and the value the class to use
                to handle the specified type/attribute. The standard Oracle
                object types can be overridden by using the constants exposed
                by the ``ObjectType`` class as key values.
        """
        self.__custom_objects__.update({
            sibilla.sql_identifier(k): v for k, v in types.items()
        })
