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

from functools import update_wrapper

from sibilla import CursorRow, DatabaseError
from sibilla.caching import Cached, cachedmethod
from sibilla.object import OracleObject


# ---- Exceptions -------------------------------------------------------------


class RowError(DatabaseError):
    """Dataset row error."""
    pass


class NoSuchRowError(RowError):
    """Raised when no row matches the given conditions.

    Similar to Oracle's``NO_DATA_FOUND``
    """
    pass


class RowAttributeError(RowError):
    """Row attribute access error."""
    pass


class MultipleRowsError(RowError):
    """Multiple rows returned when only one expected.

    Usually a consequence of a primary key defined on the table class that
    is not part of the actual table schema and that is violated by the
    retrieved data.
    """
    pass


class QueryError(DatabaseError):
    """Database query error."""
    pass


class RowGetterError(Exception):
    """Row getter method error.

    Raised when the requested attribute on the row cannot be determined.
    """
    pass


# -----------------------------------------------------------------------------


class Row(Cached):

    __slots__ = []

    def __init__(self, dataset, kwargs):
        super().__init__()

        self.__dataset__ = dataset
        self.__kwargs = kwargs

        self._get_record()

    @cachedmethod
    def _get_record(self):
        if isinstance(self.__kwargs, CursorRow):
            return self.__kwargs

        if not isinstance(self.__kwargs, dict):
            raise RowError(
                f"Row class does not support data of type {type(self.__kwargs)}"
            )
        res = self.__dataset__.fetch_many(2, **self.__kwargs)

        if len(res) > 1:
            raise MultipleRowsError(
                "Multiple rows returned by the matching criteria "
                "{} from {}.".format(
                    self.__kwargs,
                    self.__dataset__
                )
            )
        if not res:
            raise NoSuchRowError(
                "No rows returned by the matching criteria {} from {}.".format(
                    self.__kwargs,
                    self.__dataset__
                )
            )

        return res[0]

    @property
    def db(self):
        """Get the underlying database."""
        return self.__dataset__.db

    def get(self, name, default=None):
        """Attribute getter hook.

        This method provides a convenient customisation interface for
        subclasses of :class:`Row`. Implement it to define custom behaviour
        when retrieving row attributes.

        When the requested attribute cannot be determined, this method should
        raise the :class:`RowGetterError` exception.
        """
        raise RowGetterError()

    @cachedmethod
    def __getattr__(self, name):
        # Get a row method/attribute from the parent DataSet object
        attr = getattr(type(self.__dataset__), name, None)
        if attr is not None and not hasattr(OracleObject, name):
            if callable(attr):
                def callattr(*args, **kwargs):
                    return attr(self, *args, **kwargs)
                # It is a method
                return callattr

            # It is an attribute
            return attr.__get__(self)
        else:
            # Try to get a field using the custom getter
            try:
                return self.get(name, None)
            except RowGetterError:
                # Retrieve attribute from cached record
                try:
                    return self.__field__(name)
                except KeyError:
                    raise RowAttributeError(
                        "No attribute named '{}' for {}.".format(
                            name,
                            repr(self)
                        )
                    )

    def __field__(self, name):
        return getattr(self._get_record(), name)

    def __repr__(self):
        return "<row from {}>".format(self.__dataset__)


# ---- Decorators -------------------------------------------------------------


def rowmethod(func):
    def method_wrapper(row, *args, **kwargs):
        return func(row, *args, **kwargs)
    return staticmethod(update_wrapper(wrapper=method_wrapper, wrapped=func))


def rowattribute(func):
    return property(func)


# -----------------------------------------------------------------------------


def _generate_where_statement(e, binds, op=None):
    def generate_condition(k, v):
        key = k+str(len(binds))
        binds[key] = v

        return '{} {} {}'.format(
            k,
            'like' if isinstance(v, str) and '%' in v else '=',
            ":" + key
        )

    def group(s):
        return "(" + s + ")"

    if isinstance(e, str):
        return e

    if isinstance(e, dict):
        if op is None:
            raise QueryError("Invalid where clause")

        return group(
            op.join(generate_condition(k, v) for k, v in e.items())
        )

    if isinstance(e, list):
        return group(
            " or ".join(
                [_generate_where_statement(i, binds, " or ") for i in e]
            )
        )

    if isinstance(e, tuple):
        return group(
            " and ".join(
                [_generate_where_statement(i, binds, " and ") for i in e]
            )
        )

# def where_statement_from_kwargs(kwargs):
#     return ' and '.join(
#         ['{} {} :{}'.format(
#             k,
#             'like' if type(kwargs[k]) == str and '%' in kwargs[k] else '=',
#             k
#         ) for k in kwargs]
#     )
#
#
# def prepare_where_statement(where, kwargs):
#     if not kwargs:
#         return where if where else ""
#
#     if not where:
#         return where_statement_from_kwargs(kwargs)
#
#     return "{} and {}".format(where, where_statement_from_kwargs(kwargs))


class DataSet:

    __row_class__ = Row
    __cols = None

    @classmethod
    def set_row_class(cls, row_class):
        cls.__row_class__ = row_class

    def __call__(self, **kwargs):
        """Make an Oracle Table a callable object whose return value is a Row
        object referencing a row in the table by the table's primary key.

        One can also specify some other matching criteria, provided they will
        uniquely identify a row

        Args:
            **kwargs: Arbitrary keyword arguments for other matching
                conditions. The use of the WHERE clause is not allowed. In this
                case use the either the ``fetch_one`` or ``fetch_all`` methods
                directly instead.

        Returns:
            generator: TODO
        """
        if not kwargs:
            return self

        return self.fetch_all(**kwargs)

    def _generate_select_statement(
        self, select="*", where=None, order_by=None
    ):
        binds = {}
        where_stmt = ("where " + _generate_where_statement(where, binds)) \
            if where else ""

        return """
            select {cols}
            from   {tab}
            {where}
            {order_by}""".format(
                cols=', '.join(select),
                tab=self.name,
                where=where_stmt,
                order_by=(
                    " order by {}".format(order_by) if order_by is not None
                    else ""
                )
        ), binds

    def _prepare_fetch(self, select, where, order_by, kwargs):
        if not where and kwargs:
            where = (kwargs,)
            kwargs = {}

        statement, binds = self._generate_select_statement(
            select, where, order_by
        )
        binds.update(kwargs)

        return statement, binds

    def fetch_one(self, select="*", where=None, order_by=None, **kwargs):
        statement, binds = self._prepare_fetch(
            select, where, order_by, kwargs
        )
        result = self.db.fetch_one(
            statement,
            **binds
        )

        if not result:
            return None

        try:
            return (
                self.__row_class__(self, result) if self.__row_class__
                else result
            )
        except RowError as ex:
            raise QueryError(
                f"Row class {self.__row_class__} is incompatible with wrapped "
                f"row type {type(result)}"
            ) from ex

    def fetch_all(self, select="*", where=None, order_by=None, **kwargs):
        statement, binds = self._prepare_fetch(
            select, where, order_by, kwargs
        )
        result = self.db.fetch_all(
            statement,
            **binds
        )
        if self.__row_class__:
            def row_generator():
                for e in result:
                    try:
                        yield self.__row_class__(self, e)
                    except RowError as ex:
                        raise QueryError(
                            f"Row class {self.__row_class__} is incompatible "
                            f"with wrapped row type {type(e)}"
                        ) from ex
            return row_generator()
        else:
            return result

    def fetch_many(self, n, select="*", where=None, order_by=None, **kwargs):
        statement, binds = self._prepare_fetch(
            select, where, order_by, kwargs
        )
        result = self.db.fetch_many(
            statement,
            n, **binds
        )
        try:
            return (
                [self.__row_class__(self, row) for row in result]
                if self.__row_class__
                else result
            )
        except RowError as ex:
            raise QueryError(
                f"Row class {self.__row_class__} is incompatible with wrapped "
                f"row type in collection {type(result)}"
            ) from ex

    def __iter__(self):
        """Make a table iterable on its rows.

        When an instance of this class is used as an iterator, it is equivalent
        to the iteration over the ``fetch_all`` method.
        """
        return self.fetch_all()

    def describe(self):
        """Describe the table columns.

        The return value is the same as the ``description`` attribute of a
        Cursor object from the ``cx_Oracle`` module.
        """
        return self.db.plsql(
            "select * from " + self.name + " where 1=0"
        ).description

    @property
    def __cols__(self):
        if self.__cols is None:
            self.__cols = [c[0] for c in self.describe()]

        return self.__cols
