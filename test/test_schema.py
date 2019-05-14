import pytest

from sibilla import Database
from sibilla.object import ObjectLookupError
from sibilla.schema import Schema, SchemaError
from sibilla.procedure import Procedure
from sibilla.view import View


USER = "g"
PASSWORD = "g"

STUDENT_NO = "20060105"


class TestSchema:

    @classmethod
    def setup_class(cls):
        cls.db = Database(USER, PASSWORD, "XE", events=True)

    def test_no_schema(self):
        with pytest.raises(SchemaError):
            Schema(self.db, "noschema")

    def test_g_schema(self):
        assert Schema(self.db, "g").name == "G"

    def test_sys_schema(self):
        sys = self.db.sys
        assert isinstance(sys, Schema) and sys.name == "SYS"
        assert isinstance(sys.dbms_output.put_line, Procedure)

    def test_schema_in_user_scope(self):
        self.db.set_scope(Database.Scope.USER)
        self.db.cache.flush()

        with pytest.raises(ObjectLookupError):
            self.db.dbms_output

        assert isinstance(self.db.sys.dbms_output.put_line, Procedure)

        with pytest.raises(ObjectLookupError):
            self.db.all_users

        assert isinstance(self.db.sys.all_users, View)

        self.db.sys.dbms_output.put_line(STUDENT_NO)
        assert self.db.get_output()[:-1] == STUDENT_NO
