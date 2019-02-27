import pytest

from sibilla import ConnectionError, Database, LoginError, DatabaseError
from sibilla.object import ObjectLookupError
from sibilla.table import PrimaryKeyError, TableError, TableEntryError, TableInsertError, Table

USER = "g"
PASSWORD = "g"


class TestTable:

    @classmethod
    def setup_class(cls):
        cls.db = Database(USER, PASSWORD, "XE", events=True)

    def test_base_class(self):
        with pytest.raises(TableError):
            Table(self.db)

    def test_cols(self):
        assert self.db.students.__cols__ == [
            'no', 'surname', 'forename'
        ]

    def test_pk(self):
        assert self.db.students.__pk__ == ["NO"]
        assert not self.db.marks.__pk__

    def test_fk(self):
        assert self.db.marks.__fk__ == {
            'module_code': 'modules',
            'student_no': 'students',
        }

    def test_iter(self):
        assert len(list(self.db.students.__iter__())) == 5

    def test_fetch_all(self):
        result = self.db.marks.fetch_all(
            select=["module_code", "mark"],
            where=[
                ({
                    'student_no': ':student',
                    'module_code': ':module'
                },),
                {
                    'student_no' : ':other_student'
                }
            ],
            student="20060101",
            module="CM0003",
            other_student="20060105"
        )

        assert len(list(result)) == 4

        assert not list(self.db.marks.fetch_all(where="1=0"))

        with pytest.raises(TableError):
            self.db.marks.fetch_all(
                select=["module_code", "mark"],
                where={
                    'student_no': ':student',
                    'module_code': ':module'
                },
                student="20060101",
                module="CM0003",
            )

    def test_fetch_one(self):
        assert self.db.marks.fetch_one(
            where=({
                'student_no': ':student',
                'module_code': ':module'
            },),
            student="20060101",
            module="CM0003",
        ).module_code == "CM0003"

        assert not self.db.marks.fetch_one(where="1=0")

    def test_call(self):
        assert self.db.students("20060105")

        assert self.db.students() == self.db.students

        with pytest.raises(TableEntryError):
            self.db.students("20060105", surname="name")

        with pytest.raises(PrimaryKeyError):
            self.db.students([1, 2])

        with pytest.raises(PrimaryKeyError):
            self.db.students("20060155")

        with pytest.raises(PrimaryKeyError):
            self.db.marks("no_pk")

    def test_describe(self):
        assert len(self.db.students.describe()) == 3

    def test_table_dml(self):
        try:
            self.db.drop_me.drop()
        except DatabaseError:
            pass

        self.db.plsql("create table drop_me(no varchar(10), aye number(1))")

        # ---- Test inserts ----
        self.db.drop_me.insert(('a', 0))
        self.db.drop_me.insert({'no': 'test'})

        with pytest.raises(TableInsertError):
            self.db.drop_me.insert("nonsense")

        with pytest.raises(TableInsertError):
            self.db.drop_me.insert(("too short", ))

        with pytest.raises(TableInsertError):
            self.db.drop_me.insert({'answer': 42})

        assert len(list(self.db.drop_me)) == 2

        # ---- Test truncate ----
        self.db.drop_me.truncate()
        assert len(list(self.db.drop_me)) == 0

        # ---- Test drop ----
        with pytest.raises(ObjectLookupError):
            self.db.drop_me.drop()
            self.db.drop_me
