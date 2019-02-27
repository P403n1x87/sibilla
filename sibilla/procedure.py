from sibilla.object import OracleObject, ObjectType
from .callable import Callable

class Procedure(OracleObject, Callable):
    def __init__(self, db, name):
        super(Procedure, self).__init__(db, name, ObjectType.PROCEDURE)

    def __call__(self, *args, **kwargs):
        cur = self.db.cursor()
        cur.callproc(self.name, args, kwargs)

    def __repr__(self):
        return "<procedure {}>".format(self.name)
