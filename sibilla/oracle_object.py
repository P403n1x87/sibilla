import cx_Oracle

from .cached import Cached

################################################################################

class ObjectType(object):
    TABLE           = "TABLE"
    VIEW            = "VIEW"
    ROW             = "ROW"
    PACKAGE         = "PACKAGE"
    PROCEDURE       = "PROCEDURE"
    FUNCTION        = "FUNCTION"
    RECORD          = "RECORD"

################################################################################

class OracleObject(object):
    def __init__(self, db, obj_name, obj_type):
        self.__db = db
        self.__name = self.renaming(obj_name)
        self.__type = obj_type

    def renaming(self, name):
        return name

    @property
    def db(self):
        return self.__db

    @property
    def name(self):
        return self.__name

    @property
    def ora_obj_type(self):
        return self.__type
