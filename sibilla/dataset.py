import cx_Oracle

from functools import update_wrapper

from sibilla import DatabaseError
from sibilla.object import OracleObject

from sibilla.caching import Cached, cachedmethod

# -- Exceptions ---------------------------------------------------------------

class RowError(DatabaseError):
    pass

class NoSuchRowError(RowError):
    """Raised when no row matches the given conditions.

    Similar to Oracle's``NO_DATA_FOUND``
    """
    pass

class RowAttributeError(RowError):
    pass

class MultipleRowsError(RowError):
    pass

class QueryError(DatabaseError):
    pass

class RowGetterError(Exception):
    pass

# -----------------------------------------------------------------------------

from sibilla import CursorRow


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

        res = self.__dataset__.fetch_many(
            2,
            where=({k: ":" + k for k in self.__kwargs},),
            **self.__kwargs
        )

        if len(res) > 1:
            raise MultipleRowsError(
                "Multiple rows returned by the matching criteria {} from {}.".format(
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
        return self.__dataset__.db

    def get(self, name, default=None):
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

def _generate_where_statement(e, op=None):
    def generate_condition(k, v):
        return '{} {} {}'.format(
            k,
            'like' if isinstance(v, str) and '%' in v else '=',
            v
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
            " or ".join([_generate_where_statement(i, " or ") for i in e])
        )

    if isinstance(e, tuple):
        return group(
            " and ".join([_generate_where_statement(i, " and ") for i in e])
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

    def _get_generator(self, kwargs):
        for row in self.fetch_all(
            where=({k: ":" + k for k in kwargs},),
            **kwargs
        ):
            yield self.__row_class__(self, row)

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

        return self._get_generator(kwargs)

    def _generate_select_statement(self, select="*", where=None, order_by=None):
        where_stmt = ("where " + _generate_where_statement(where)) \
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
        )

    def fetch_one(self, select="*", where=None, order_by=None, **kwargs):
        return self.db.fetch_one(
            self._generate_select_statement(select, where, order_by),
            **kwargs
        )

    def fetch_all(self, select="*", where=None, order_by=None, **kwargs):
        return self.db.fetch_all(
            self._generate_select_statement(select, where, order_by),
            **kwargs
        )

    def fetch_many(self, n, select="*", where=None, order_by=None, **kwargs):
        return self.db.fetch_many(
            self._generate_select_statement(select, where, order_by),
            n, **kwargs
        )

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
