from sibilla import DatabaseError
from sibilla.object import ObjectType, OracleObject

# ---- Exceptions -------------------------------------------------------------


class ViewError(DatabaseError):
    """View-related database error."""
    pass

# -----------------------------------------------------------------------------


from sibilla.dataset import DataSet


class View(OracleObject, DataSet):

    __view__ = None

    def __init__(self, db, name=None, schema=None):
        name = name or self.__view__

        if name is None:
            raise ViewError("No view name given")
        super().__init__(db, name, ObjectType.VIEW, schema)
