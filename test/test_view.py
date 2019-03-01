import pytest

from sibilla import Database
from sibilla.view import ViewError, View

USER = "g"
PASSWORD = "g"


class TestView:

    @classmethod
    def setup_class(cls):
        cls.db = Database(USER, PASSWORD, "XE", events=True)

    def test_view(self):
        assert repr(self.db.user_objects) == "<view 'USER_OBJECTS'>"

        self.db.user_objects(
            object_name="CALLABLE_PACKAGE",
            object_type="PACKAGE"
        )

    def test_base_class(self):
        with pytest.raises(ViewError):
            View(self.db)
