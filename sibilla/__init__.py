# from .db            import Database
# from sibilla.object import OracleObject, ObjectType
# from .__lookup__ import ObjectLookup, DatabaseObjectError
# from .table         import Table, rowattr, rowmethod
# from .view          import View
# from .row           import Row, TableFieldError
# from .package       import Package
# from .function      import Function
# from .procedure     import Procedure

import cx_Oracle

# ---- Module exceptions ----

class SibillaError(Exception):
    """Base Sibilla exception."""
    pass


class DatabaseError(SibillaError):
    """Generic database error."""
    pass


class LoginError(DatabaseError):
    pass


class ConnectionError(DatabaseError):
    pass


class IdentifierError(DatabaseError):
    """SQL identifier error."""
    pass


from sibilla.caching import Cached, cachedmethod
from sibilla.object import ObjectLookup, ObjectType

# ---- Local helpers ----

def sql_identifier(name: str) -> str:
    if name[0] == '"':
        if name[-1] != '"':
            raise IdentifierError("Invalid identifier: " + name)
        return name

    return name.upper()


class CursorRow:
    """
    Turn a row of data into a dictionary/list-like object.

    The constructor takes two lists of the same length as input parameters. The
    first contains the key names (usually the column names) and the second the
    values associated to each key.
    """

    def __init__(self, columns, row):
        if type(columns) not in (list, tuple) \
                or type(row) not in (list, tuple) \
                or len(columns) != len(row):

            if row is None:
                raise ValueError("None is not a valid row.")

            raise ValueError("Invalid row object")

        self._cols = columns
        self._state = dict(list(zip(columns, row)))
        self._max_col_len = None

    def __getattr__(self, name):
        return self.__dict__["_state"][sql_identifier(name)]

    def __getitem__(self, i):
        return self._state[self._cols[i]]

    def __repr__(self):
        if self._max_col_len is None:
            self._max_col_len = max([len(c) for c in self._cols])

        return "\n".join([
            ("{:" + str(self._max_col_len) + "} : ").format(c) + self._state[c]
            for c in self._cols
        ])

    def __dir__(self):
        return self._cols

    @property
    def values(self):
        return tuple([self.state[c] for c in self.cols])


class Database(cx_Oracle.Connection, Cached):
    """
    A subclass of the DB API specification-compliant cx_Oracle.Connection
    object, extended with additional features proper of Oracle Databases (11g
    and above).

    Example:
        To create an Database instance, import ``Database`` from ``sibilla``
        and pass `username`, `password` and `dsn` to it (plus any other
        optional argument accepted by the constructor of
        ``cx_Oracle.Connection``):

            >>> from sibilla import Database

            ...

            >>> db = Database(username, password, dsn=TNS)

    The class has built-in introspection for Oracle objects, like Tables,
    Views, Functions, Procedures and Packages.

    Example:
        To create a reference to a table called ``COUNTRY`` in the Oracle
        database, access the attribute ``country`` from the ``Database``
        instance:

            >>> db.country
            <table 'COUNTRY'>

    A table is a `callable` object that can be used to reference single rows
    from the corresponding table and treat them like objects. It is expected
    that the referenced table has a column named ID holding a primary key
    value.

    Examples:
        For tables with a primary key on a column called ``ID``, one can
        reference a row with ID = n simply with

            >>> db.country(n)
            <row from <table 'COUNTRY'> with ID n>

        To reference a row through another set of criteria, paris of column
        names and values can be passed to the table:

            >>> db.country(name = 'Italy')
            <row from <table 'COUNTRY'> with ID IT>

    A reference to a row can be treated like an object. The value of other
    columns can be accessed as attributes.

    Example:
        If ``row`` is a reference to a row in the table ``COUNTRY`` with
        ID = 'IT', one can access the ``NAME`` column with

            >>> row = db.country('IT')
            >>> row.name
            'Italy'

    In a similar way one can access stored `functions`, `procedures` and
    `packages`. For functions and procedures stored in a package, the code will
    try to figure out whether the sought object is a function or a procedure.
    When there are overloads that, due to the limitations of python, cannot be
    resolved, one can explicitly call a procedure or a function by accessing
    the ``proc`` and ``func`` attributes of a package.

    Example:
        Assume that the database holds a package ``foo`` containing overloaded
        procedures and functions named ``bar``. To call ``foo.bar`` as a
        procedure one has to use:

            >>> db.foo.proc.bar

        Similarly, to call bar as a function,

            >>> db.foo.func.bar

        When there are no ambiguities like in the previous case (e.g. there are
        only functions or only procedures named ``bar``), one can simply use

            >>> db.foo.bar
    """

    def __init__(self, *args, **kwargs):
        try:
            super().__init__(*args, **kwargs)
        except cx_Oracle.DatabaseError as e:
            error, = e.args
            code = error.code
            msg = error.message

            if code == 1017:
                raise LoginError(msg) from e
            if code == 12154:
                raise ConnectionError(msg) from e

            raise DatabaseError(msg) from e

        Cached.__init__(self)

        self._object_lookup = ObjectLookup(self)

        # Enable standard streams
        self.dbms_output.enable()

    @cachedmethod
    def __getattr__(self, name):
        return getattr(self.__lookup__, name, None)

    # ---- PUBLIC METHODS ----

    def to_cursor_row(self, cursor):
        """
        Return the fetch results from the provided cursor in the form of a
        dictionary. Note that this method returns a generator.

        Args:
            cursor (cx_Oracle.Cursor): The cursor to fetch the data from. Data
                should be available to be fetched, which means that, for
                instance, a SQL statement must have been executed first before
                passing the cursor to this method.

        Returns:
            generator: A generator that yields a dictionary containing the
            column name : column value pairs.
        """

        columns = [c[0] for c in cursor.description]

        for row in cursor:
            yield CursorRow(columns, row)

    def get_errors(self, name = None, type = None):
        """
        Returns all the occurred errors in the form of CursorRow with the
        fields _name_, _type_, _line_, _position_, _error_ and _text_. The
        errors can be filtered by object name and type via the two optional
        arguments

        Args:
            name (str): Filter errors by object name. A pattern can be used
                (case sensitive)
            type (str): Filter errors by object type. A pattern can be used
                (case insensitive)

        Returns:
            list: a list of CursorRow objects describing all the requested
                error messages.
        """

        where_list = []
        if name:
            where_list.append("name like '{}'".format(name))

        if type:
            where_list.append("type like '{}'".format(type))

        return self.fetch_all("""
            select name, type, line, position, text error, src_text text from (
              select e.*, s.text src_text
              from   user_errors e
                    ,user_source s
              where  attribute = 'ERROR'
                 and s.line = e.line
                 and s.name = e.name
                 and s.type = e.type
              union
              select e.*, to_char(null)
              from   user_errors e
              where  attribute = 'ERROR'
                 and 0 = line
            ) {where}
            order by upper(name) asc, type asc, sequence asc
            """.format(
                where=(
                    "where " + " and ".join(where_list)) if where_list else ""
                )
            )

    def get_output(self):
        """Get the output from the standard output stream buffer."""
        buf = self.var(cx_Oracle.STRING)
        status = self.var(cx_Oracle.NUMBER)
        text = ""

        while True:
            self.dbms_output.get_line(buf, status)
            if int(status.getvalue()) > 0:
                break  # Nothing left to read
            line = buf.getvalue()
            if line is not None:
                text += line
            text += "\n"
        return text

    def fetch_one(self, stmt, *args, **kwargs):
        """
        Fetches only one row from the execution of the provided statement. Bind
        variables can be provided both as positional and as keyword arguments
        to this method.

        Args:
            stmt (str): The statement to execute.

            *args: Variable length argument list for positional bind variables.

            **kwargs: Arbitrary keyword arguments for named bind variables.

        Returns:
            tuple: A record as a result of the executed statement.
        """
        cursor = self.plsql(stmt, *args, **kwargs)
        res = cursor.fetchone()
        if res:
            return CursorRow([c[0] for c in cursor.description], res)

        return None

    def fetch_all(self, stmt, *args, **kwargs):
        """
        Fetch all rows from the execution of the provided statement.

        Bind variables can be provided both as positional and as keyword
        arguments to this method.

        Args:
            stmt (str): The statement to execute.
            *args: Variable length argument list for positional bind variables.
            **kwargs: Arbitrary keyword arguments for named bind variables.

        Returns:
            generator: A collection of all the records returned by the provided
            statement.
        """
        return self.to_cursor_row(self.plsql(stmt, *args, **kwargs))

    def fetch_many(self, stmt, n, *args, **kwargs):
        """
        Fetch many rows from the execution of the provided statement.

        The number of raws returned as a list by this function is at most ``n``
        for each call made.

        Args:
            stmt (str): The statement to execute.
            n (int): The number of rows to fetch.
            *args: Variable length argument list for positional bind variables.
            **kwargs: Arbitrary keyword arguments for named bind variables.

        Returns:
            list: A list of at most n records returned by the provided
            statement.
        """
        cursor = self.plsql(stmt, *args, **kwargs)
        return [
            CursorRow([c[0] for c in cursor.description], row)
            for row in cursor.fetchmany(n)
        ]

    # TODO: Batch execute: https://blogs.oracle.com/opal/efficient-and-scalable-batch-statement-execution-in-python-cx_oracle
    def plsql(self, stmt, *args, **kwargs):
        """
        Executes the provided (PL/)SQL code. Bind variables can be provided
        both as positional and as keyword arguments to this method. Returns
        a cursor in case data needs to be fetched out of it.

        Args:
            stmt (str): The (PL/)SQL statement to execute.
            *args: Variable length argument list for positional bind variables.
            **kwargs: Arbitrary keyword arguments for named bind variables.

        Returns:
            cx_Oracle.cursor: the cursor associated with the code execution.
        """

        if args and kwargs:
            raise InterfaceError(
                "Expecting positional argument or keyword arguments, but not"
                "both"
            )

        cursor = self.cursor()
        if args:
            cursor.execute(stmt, args)
        else:
            cursor.execute(stmt, **kwargs)

        return cursor

    # TODO: This can use Function._Function__datatype_mapping to map python
    #       types to Oracle types.
    def var(self, var_type):
        """
        Creates and returns a variable of the given type from the cx_Oracle
        package.

        Args:
            var_type: The type of the variable to create. This must be one of
                the possible types provided by the cx_Oracle package.
        """
        cur = self.cursor()
        return cur.var(var_type)

    def commit(self, reset_cache = True):
        super(Database, self).commit()

        if reset_cache:
            self.cache.flush()

    # ---- PROPERTIES ----

    @property
    def session_user(self):
        """Returns the session user for the connection."""

        return self.fetch_one(
            "SELECT SYS_CONTEXT ('USERENV', 'SESSION_USER') FROM DUAL"
        )[0]

    @session_user.setter
    def session_user(self, value):
        raise AttributeError("'session_user' is read-only.")

    @property
    def __lookup__(self):
        """
        Read-only attribute. An internal ``ObjectLookup`` object to describe
        how to discover database objects. The default classes can be overridden
        with a call to the ``replace`` method to handle custom behaviour that
        best reflect the database design. See the section dedicated to  the
        ``ObjectLookup`` class for examples.
        """

        return self._object_lookup

    @__lookup__.setter
    def __lookup__(self, value):
        raise AttributeError("'__lookup__' is a read-only property.")
