from .oracle_object import ObjectType, OracleObject
from .row import NoSuchRowException
from functools import update_wrapper

# ------------------------------------------------------------------------------
# -- Decorators
# ------------------------------------------------------------------------------


def rowmethod(func):
    def method_wrapper(row, *args, **kwargs):
        return func(row, *args, **kwargs)
    return staticmethod(update_wrapper(wrapper=method_wrapper, wrapped=func))


def rowattr(func):
    return property(func)

# ------------------------------------------------------------------------------


def where_statement_from_kwargs(kwargs):
    return ' and '.join(
        ['{} {} :{}'.format(
            k,
            'like' if type(kwargs[k]) == str and '%' in kwargs[k] else '=',
            k
        ) for k in kwargs]
    )


def prepare_where_statement(where, kwargs):
    if not kwargs:
        return where if where else ""

    if not where:
        return where_statement_from_kwargs(kwargs)

    return "{} and {}".format(where, where_statement_from_kwargs(kwargs))


class Table(OracleObject):
    __table__ = None
    __pk__ = None
    __cols__ = None
    __fk__ = None

    def __init__(self, db, name=None):
        name = (
            type(self).__table__ if type(self).__table__ is not None else
            name
        )
        if name is None:
            ValueError("No table name provided in the superclass.")

        super(Table, self).__init__(db, name, ObjectType.TABLE)

        self.__pk__ = type(self).__pk__
        if self.__pk__ is None:
            self.__pk__ = [e.values[0] for e in self.db.fetch_all("""
                SELECT cols.column_name
                FROM   all_constraints  cons
                      ,all_cons_columns cols
                WHERE  cols.table_name      = :tab
                   AND cons.status          = 'ENABLED'
                   AND cons.constraint_type = 'P'
                   AND cons.constraint_name = cols.constraint_name
                   AND cons.owner           = cols.owner
                ORDER BY cols.position
                """, self.name.upper())]

        if self.__cols__ is None:
            self.__cols__ = [c[0].lower() for c in self.db.fetch_all("""
                SELECT column_name
                FROM   all_tab_cols
                WHERE  table_name = :tab
                """, self.name.upper())]

        if self.__fk__ is None:
            fk_list = self.db.fetch_all("""
                SELECT cols.column_name
                      ,cond.table_name
                FROM   all_constraints  cons
                      ,all_constraints  cond
                      ,all_cons_columns cols
                WHERE  cols.table_name      = :tab
                   AND cons.status          = 'ENABLED'
                   AND cons.constraint_type = 'R'
                   AND cons.constraint_name = cols.constraint_name
                   AND cons.owner           = cols.owner
                   AND cond.constraint_name = cons.r_constraint_name
                ORDER BY cols.position
                """, self.name.upper())

            self.__fk__ = {}
            for k, v in fk_list:
                self.__fk__[k.lower()] = v.lower()

    def __call__(self, pk=None, _id=None, **kwargs):
        """Make an Oracle Table a callable object whose return value is a Row
        object referencing a row in the table by the table's primary key.

        One can also specify some other matching criteria, provided they will
        uniquely identify a row

        Args:
            pk (scalar or iterable): A primary key value that identifies the
                row
            _id (scalar): Convenience argument for tables with a primary key on
                column named ID.
            **kwargs: Arbitrary keyword arguments for other matching
                conditions. The use of the WHERE clause is not allowed. In this
                case use the either the ``fetch_one`` or ``fetch_all`` methods
                directly instead.

        Returns:
            Row: A Row object referencing the row in the table with the given
                primary key or matching criteria.
        """

        if pk is None and _id is None and kwargs == {}:
            return None

        if pk is None:
            try:
                matching_conditions = (
                    {'id': _id} if _id is not None else
                    kwargs
                )

                row_object_handler = self.db.object_lookup.map(ObjectType.ROW)
                return row_object_handler(self, matching_conditions)

            except TypeError:
                if _id is not None:
                    raise ValueError(
                        "No entry with ID = {}, or no column named "
                        "ID in Table {}".format(_id, self.name.upper())
                    )
                else:
                    raise ValueError(
                        "oracle: No data matching the given criteria in Table "
                        + self.name.upper()
                    )
        else:
            if kwargs:
                raise ValueError(
                    "Unable to filter by PK and additional constraints"
                )

            if not self.__pk__:
                raise ValueError(
                    "Table '{}' has no primary key defined.".format(
                        self.name.upper()
                    )
                )

            if type(pk) not in (list, tuple):
                pk = [pk]

            if len(self.__pk__) != len(pk):
                raise TypeError(
                    "The given primary key for table '{}' is of wrong type "
                    "(expected {})".format(
                        self.name.upper(), repr(self.__pk__)
                    )
                )

            try:
                row_object_handler = self.db.object_lookup.map(ObjectType.ROW)
                return row_object_handler(
                    self,
                    dict(list(zip(self.__pk__, pk)))
                )
            except NoSuchRowException:
                raise ValueError(
                    "No entry with PK '{}' in Table {}".format(
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

    def fetch_one(self, columns="*", where=None, order_by=None, **kwargs):
        where_stmt = prepare_where_statement(where, kwargs)
        try:
            return self.db.fetch_one("""
                select {cols}
                from   {tab}
                {where}
                {order_by}""".format(
                    cols=', '.join(columns),
                    tab=self.name,
                    where=(
                        " where {}".format(where_stmt) if where_stmt != "" else
                        ""),
                    order_by=(
                        " order by {}".format(order_by) if order_by is not None
                        else "")
            ), **kwargs)

        except ValueError:
            raise ValueError(
                "Nothing matches '{}' (with {}) in table '{}'".format(
                    where_stmt,
                    kwargs,
                    self.name
                )
            )

    def fetch_all(self, columns="*", where=None, order_by=None, **kwargs):
        where_stmt = prepare_where_statement(where, kwargs)
        return self.db.fetch_all("""
            select {cols}
            from   {tab}
            {where}
            {order_by}""".format(
                cols=', '.join(columns),
                tab=self.name,
                where=" where " + where_stmt if where_stmt else "",
                order_by=(
                    " order by {}".format(order_by) if order_by is not None
                    else "")
        ), **kwargs)

    def fetch_many(self, n, columns="*", where=None, order_by=None, **kwargs):
        where_stmt = prepare_where_statement(where, kwargs)
        return self.db.fetch_many("""
            select {cols}
            from   {tab}
            {where}
            {order_by}""".format(
                cols=', '.join(columns),
                tab=self.name,
                where=" where " + where_stmt if where_stmt else "",
                order_by=(
                    " order by {}".format(order_by) if order_by is not None
                    else "")
        ), n, **kwargs)

    def truncate(self):
        self.db.plsql('truncate table {}'.format(self.name))
