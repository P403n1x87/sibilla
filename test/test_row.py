import pytest

from sibilla import Database
from sibilla.row import RowAttributeError, MultipleRowsError, NoSuchRowError, SmartRow

USER = "g"
PASSWORD = "g"

STUDENT_NO = "20060105"


class TestRow:

    @classmethod
    def setup_class(cls):
        cls.db = Database(USER, PASSWORD, "XE", events=True)

    def test_row_errors(self):
        with pytest.raises(MultipleRowsError):
            self.db.marks(student_no=STUDENT_NO)

        with pytest.raises(NoSuchRowError):
            self.db.marks(student_no="NOSUCHSTUDENT")

    def test_row_fields(self):
        student = self.db.students(STUDENT_NO)

        assert student.no == STUDENT_NO

        with pytest.raises(RowAttributeError):
            self.db.students(STUDENT_NO).no_such_field

    def test_row_pk(self):
        student = self.db.students(STUDENT_NO)
        assert student.__pk__ == {'NO': '20060105'}

        assert self.db.marks(
            student_no=STUDENT_NO,
            module_code="CM0004"
        ).__pk__ is None

    def test_smart_row(self):
        self.db.cache.flush()

        from sibilla.table import Table
        Table.set_row_class(SmartRow)

        assert self.db.marks(
            student_no=STUDENT_NO,
            module_code="CM0004"
        ).student_no.no == STUDENT_NO
