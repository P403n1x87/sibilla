import pytest

from pandas import DataFrame

from sibilla import CursorRow, Database
from sibilla.dataset import DataSet, Row, QueryError


USER = "g"
PASSWORD = "g"


class DataFrameWrapper(CursorRow):

    @staticmethod
    def from_cursor(cursor):
        return DataFrame.from_records(
            list(cursor),
            columns=[c[0] for c in cursor.description]
        )

    @staticmethod
    def from_list(cursor, data):
        return DataFrame.from_records(
            data,
            columns=[c[0] for c in cursor.description]
        )


class TestPandas:

    @classmethod
    def setup_class(cls):
        cls.db = Database(USER, PASSWORD, "XE", events=True)
        cls.db.set_row_wrapper(DataFrameWrapper)

    def teardown_class(cls):
        DataSet.set_row_class(Row)

    def test_row_with_data_frame(self):
        with pytest.raises(QueryError):
            assert isinstance(
                self.db.all_objects.fetch_many(2, owner="G"), DataFrame
            )

    def test_all_objects(self):
        DataSet.set_row_class(None)
        assert isinstance(self.db.all_objects.fetch_all(owner="G"), DataFrame)
