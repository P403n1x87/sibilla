from sibilla.object import OracleObject, ObjectType
from sibilla.callable import Callable


class Procedure(Callable):

    __slots__ = []

    def __init__(self, db, name, package=None):
        super().__init__(db, name, ObjectType.PROCEDURE, package)

    def __call__(self, *args, **kwargs):
        cur = self.db.cursor()
        cur.callproc(self.callable_name, args, kwargs)
