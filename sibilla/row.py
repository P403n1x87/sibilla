import cx_Oracle

from sibilla.object import OracleObject

from .cached import Cached

# -- Exceptions ----------------------------------------------------------------


class TableFieldError(Exception):
    pass

class MultipleRowsException(Exception):
    pass

class NoSuchRowException(Exception):
    pass

# ------------------------------------------------------------------------------


class Row(Cached):
    def __init__(self, table, kwargs):
        super(Row, self).__init__()
        self.__table = table
        self.__kwargs = kwargs
        self.__record = None
        self._pk = None

    def _get_record(self):
        res = self.__table.fetch_many(2, **self.__kwargs)
        if len(res) > 1:
            raise MultipleRowsException(
                "Multiple rows returned by the matching criteria {} from table {}.".format(
                    self.__kwargs,
                    self.__table.name.upper()
                )
            )
        if not res:
            raise NoSuchRowException(
                "No rows returned by the matching criteria {} from table {}.".format(
                    self.__kwargs,
                    self.__table.name.upper()
                )
            )

        self.__record = res[0]
        self._pk = {
            k: getattr(self.__record, k) for k in self.__table.__pk__
        } if self.__table.__pk__ is not None else None

    @property
    def table(self):
        return self.__table

    @property
    def db(self):
        return self.table.db

    def get(self, name, default=None):
        return None

    def __getattr__(self, name):
        # if name[:2] == "__": name = "_{}{}".format(type(self).__name__, name)
        # Try to hit the cache
        ret = self.get_cached(name)
        if ret is not None:
            return ret

        # Get a row method from the parent Table object
        attr = getattr(type(self.table), name, None)
        if attr is not None and not hasattr(OracleObject, name):
            if callable(attr):
                def callattr(*args, **kwargs):
                    return attr(self, *args, **kwargs)
                # It is a method
                ret = callattr
            else:
                # It is an attribute
                ret = attr.__get__(self)
        else:
            # Try to get a field
            ret = self.get(name, None)
            if ret is None:
                try:
                    ret = self.field(name)
                except KeyError:
                    raise TableFieldError(
                        "No attribute named '{}' for {}.".format(
                            name,
                            repr(self)
                        )
                    )

        self.cache(name, ret)

        return ret

    def reset(self):
        super().reset()

        self.__record = None

    def field(self, name):
        if self.__record is None:
            self._get_record()
        return getattr(self.__record, name)

    def __repr__(self):
        ident = "with PK '{}'".format(
            str(self.__pk)
        ) if self._pk is not None else "at {}".format(id(self))
        return "<row from {} {}>".format(self.table, ident)
