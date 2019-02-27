import pytest

from sibilla import Database
from sibilla.object import ObjectLookupError

USER = "g"
PASSWORD = "g"

class TestObject:

    @classmethod
    def setup_class(cls):
        cls.db = Database(USER, PASSWORD, "XE", events=True)

        cls.db.plsql("""
            create procedure user_objects is begin null; end;
        """)

    def teardown_class(cls):
        cls.db.plsql("drop procedure user_objects")

    def test_object(self):
        assert self.db.all_objects

    def test_no_such_object(self):
        with pytest.raises(ObjectLookupError):
            self.db.no_such_object

    def test_multiple_objects(self):
        with pytest.raises(ObjectLookupError):
            self.db.user_objects
