import pytest

from sibilla import ConnectionError, Database, LoginError
from sibilla.object import ObjectType
from sibilla.package import PackageAttributeError
from sibilla.callable import CallableError


USER = "g"
PASSWORD = "g"

MESSAGE = "Hello World!"


class TestCallable:

    @classmethod
    def setup_class(cls):
        cls.db = Database(USER, PASSWORD, "XE", events=True)

    def test_stored_procedure(self):
        self.db.print(MESSAGE)
        assert MESSAGE in self.db.get_output()

        assert getattr(self.db, '"CamelCase"')

        def enquote(s):
            if s[0] == s[-1] == '_':
                return '"{}"'.format(s[1:-1])
            return s
        self.db.__lookup__.renaming = enquote

        assert self.db._CamelCase_

    def test_stored_function(self):
        assert self.db.len(MESSAGE) == len(MESSAGE)

        assert self.db.is_positive(10)
        assert not self.db.is_positive(0)

        assert self.db.negate(False)
        assert not self.db.negate(True)

        students = list(self.db.return_cursor())
        assert len(students) == 5
        assert len(students[0]) == 3

    def test_package_callable(self):
        assert not self.db.callable_package.is_negative(10)
        assert not self.db.callable_package.logic_and(True, False)

        self.db.callable_package.print(MESSAGE)
        assert MESSAGE in self.db.get_output()

        with pytest.raises(PackageAttributeError):
            self.db.callable_package.no_such_callable

    def test_package_callable_factory(self):
        self.db.dbms_output.proc.put_line(MESSAGE)
        assert MESSAGE in self.db.get_output()

        with pytest.raises(CallableError):
            self.db.callable_package.func.print

    def test_procedure_mixed_arguments(self):
        self.db.callable_package.mixed_arguments(10, "hello", True)
        assert self.db.get_output() == "10hellotrue\n"

    def test_function_return_type(self):
        assert self.db.is_positive.return_type == "BOOLEAN"

    def test_overloaded_function(self):
        overloaded_function = self.db.callable_package.ret_overloaded
        assert overloaded_function.return_type == {'VARCHAR2', 'BOOLEAN'}

        with pytest.raises(CallableError):
            overloaded_function(10)

        assert overloaded_function(a=-10, ret_type=bool)
        assert overloaded_function(b=-10, ret_type=str) == "-10"

        with pytest.raises(CallableError):
            assert overloaded_function(-10, ret_type=bool)

    def test_callable_repr(self):
        assert repr(self.db.dbms_output.put_line) == \
            "<procedure 'PUT_LINE' from <package 'DBMS_OUTPUT'>>"
