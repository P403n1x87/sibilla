import cx_Oracle

from sibilla.table import TableError
from sibilla.object import OracleObject

from sibilla.caching import Cached, cachedmethod

# -- Exceptions ----------------------------------------------------------------

class RowError(TableError):
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

class RowGetterError(Exception):
    pass

# ------------------------------------------------------------------------------

class Row(Cached):

    __slots__ = []

    def __init__(self, table, kwargs):
        super().__init__()

        self.__table__ = table
        self.__kwargs = kwargs

        self._get_record()

    @cachedmethod
    def _get_record(self):
        res = self.__table__.fetch_many(
            2,
            where=({k: ":" + k for k in self.__kwargs},),
            **self.__kwargs
        )

        if len(res) > 1:
            raise MultipleRowsError(
                "Multiple rows returned by the matching criteria {} from table {}.".format(
                    self.__kwargs,
                    self.__table__.name.upper()
                )
            )
        if not res:
            raise NoSuchRowError(
                "No rows returned by the matching criteria {} from table {}.".format(
                    self.__kwargs,
                    self.__table__.name.upper()
                )
            )

        record = res[0]
        pk = {
            k: getattr(record, k) for k in self.__table__.__pk__
        } if self.__table__.__pk__ else None

        return record, pk

    @property
    def db(self):
        return self.__table__.db

    def get(self, name, default=None):
        raise RowGetterError()

    @cachedmethod
    def __getattr__(self, name):
        # Get a row method/attribute from the parent Table object
        attr = getattr(type(self.__table__), name, None)
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
        record, _ = self._get_record()
        return getattr(record, name)

    @property
    def __pk__(self):
        _, pk = self._get_record()
        return pk

    def __repr__(self):
        _, pk = self._get_record()
        ident = "with PK '{}'".format(
            str(pk)
        ) if pk is not None else "at {}".format(id(self))
        return "<row from {} {}>".format(self.__table__, ident)


class SmartRow(Row):

    __slots__ = []

    def get(self, name, default=None):
        try:
            foreign_table = self.__table__.__fk__[name]
            return getattr(self.__table__.db, foreign_table)(
                self.__field__(name)
            )
        except KeyError:
            # Not a foreign key
            raise RowGetterError()
