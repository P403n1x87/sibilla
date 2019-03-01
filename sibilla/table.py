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


from sibilla.dataset import Row, RowError, DataSet


class Table(OracleObject, DataSet):
    
    __table__ = None
    __pk__ = None
    __fk__ = None

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
                """, self.name)]

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
                """, self.name)

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

        if pk is None:
            return super().__call__(**kwargs)

        else:
            if kwargs:
                raise TableEntryError(
                    "Cannot select by PK and additional conditions."
                )

            if not self.__pk__:
                raise PrimaryKeyError(
                    "No primary key constraint on table {}.".format(self.name)
                )

            if type(pk) not in (list, tuple):
                pk = [pk]

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
