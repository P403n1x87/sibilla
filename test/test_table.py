import pytest

from sibilla import ConnectionError, Database, DatabaseError, LoginError
from sibilla.dataset import QueryError
from sibilla.object import ObjectLookupError
from sibilla.table import (PrimaryKeyError, Table, TableEntryError, TableError,
                           TableInsertError)

USER = "g"
PASSWORD = "g"


class TestTable:

    @classmethod
    def setup_class(cls):
        cls.db = Database(USER, PASSWORD, "XE", events=True)

        cls.db.plsql("""
            create table test_slice(
                id number(9),
                constraint id#p primary key (id)
            )
        """)

    @classmethod
    def teardown_class(cls):
        cls.db.test_slice.drop()

    def test_base_class(self):
        with pytest.raises(TableError):
            Table(self.db)

    def test_cols(self):
        assert self.db.students.__cols__ == [
            'NO', 'SURNAME', 'FORENAME'
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
                    'student_no': "20060101",
                    'module_code': "CM0003"
                },),
                {
                    'student_no': "20060105"
                }
            ],
        )

        assert len(list(result)) == 4

        assert not list(self.db.marks.fetch_all(where="1=0"))

        with pytest.raises(QueryError):
            self.db.marks.fetch_all(
                select=["module_code", "mark"],
                where={
                    'student_no': "20060101",
                    'module_code': "CM0003"
                },
            )

    def test_fetch_one(self):
        assert self.db.marks.fetch_one(
            where=({
                'student_no': "20060101",
                'module_code': "CM0003"
            },),
        ).module_code.code == "CM0003"

        assert not self.db.marks.fetch_one(where="1=0")

        assert self.db.marks.fetch_one(
            student_no="20060101",
            module_code="CM0003"
        ).module_code.code == "CM0003"

    def test_fetch_many(self):
        assert len(self.db.marks.fetch_many(
            2,
            where=({
                'student_no': "20060101",
                'module_code': "CM0003"
            },),
        )) == 1

    def test_call(self):
        assert self.db.students() == self.db.students
        assert len(list(self.db.marks(module_code="CM0003"))) == 3

    def test_pk(self):
        assert self.db.students["20060105"]

        with pytest.raises(PrimaryKeyError):
            self.db.students[[1, 2]]

        with pytest.raises(PrimaryKeyError):
            self.db.students["20060155"]

        with pytest.raises(PrimaryKeyError):
            self.db.marks["no_pk"]

        self.db.test_slice.insert([(i,) for i in range(20)])

        rows = list(self.db.test_slice[16:4:-2])
        assert len(rows) == 6

        j = 0
        for i in range(16, 4, -2):
            assert rows[j].id == i
            j += 1

    def test_empty_insert(self):
        self.db.test_slice.insert([])
        self.db.test_slice.insert(tuple())
        self.db.test_slice.insert({})

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

        self.db.commit()

        # ---- Test truncate ----
        self.db.drop_me.truncate()
        assert len(list(self.db.drop_me)) == 0

        # ---- Test drop ----
        with pytest.raises(ObjectLookupError):
            self.db.drop_me.drop()
            self.db.drop_me
