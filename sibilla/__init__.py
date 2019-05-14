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

from abc import ABC, abstractmethod
from typing import Any, Generator

import cx_Oracle


# ---- Module exceptions ------------------------------------------------------


class SibillaError(Exception):
    """Base Sibilla exception."""
    pass


class DatabaseError(SibillaError):
    """Generic database error."""
    pass


class LoginError(DatabaseError):
    """Database login error."""
    pass


class ConnectionError(DatabaseError):
    """Database connection error."""
    pass


class IdentifierError(DatabaseError):
    """SQL identifier error."""
    pass

class CursorRowError(SibillaError):
    """Cursor row wrapper error."""
    pass


# ---- Local helpers ----------------------------------------------------------


def sql_identifier(name: str) -> str:
    """Treat string as SQL identifier.

    SQL identifier are case insensitive, unless they are double-quoted. This
    helper function ensures that any identifier is treat consistently by
    returning an upper-case version of the given string if it is not
    double-quoted, otherwise it return the string itself.

    Example:
        >>> sql_identifier('foo')
        'FOO'
        >>> sql_identifier('"foo"')
        '"foo"'
    """
    if (
        not name
        or name == '"'
        or (len(name) > 1 and len((name[0] + name[-1]).strip('"')) & 1)
    ):
        raise IdentifierError("Invalid identifier: " + name)

    if name[0] == '"':
        return name

    return name.upper()


class RowWrapper(ABC):
    """Abstract wrapper class for cursor rows.

    The results returned from a query are plain tuples and therefore lack some
    information like, e.g., column names. A row wrapper allows to wrap the
    results from a cursor or individual rows around a Python object that
    carries extra information as required.
    """

    @staticmethod
    @abstractmethod
    def from_cursor(cursor) -> Generator[Any, None, None]:
        """Convert the rows of a cursor into richer Python objects.

        Subclasses must implement this method in order to instruct the
        :func:`Database.fetch_all` method on how to wrap the result from the
        cursor.

        Args:
            cursor (:class:`cx_Oracle.Cursor`): The cursor with the results
                ready to be fetched.

        Returns:
            generator: the wrapped rows.
        """
        ...

    @staticmethod
    @abstractmethod
    def from_list(cursor, data: list) -> list:
        """Convert the elements in the data list into richer Python objects.

        Subclasses must implement htis method in order to instruct the
        `fetch_many` method on how to wrap the results in the data list.

        Args:
            cursor (:class:`cx_Oracle.Cursor`): The cursor used to obtain the
                `data`.
            data (``list``): The list of rows obtained from the given `cursor`.

        Returns:
            ``list``: the wrapped rows.
        """
        ...


class CursorRow(RowWrapper):
    """
    Turn a row of data into a dictionary/list-like object.

    This default implementation of the :class:`RowWrapper` abstract base class
    allows accessing row values both as attributes as well as tuple entries.

    For example, if a query returns the tuple ``(10, None, "Hello")`` and the
    corresponding columns are named ``A``, ``B`` and ``C``, by wrapping it with
    :class:`CursorRow` you get an object ``row`` that gives you the attributes
    ``a``/``A``, ``b``/``B`` and ``c``/``C`` for which ``row.a = row[0]``,
    ``row.B = row[1]`` and ``row.c = row[2]``.
    """

    @staticmethod
    def from_cursor(cursor):
        columns = [c[0] for c in cursor.description]
        for row in cursor:
            yield CursorRow(cursor, row, columns)

    @staticmethod
    def from_list(cursor, data):
        columns = [c[0] for c in cursor.description]
        return [CursorRow(cursor, row, columns) for row in data]

    def __init__(self, cursor, row, columns=None):
        """CursorRow constructor.

        For performance reasons, an optional ``columns`` argument can be
        provided so that the column names can be determined from the cursor
        only once and reused for every element in the collection that is to be
        wrapped.
        """
        columns = columns or [c[0] for c in cursor.description]

        if type(columns) not in (list, tuple) \
                or type(row) not in (list, tuple) \
                or len(columns) != len(row):

            if not row:
                raise CursorRowError("Invalid row values.")

            raise CursorRowError("Columns-values mismatch.")

        self._cols = columns
        self._state = dict(list(zip(columns, row)))
        self._max_col_len = None
        self._values = row

    def __getattr__(self, name):
        return self.__dict__["_state"][sql_identifier(name)]

    def __getitem__(self, i: int):
        return self._state[self._cols[i]]

    def __repr__(self):
        if self._max_col_len is None:
            self._max_col_len = max([len(c) for c in self._cols])

        return "\n".join([
            ("{:"+str(self._max_col_len)+"} : ").format(c)+str(self._state[c])
            for c in self._cols
        ])

    def __dir__(self):
        return self._cols

    @property
    def __raw__(self):
        return self._values


# -----------------------------------------------------------------------------


from sibilla.object import ObjectLookup, ObjectType


class Database(cx_Oracle.Connection):
    """The Database class.

    A subclass of the DB API specification-compliant cx_Oracle.Connection
    object, extended with additional features of Oracle Databases.

    Objects of this kind identify the database connection with the database
    itself. This is because the :class:`Database` class offers the capability
    of accessing Oracle stored object in a Pythonic way. Typical examples are
    data access from tables and views, which would normally require the user to
    embed "alien" SQL queries in Python code. The same would be true if the
    user wishes to call a stored function or procedure. Traditionally, this
    would be done by writing a block of PL/SQL code or via the
    :func:`cx_Oracle.Cursor.callfunc` and :func:`cx_Oracle.Cursor.callproc`
    methods. Sibilla allows you to call them as if they were plain Python
    methods of any :class:`Database` instance.

    Example:
        To create an Database instance, import :class:`Database` from
        ``sibilla`` and pass ``username``, ``password`` and ``dsn`` to it (plus
        any other optional argument accepted by the constructor of
        :class:`cx_Oracle.Connection`):

            >>> from sibilla import Database
            >>> db = Database(username, password, dsn=TNS)

    The :class:`Database` class offers a built-in look-up for Oracle objects,
    like Tables, Views, Functions, Procedures and Packages.

    Example:
        To create a reference to a table called ``COUNTRY`` in the Oracle
        database, access the attribute ``country`` from the ``Database``
        instance:

            >>> db.country
            <table 'COUNTRY'>

    A table is a special instance of a :class:`sibilla.dataset.DataSet` object,
    which allows you to perform basic SQL queries in a Pythonic way, without
    writing a single line of SQL code. See the sections on
    :class:`siblla.dataset.DataSet` and :class:`sibilla.table.Table` for more
    details.

    In a similar way one can access stored `functions`, `procedures` and
    `packages`. For functions and procedures stored in a package, the code will
    try to figure out whether the sought object is a function or a procedure.
    When there are overloaded objects that cannot be resolved, one can
    explicitly call a procedure or a function by accessing the ``proc`` and
    ``func`` attributes of a :class:`sibilla.package.Package` instance.

    Example:
        Assume that the database has a stored package called ``foo`` containing
        (overloaded) procedures and functions named ``bar``. To get
        ``foo.bar`` as a procedure one has to use:

            >>> db.foo.proc.bar
            <procedure 'BAR' from <package 'FOO'>>

        Similarly, to get bar as a function,

            >>> db.foo.func.bar
            <function 'BAR' from <package 'FOO'>>

        When there are no ambiguities like in the previous case (e.g. there are
        only functions or only procedures named ``bar``), one can simply use

            >>> db.foo.bar

        One can then call stored functions and procedures as normal Python
        functions/methods, using both positional and keyword arguments.

            >>> db.foo.bar(42)
            'The answer is 42. So long and thanks for all the fish!'
    """

    class Scope(type):
        """Oracle Data Dictionary scopes.

        This type is used to specify which scope the database look-up must use
        when looking up stored objects. Choose between ``ALL``, ``DBA`` and
        ``USER``. For more details on the meaning of these scopes, please refer
        to the Oracle documentation.

        The ``ALL`` scope is set by default. However, if you do not make use
        of many objects from different schema other than the current one,
        consider using the ``USER`` scope instead. This will make object
        look-ups faster as the search is restricted to a smaller view.
        """

        ALL = "all"
        DBA = "dba"
        USER = "user"

    __scope__ = Scope.ALL

    __row_wrapper__ = CursorRow

    def __init__(self, *args, **kwargs):
        """``Database`` constructor.

        The arguments are the same as those required by the
        :class:`cx_Oracle.Connection` class. The :class:`Database` is
        initialised with a default instance of
        :class:`sibilla.object.ObjectLookup`, which is at the heart of the
        stored object look-up. Previously retrieved objects are normally cached
        for faster access and the cache is exposed with the ``cache``
        attribute. The user is in charge of `flushing` caches when objects in
        the database change and the new state is to be retrieved. For more
        details about cache objects see :class:`sibilla.caching.Cached`.

        The initialisation is completed with a call to
        ``SYS.DBMS_OUTPUT.ENABLE`` so that any text output generated with calls
        to, e.g. ``SYS.DBMS_OUTPUT.PUT_LINE`` can be retrieved with the
        ``get_output`` method.
        """
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

        self._default_lookup = ObjectLookup(self)
        self.cache = self._default_lookup.cache

        # Enable standard streams
        self.dbms_output.enable()

    def __getattr__(self, name):
        return getattr(self.__lookup__, name, None)

    def get_errors(self, name: str=None, type: str=None) -> list:
        """Get Oracle errors.

        Retrieves all the current errors for the logged user. Internally, this
        method performs a query on the inner join between ``USER_ERRORS`` and
        ``USER_SOURCES``. The result is a collection of records with the fields
        ``name``, ``type``, ``line``, ``position``, ``error`` and ``text``.

        Args:
            name (str): Filter errors by object name. A pattern can be used
                (case sensitive)
            type (str): Filter errors by object type. A pattern can be used
                (case insensitive)

        Returns:
            `list`: a list of CursorRow objects describing all the requested
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
            order by name asc, type asc, sequence asc
            """.format(
                where=(
                    "where " + " and ".join(where_list)) if where_list else ""
                )
            )

    def get_output(self) -> str:
        """Get the output from the standard output stream buffer."""
        buf = self.var('STRING')
        status = self.var('NUMBER')
        text = ""

        while True:
            self.sys.dbms_output.get_line(buf, status)
            if int(status.getvalue()) > 0:
                break  # Nothing left to read
            line = buf.getvalue()
            if line is not None:
                text += line
            text += "\n"
        return text

    def fetch_one(self, stmt: str, *args, **kwargs) -> Any:
        """Fetch a single row from the execution of the provided statement.

        Bind variables can be provided both as positional and as keyword
        arguments to this method.

        Args:
            stmt (str): The statement to execute.
            *args: Variable length argument list for positional bind variables.
            **kwargs: Arbitrary keyword arguments for named bind variables.

        Returns:
            `object`: An instance of the ``__row_rapper__`` class if not
                ``None`` or `tuple` otherwise.
        """
        cursor = self.plsql(stmt, *args, **kwargs)
        res = cursor.fetchone()

        if not self.__row_wrapper__:
            return res

        return self.__row_wrapper__(cursor, res) if res else None


    def fetch_all(self, stmt: str, *args, **kwargs) -> Generator[Any, None, None]:
        """Fetch all rows from the execution of the provided statement.

        Bind variables can be provided both as positional and as keyword
        arguments to this method.

        Args:
            stmt (str): The statement to execute.
            *args: Variable length argument list for positional bind variables.
            **kwargs: Arbitrary keyword arguments for named bind variables.

        Returns:
            `generator`: A collection of all the records returned by the
                provided statement, either wrapped in ``__row_wrapper__`` if
                not ``None`` or as ``tuple`` s otherwise.
        """
        cursor = self.plsql(stmt, *args, **kwargs)

        if not self.__row_wrapper__:
            return cursor

        return self.__row_wrapper__.from_cursor(cursor)

    def _fetch_many(self, stmt: str, n: int, *args, **kwargs) -> tuple:
        # Required to break cyclic dependencies leading to infinite recursion.
        cursor = self.plsql(stmt, *args, **kwargs)
        return cursor, cursor.fetchmany(n)

    def fetch_many(self, stmt: str, n: int, *args, **kwargs) -> list:
        """Fetch (at most) `n` rows from the given query.

        The number of raws returned as a list by this function is at most ``n``
        for each call made.

        Args:
            stmt (str): The statement to execute.
            n (int): The number of rows to fetch.
            *args: Variable length argument list for positional bind variables.
            **kwargs: Arbitrary keyword arguments for named bind variables.

        Returns:
            `list`: A list of at most n records returned by the provided
            statement, either wrapped in ``__row_wrapper__`` if not ``None`` or
            as ``tuple`` s otherwise.
        """
        cursor, data = self._fetch_many(stmt, n, *args, **kwargs)

        if not self.__row_wrapper__:
            return data

        return self.__row_wrapper__.from_list(cursor, data)

    # TODO: Batch execute: https://blogs.oracle.com/opal/efficient-and-scalable-batch-statement-execution-in-python-cx_oracle
    def plsql(self, stmt: str, *args, batch: list=None, **kwargs):
        """Execute (PL/)SQL code.

        Bind variables can be provided both as positional and as keyword
        arguments to this method. Returns a cursor in case data needs to be
        fetched out of it.

        If the provided statement is to be executed multiple times but with
        different values, the ``batch`` argument should be used instead of
        implementing a loop in Python in order to improve performance.

        Args:
            stmt (str): The (PL/)SQL statement to execute.
            *args: Variable length argument list for positional bind variables.
            batch (list): A list of bind variables in the form of tuples to
                use iteratively with the given (PL/)SQL statement.
            **kwargs: Arbitrary keyword arguments for named bind variables.

        Returns:
            :class:`cx_Oracle.Cursor`: the cursor associated with the code
                execution.
        """
        c = 0
        c += 1 if args else 0
        c += 1 if kwargs else 0
        c += 1 if batch else 0
        if c > 1:
            raise DatabaseError(
                "Expecting either positional argument or keyword arguments or "
                "batch."
            )

        try:
            cursor = self.cursor()

            # TODO: executemany doesn't support generators yet.
            #       See https://github.com/oracle/python-cx_Oracle/issues/200
            if batch:
                cursor.executemany(stmt, batch)
            elif kwargs:
                cursor.execute(stmt, **kwargs)
            else:
                cursor.execute(stmt, args)

            return cursor

        except cx_Oracle.DatabaseError as e:
            raise DatabaseError(e) from e

    def set_scope(self, scope):
        """Set the Oracle Data Dictionary scope.

        Use one of the ``Database.Scope`` attributes. By default, a
        ``Database`` instance is created with the ``Database.Scope.ALL`` scope.
        For applications that rely mostly or exclusively on the logged user
        schema, it is recommended that the scope be set to
        ``Database.Scope.USER`` for better performance.
        """

        self.__scope__ = scope

    def set_row_wrapper(self, wrapper):
        """Set the row wrapper class.

        This class is used to wrap the raw rows returned by a SQL query around
        richer Python objects. See :class:`RowWrapper` for more details.
        """
        self.__row_wrapper__ = wrapper

    # TODO: This can use Function._Function__datatype_mapping to map python
    #       types to Oracle types.
    def var(self, var_type):
        """Create a PL/SQL variable reference.

        One can either pass the name of the variable type as defined in the
        ``cx_Oracle`` package (e.g. `STRING`), or pass the type itself (e.g.
        ``cx_Oracle.STRING``).

        Args:
            var_type: The type of the variable to create.

        Returns:
            `object`: The requested variable reference.
        """
        cur = self.cursor()
        return cur.var(
            getattr(cx_Oracle, var_type.upper()) if isinstance(var_type, str)
            else var_type
        )

    def commit(self, flush_cache=True):
        super().commit()

        if flush_cache:
            self.cache.flush()

    # ---- Properties ---------------------------------------------------------

    @property
    def session_user(self):
        """Returns the session user for the connection."""
        return self.fetch_one(
            "select sys_context('userenv', 'session_user') from dual"
        )[0]

    @session_user.setter
    def session_user(self, value):
        raise AttributeError("'session_user' is read-only.")

    @property
    def __lookup__(self):
        """Internal ``ObjectLookup`` for object discovery.

        The default classes can be overridden with a call to the
        :method:`sibilla.object.ObjectLookup.replace` method to handle custom
        behaviour that best reflect the database design. See the section
        dedicated to  the :class:`sibilla.object.ObjectLookup`` class for
        examples.
        """

        return self._default_lookup

    @__lookup__.setter
    def __lookup__(self, value):
        raise AttributeError("'__lookup__' is a read-only property.")
