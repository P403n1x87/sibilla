import pytest

from sibilla import Database
from sibilla.dataset import rowattribute
from sibilla.object import ObjectLookupError, ObjectTypeError
from sibilla.table import Table

USER = "g"
PASSWORD = "g"

class Modules(Table):

    __table__ = "MODULES"

    @rowattribute
    def description(row):
        return row.code + ": " + row.name


class TestObject:

    @classmethod
    def setup_class(cls):
        cls.db = Database(USER, PASSWORD, "XE", events=True)

        cls.db.plsql("""
            create procedure user_tables is begin null; end;
        """)

    def teardown_class(cls):
        cls.db.plsql("drop procedure user_tables")

    def test_object(self):
        assert self.db.all_objects

    def test_no_such_object(self):
        with pytest.raises(ObjectLookupError):
            self.db.no_such_object

    def test_multiple_objects(self):
        with pytest.raises(ObjectLookupError):
            self.db.user_tables

    def test_custom_table(self):
        self.db.__lookup__.replace({"modules": Modules})
        self.db.cache.flush()

        assert self.db.modules["CM0004"].description == 'CM0004: Graphics'

    def test_scope(self):
        self.db.set_scope(Database.Scope.USER)
        self.db.cache.flush()
        self.db.callable_package
        with pytest.raises(ObjectLookupError):
            self.db.dbms_output

    def test_unsupported_types(self):
        with pytest.raises(ObjectTypeError):
            self.db.test_sequence
