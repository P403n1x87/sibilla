from functools import update_wrapper

from sibilla import DatabaseError
from sibilla.object import ObjectType, OracleObject


class TableError(DatabaseError):
    """Table-related database error."""
    pass


class TableEntryError(TableError):
    """Raised when failed to access a table entry."""
    pass


class TableInsertError(TableError):
    pass


class PrimaryKeyError(TableEntryError):
    """Raised when unable to make use of a primary key."""
    pass


from sibilla.row import Row, RowError

# ---- Decorators ----

def rowmethod(func):
    def method_wrapper(row, *args, **kwargs):
        return func(row, *args, **kwargs)
    return staticmethod(update_wrapper(wrapper=method_wrapper, wrapped=func))


def rowattribute(func):
    return property(func)

# ------------------------------------------------------------------------------

def generate_condition(k, v):
    return '{} {} {}'.format(
        k,
        'like' if isinstance(v, str) and '%' in v else '=',
        v
    )

def generate_where_statement(e, op=None):
    def group(s):
        return "(" + s + ")"

    if isinstance(e, str):
        return e

    if isinstance(e, dict):
        if op is None:
            raise TableError("Invalid where clause")

        return group(
            op.join(generate_condition(k, v) for k, v in e.items())
        )

    if isinstance(e, list):
        return group(
            " or ".join([generate_where_statement(i, " or ") for i in e])
        )

    if isinstance(e, tuple):
        return group(
            " and ".join([generate_where_statement(i, " and ") for i in e])
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


class Table(OracleObject):
    __table__ = None
    __pk__ = None
    __cols__ = None
    __fk__ = None
    __row_class__ = Row

    @classmethod
    def set_row_class(cls, row_class):
        cls.__row_class__ = row_class

    def __init__(self, db, name=None):
        name = name if name else self.__table__

        if name is None:
            raise TableError("No table name given")

        super().__init__(db, name, ObjectType.TABLE)
        if self.__pk__ is None:
            self.__pk__ = [e[0] for e in self.db.fetch_all("""
                select cols.column_name
                from   all_constraints  cons
                      ,all_cons_columns cols
                where  cols.table_name      = :tab
                   and cons.status          = 'ENABLED'
                   and cons.constraint_type = 'P'
                   and cons.constraint_name = cols.constraint_name
                   and cons.owner           = cols.owner
                order by cols.position
                """, self.name.upper())]

        if self.__cols__ is None:
            self.__cols__ = [c[0].lower() for c in self.db.fetch_all("""
                select column_name
                from   all_tab_cols
                where  table_name = :tab
                """, self.name.upper())]

        # TODO: Support arbitrary foreign keys
        if self.__fk__ is None:
            fk_list = self.db.fetch_all("""
                select cols.column_name
                      ,cond.table_name
                from   all_constraints  cons
                      ,all_constraints  cond
                      ,all_cons_columns cols
                where  cols.table_name      = :tab
                   and cons.status          = 'ENABLED'
                   and cons.constraint_type = 'R'
                   and cons.constraint_name = cols.constraint_name
                   and cons.owner           = cols.owner
                   and cond.constraint_name = cons.r_constraint_name
                order by cols.position
                """, self.name.upper())

            self.__fk__ = {k.lower(): v.lower() for k, v in fk_list}

    def __call__(self, pk=None, **kwargs):
        """Make an Oracle Table a callable object whose return value is a Row
        object referencing a row in the table by the table's primary key.

        One can also specify some other matching criteria, provided they will
        uniquely identify a row

        Args:
            pk (scalar or iterable): A primary key value that identifies the
                row
            **kwargs: Arbitrary keyword arguments for other matching
                conditions. The use of the WHERE clause is not allowed. In this
                case use the either the ``fetch_one`` or ``fetch_all`` methods
                directly instead.

        Returns:
            Row: A Row object referencing the row in the table with the given
                primary key or matching criteria.
        """

        if pk is None and not kwargs:
            return self

        if pk is None:
            return self.__row_class__(self, kwargs)
        else:
            if kwargs:
                raise TableEntryError(
                    "Cannot select by PK and additional conditions."
                )

            if not self.__pk__:
                raise PrimaryKeyError(
                    "No primary key constraint on table {}.".format(
                        self.name.upper()
                    )
                )

            if type(pk) not in (list, tuple):
                pk = [pk]

            if len(self.__pk__) != len(pk):
                raise PrimaryKeyError(
                    "Primary key size mismatch for table {} "
                    "(expected {})".format(
                        self.name.upper(), repr(self.__pk__)
                    )
                )

            try:
                return self.__row_class__(
                    self,
                    dict(list(zip(self.__pk__, pk)))
                )
            except RowError:
                raise PrimaryKeyError(
                    "No entry with PK '{}' in table {}".format(
                        repr(pk),
                        self.name.upper()
                    )
                )

    def __repr__(self):
        return "<table '{}'>".format(self.name.upper())

    def __iter__(self):
        """Make a table iterable on its rows.

        When an instance of this class is used as an iterator, it is equivalent
        to the iteration over the ``fetch_all`` method.
        """
        return self.fetch_all()

    # -- Public ---------------------------------------------------------------

    def describe(self):
        """Describe the table columns.

        The return value is the same as the ``description`` attribute of a
        Cursor object from the ``cx_Oracle`` module.
        """
        return self.db.plsql(
            "select * from " + self.name + " where 1=0"
        ).description

    def _generate_select_statement(self, select="*", where=None, order_by=None):
        where_stmt = ("where " + generate_where_statement(where)) \
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

    def drop(self, flush_cache=True):
        self.db.plsql('drop table {}'.format(self.name))
        if flush_cache:
            self.db.cache.flush()

    # TODO: Extend to allow bulk
    def insert(self, values):
        if isinstance(values, dict):
            insert_columns = "(" + ", ".join(values.keys()) + ")"
            insert_values = ", ".join([":" + k for k in values])
            insert_kwargs = values

        elif isinstance(values, tuple):
            if len(values) != len(self.__cols__):
                raise TableInsertError(
                    "Wrong number of values to insert (expected {})".format(
                        len(self.__cols__)
                    )
                )

            insert_values = ", ".join([":" + k for k in self.__cols__])
            insert_columns = ""
            insert_kwargs = dict(list(zip(self.__cols__, values)))

        else:
            raise TableInsertError("Invalid type for values to insert.")

        try:
            self.db.plsql(
                "insert into {} {} values ({})".format(
                    self.name, insert_columns, insert_values
                ),
                **insert_kwargs
            )
        except DatabaseError as e:
            raise TableInsertError(e) from e

    def truncate(self):
        self.db.plsql('truncate table {}'.format(self.name))
