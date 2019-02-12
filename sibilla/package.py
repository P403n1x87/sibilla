from .oracle_object import *
from .record        import Record, PLSQLRecordError


#TODO: Might be Cached?
class CallableFactory(object):
    def __init__(self, db, pkg_name, call_type):
        self.__db = db
        self.__pkg_name = pkg_name
        self.__type = call_type

    def __getattr__(self, name):
        ret = self.__type(self.__db, '{}.{}'.format(self.__pkg_name, name))
        self.__dict__[name] = ret
        return ret


# -----------------------------------------------------------------------------


class PackageAttributeError(Exception):
    pass


#TODO: Might be Cached?
class Package(OracleObject):
    def __init__(self, db, name):
        super(Package, self).__init__(db, name, ObjectType.PACKAGE)

        self.func = CallableFactory(self.db, self.name, self.db.object_lookup.map(ObjectType.FUNCTION))
        self.proc = CallableFactory(self.db, self.name, self.db.object_lookup.map(ObjectType.PROCEDURE))

    def __getattr__(self, name):
        name = self.renaming(name)

        # No of procedures and functions
        tot = self.db.fetch_one("""
            select count(*)
            from   all_procedures
            where  object_name    = upper(:pkg_name)
               and procedure_name = upper(:name)""", name = name, pkg_name = self.name)[0]
        if tot == 0:
            # Look for records
            try:
                return Record(self.db, "{}.{}".format(self.name, name))
            except PLSQLRecordError:
                raise PackageAttributeError("No object '{}' within package '{}'".format(name, self.name))

        # This reliably returns functions
        res = self.db.fetch_all("""
            select pls_type
            from   all_arguments
            where  object_name  = upper(:name)
               and package_name = upper(:pkg_name)
               and position     = 0
               and defaulted    = 'N'""", name = name, pkg_name = self.name)

        funcs = len(set(res))
        procs = tot - len(list(res))

        ret = self.db.object_lookup.map(ObjectType.FUNCTION if funcs > 0 else ObjectType.PROCEDURE)(self.db, '{}.{}'.format(self.name, name))

        # TODO: Cache not under direct control
        self.__dict__[name] = ret

        return ret
