import pytest

from sibilla import Database
from sibilla.object import ObjectType
from sibilla.table import Table, SmartRow
from sibilla.dataset import rowmethod, rowattribute
from sibilla.dataset import RowAttributeError, MultipleRowsError, NoSuchRowError

USER = "g"
PASSWORD = "g"

STUDENT_NO = "20060105"


class CustomTable(Table):

    @rowattribute
    def first_column(row):
        return getattr(row, row.__dataset__.__cols__[0])

    @rowmethod
    def get_first_column(row):
        return row.first_column

    def __repr__(self):
        return "CustomTable({})".format(self.name)


class TestRow:

    @classmethod
    def setup_class(cls):
        cls.db = Database(USER, PASSWORD, "XE", events=True)

    def test_row_errors(self):
        with pytest.raises(MultipleRowsError):
            SmartRow(self.db.marks, {'student_no': STUDENT_NO})

    def test_row_db(self):
        assert self.db == self.db.students[STUDENT_NO].db

    def test_row_fields(self):
        student = self.db.students[STUDENT_NO]

        assert student.no == STUDENT_NO

        with pytest.raises(RowAttributeError):
            self.db.students[STUDENT_NO].no_such_field

    def test_row_pk(self):
        student = self.db.students[STUDENT_NO]
        assert student.__pk__ == {'NO': '20060105'}

        assert list(self.db.marks(
            student_no=STUDENT_NO,
            module_code="CM0004"
        ))[0].__pk__ is None

    def test_smart_row(self):
        self.db.cache.flush()

        Table.set_row_class(SmartRow)

        assert list(self.db.marks(
            student_no=STUDENT_NO,
            module_code="CM0004"
        ))[0].student_no.no == STUDENT_NO

    def test_row_decorators(self):
        self.db.__lookup__.replace({ObjectType.TABLE: CustomTable})
        self.db.cache.flush()

        student = self.db.students[STUDENT_NO]

        assert student.get_first_column() == STUDENT_NO
