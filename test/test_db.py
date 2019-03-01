import pytest

from sibilla import ConnectionError, Database, LoginError, DatabaseError
from sibilla import CursorRow, CursorRowError
from sibilla import sql_identifier, IdentifierError


USER = "g"
PASSWORD = "g"


class TestDB:

    @classmethod
    def setup_class(cls):
        cls.db = Database(USER, PASSWORD, "XE", events=True)

    @classmethod
    def teardown_class(cls):
        if cls.db:
            cls.db.close()

    def test_connection_user(self):
        assert self.db.session_user.lower() == USER
        with pytest.raises(AttributeError):
            self.db.session_user = "gab"
        with pytest.raises(AttributeError):
            self.db.__lookup__ = None

    def test_output(self):
        self.db.dbms_output.put_line("Hello World!")
        assert self.db.get_output() == "Hello World!\n"

    def test_fetch(self):
        res = self.db.fetch_one("""
            select procedure_name
            from   all_procedures
            where  object_name    = :obj_name
               and procedure_name = :proc_name
            """, obj_name = "DBMS_OUTPUT", proc_name = "PUT_LINE")
        assert repr(res) == "PROCEDURE_NAME : PUT_LINE"
        assert res[0] == "PUT_LINE"

        res = self.db.fetch_one("""
            select procedure_name
            from   all_procedures
            where  object_name    = :obj_name
               and procedure_name = :proc_name
            """, "DBMS_OUTPUT", "PUT_LINE")

        assert res.proceDure_name == "PUT_LINE"
        assert res[0] == "PUT_LINE"
        assert dir(res) == ["PROCEDURE_NAME"]

        res = self.db.fetch_all("""
            select procedure_name
            from   all_procedures
            where  object_name = :obj_name
        """, "DBMS_OUTPUT")
        assert len(list(res)) > 1

        res = self.db.fetch_many("""
            select procedure_name
            from   all_procedures
            where  object_name = :obj_name
        """, 4, "DBMS_OUTPUT")
        assert len(res) == 4

    def test_plsql(self):
        self.db.plsql(
            "begin dbms_output.put_line(:msg); end;",
            msg='Hello PLSQL'
        )
        assert self.db.get_output()

        with pytest.raises(DatabaseError):
            self.db.plsql("select sysdate from dual", 10, a=20)

    def test_get_errors(self):
        self.db.plsql("""
            create or replace procedure with_errors
            is
            begin
                invalid_identifier;
            end;
        """)
        errors = list(self.db.get_errors(name='%', type='%'))
        assert len(errors) == 2

        error = errors[0]
        assert error.type == "PROCEDURE"
        assert "invalid_identifier" in error.error.lower()

        self.db.plsql("drop procedure with_errors")
        assert not list(self.db.get_errors())

    def test_sql_indentifier(self):
        assert sql_identifier("caseInsensitive") == "CASEINSENSITIVE"
        assert sql_identifier('"CaseSensitive"') == '"CaseSensitive"'
        with pytest.raises(IdentifierError):
            sql_identifier('"Invalid')
        with pytest.raises(IdentifierError):
            sql_identifier('Invalid"')
        with pytest.raises(IdentifierError):
            sql_identifier('"')
        with pytest.raises(IdentifierError):
            sql_identifier('')


    def test_cursor_row(self):
        with pytest.raises(CursorRowError):
            CursorRow(("Col",), None)

        with pytest.raises(CursorRowError):
            CursorRow(("Col", ), (12, 10))

    def test_db_login_error(self):
        with pytest.raises(LoginError):
            Database("invalid", "user", "XE")

    def test_db_connection_error(self):
        with pytest.raises(DatabaseError):
            Database(USER, PASSWORD, "XE", mode=-100)
        with pytest.raises(ConnectionError):
            Database(USER, PASSWORD, "EX")
