from sibilla import DatabaseError

from sibilla.callable import CallableFactory
from sibilla.caching import Cached, cachedmethod
from sibilla.object import OracleObject, ObjectType
# from .record import Record, PLSQLRecordError

# ---- Exceptions -------------------------------------------------------------

class PackageAttributeError(DatabaseError):
    pass

# -----------------------------------------------------------------------------

class Package(OracleObject, Cached):

    __slots__ = []

    def __init__(self, db, name):
        super().__init__(db, name, ObjectType.PACKAGE)
        Cached.__init__(self)

        self.func = CallableFactory(
            self.db.__lookup__.get_class(ObjectType.FUNCTION),
            self
        )

        self.proc = CallableFactory(
            self.db.__lookup__.get_class(ObjectType.PROCEDURE),
            self
        )

    @cachedmethod
    def __getattr__(self, name):
        name = self.renaming(name)

        # No of procedures and functions
        tot = self.db.fetch_one("""
            select count(*)
            from   all_procedures
            where  object_name    = upper(:pkg_name)
               and procedure_name = upper(:name)
        """, name=name, pkg_name=self.name)[0]

        if not tot:
            # Look for records
            # try:
            #     return Record(self.db, "{}.{}".format(self.name, name))
            # except PLSQLRecordError:
            #     raise PackageAttributeError("No object '{}' within package '{}'".format(name, self.name))
            raise PackageAttributeError("No callable {} within {}".format(
                name, self
            ))

        # This reliably returns functions
        res = self.db.fetch_all("""
            select pls_type
            from   all_arguments
            where  object_name  = upper(:name)
               and package_name = upper(:pkg_name)
               and position     = 0
               and defaulted    = 'N'
        """, name=name, pkg_name=self.name)

        funcs = len(set(res))
        procs = tot - len(list(res))

        callable_class = self.db.__lookup__.get_class(
            ObjectType.FUNCTION if funcs else ObjectType.PROCEDURE
        )
        return callable_class(self.db, name, self)

    def __repr__(self):
        return "<package {}>".format(self.name.upper())
