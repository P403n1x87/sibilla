import pytest

from sibilla import ConnectionError, Database, LoginError
from sibilla.table import PrimaryKeyError

USER = "g"
PASSWORD = "g"


class TestTable:

    @classmethod
    def setup_class(cls):
        cls.db = Database(USER, PASSWORD, "XE", events=True)

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

        with pytest.raises(PrimaryKeyError):
            self.db.students([1, 2])

        with pytest.raises(PrimaryKeyError):
            self.db.students("20060155")
