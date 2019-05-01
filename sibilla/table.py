from sibilla import DatabaseError
from sibilla.object import ObjectType, OracleObject

# ---- Exceptions -------------------------------------------------------------

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

# -----------------------------------------------------------------------------


from sibilla.dataset import DataSet, Row, RowError, RowGetterError


class TableRow(Row):

    __slots__ = []

    @property
    def __pk__(self):
        record = self._get_record()
        return {
            k: getattr(record, k) for k in self.__dataset__.__pk__
        } if self.__dataset__.__pk__ else None

    def __repr__(self):
        ident = " with PK '{}'".format(
            self.__pk__
        ) if self.__pk__ else ""
        return "<row from {}{}>".format(self.__dataset__, ident)


class SmartRow(TableRow):

    __slots__ = []

    def get(self, name, default=None):
        try:
            foreign_table = getattr(
                self.__dataset__.db,
                self.__dataset__.__fk__[name]
            )
            return foreign_table[self.__field__(name)]
        except KeyError:
            # Not a foreign key
            raise RowGetterError()


class Table(OracleObject, DataSet):

    __row_class__ = TableRow

    __table__ = None
    __pk = None
    __fk = None

    def __init__(self, db, name=None, schema=None):
        name = name or self.__table__

        if name is None:
            raise TableError("No table name given")

        super().__init__(db, name, ObjectType.TABLE, schema)

    @property
    def __pk__(self):
        if self.__pk is None:
            self.__pk = [e[0] for e in self.db.fetch_all("""
                select cols.column_name
                from   {}_constraints  cons
                      ,{}_cons_columns cols
                where  cols.table_name      = :tab
                   and cons.status          = 'ENABLED'
                   and cons.constraint_type = 'P'
                   and cons.constraint_name = cols.constraint_name
                   and cons.owner           = cols.owner
                   {}
                order by cols.position
                """.format(
                    *["all" if self.__schema__ else self.db.__scope__] * 2,
                    ("and owner = '"+self.__schema__+"'") if self.__schema__ else ""
                ), self.name
            )]

        return self.__pk

    @property
    def __fk__(self):
        if self.__fk is None:
            # TODO: Support arbitrary foreign keys
            fk_list = self.db.fetch_all("""
                select cols.column_name
                      ,cond.table_name
                from   {}_constraints  cons
                      ,{}_constraints  cond
                      ,{}_cons_columns cols
                where  cols.table_name      = :tab
                   and cons.status          = 'ENABLED'
                   and cons.constraint_type = 'R'
                   and cons.constraint_name = cols.constraint_name
                   and cons.owner           = cols.owner
                   and cond.constraint_name = cons.r_constraint_name
                   {}
                order by cols.position
                """.format(
                    *["all" if self.__schema__ else self.db.__scope__] * 3,
                    ("and owner = '"+self.__schema__+"'") if self.__schema__ else ""

                ), self.name
            )

            self.__fk = {k.lower(): v.lower() for k, v in fk_list}

        return self.__fk

    def _get_by_pk(self, pk):
        if type(pk) not in (list, tuple):
            pk = (pk, )

        if len(self.__pk__) != len(pk):
            raise PrimaryKeyError(
                "Primary key size mismatch for table {} "
                "(expected {})".format(self.name, repr(self.__pk__))
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
                    self.name
                )
            )

    def __getitem__(self, pk):
        def row_generator():
            for n in range(pk.start, pk.stop, pk.step):
                yield self._get_by_pk(n)

        if not self.__pk__:
            raise PrimaryKeyError(
                "No primary key constraint on table {}.".format(self.name)
            )

        if isinstance(pk, slice):
            return row_generator()
        else:
            return self._get_by_pk(pk)

    def drop(self, flush_cache=True):
        self.db.plsql('drop table {}'.format(self.name))
        if flush_cache:
            self.db.cache.flush()

    def insert(self, values):
        def generate_insert_stmt(v, gen_kwargs=True):
            if isinstance(v, dict):
                insert_columns = "(" + ", ".join(v.keys()) + ") "
                insert_values = ", ".join([":" + k for k in v])
                insert_kwargs = v if gen_kwargs else {}

            elif isinstance(v, tuple):
                if len(v) != len(self.__cols__):
                    raise TableInsertError(
                        "Wrong number of values to insert (expected {})".format(
                            len(self.__cols__)
                        )
                    )

                insert_values = ", ".join([":" + k for k in self.__cols__])
                insert_columns = ""
                insert_kwargs = (
                    dict(list(zip(self.__cols__, v))) if gen_kwargs else {}
                )

            else:
                raise TableInsertError("Invalid type for values to insert.")

            return "insert into {} {}values ({})".format(
                self.name, insert_columns, insert_values
            ), insert_kwargs

        if not values:
            return

        try:
            # TODO: executemany doesn't support generators yet.
            #       See https://github.com/oracle/python-cx_Oracle/issues/200
            is_list = isinstance(values, list)
            insert_stmt, insert_kwargs = generate_insert_stmt(
                values[0] if is_list else values,
                not is_list
            )
            self.db.plsql(
                insert_stmt,
                batch=values if isinstance(values, list) else None,
                **insert_kwargs
            )
        except DatabaseError as e:
            raise TableInsertError(e) from e

    def truncate(self):
        self.db.plsql('truncate table {}'.format(self.name))
