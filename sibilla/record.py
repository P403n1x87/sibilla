from .oracle_object import OracleObject, ObjectType
from .datatypes     import mapping

class PLSQLRecordError(AttributeError):
    pass

class RecordInstance(dict):
    def __init__(self, rec_type):
        self.__dict__["_RecordInstance__type"] = rec_type
        for f in rec_type.fields:
            if rec_type.fields[f] in mapping:
                self[f] = rec_type.db.var(mapping[rec_type.fields[f]])
            else:
                self[f] = rec_type.fields[f]()

    def __getattr__(self, name):
        name = name.upper()

        if name not in self:
            raise PLSQLRecordError("No field named '{}' in record of type '{}'".format(name, self.__type.name))

        return self[name].getvalue() if hasattr(self[name], "getvalue") else self[name]

    def __setattr__(self, name, value):
        name = name.upper()
        if name not in self:
            raise PLSQLRecordError("No field named '{}' in record of type '{}'".format(name, self.__type.name))

        self[name].setvalue(0, value)

    def __set__(self, obj, value):
        """
        Implement this to handle nested arrays.
        """
        pass

    def __repr__(self):
        return "<instance of record type '{}'>".format(self.__type.name)

    def assign(self, dest):
        pass


    @property
    def type(self):
        return self.__type.name

class Record(OracleObject):
    """
    Wrapper around the *_IDENTIFIERS Oracle Data Dictionary
    """
    def __init__(self, db, name):
        super(Record, self).__init__(db, name, ObjectType.RECORD)
        self.pkg_name, self.rec_name = name.upper().split('.')

        fields_res = self.db.fetch_all("""
            select     name, type
            from       all_identifiers
            start with name        = :name
                   and type        = 'RECORD'
                   and object_name = :pkg_name
                   and usage       = 'DECLARATION'
            connect by prior usage_id    = usage_context_id
                   and prior object_name = object_name
                   and prior object_type = object_type
            order by   usage_id
            """, name = self.rec_name, pkg_name = self.pkg_name)[1:]

        if not fields_res:
            raise PLSQLRecordError("No record named '{}' within package '{}'".format(self.rec_name, self.pkg_name))

        fields = {}
        last_pkg = None
        for e in fields_res:
            if e[1] == 'VARIABLE':
                fields[e[0]] = None
                last_field = e[0]
            elif e[1] == "PACKAGE":
                last_pkg = e[0]
            elif e[1] == "RECORD":
                fields[last_field] = getattr(getattr(db, last_pkg if last_pkg != None else self.pkg_name), e[0])#["RECORD", "{}.{}".format(last_pkg if last_pkg != None else self.pkg_name, e[0])]
                last_pkg = None
            else:
                fields[last_field] = e[0]

        self.fields = fields

    def __call__(self, *args, **kwargs):
        """
        Instantiate a new record of the given type
        """

        return RecordInstance(self)

    def __repr__(self):
        return "<record type '{}'>".format(self.name)
