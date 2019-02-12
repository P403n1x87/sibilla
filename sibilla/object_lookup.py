from .oracle_object import ObjectType

from .table         import Table
from .view          import View
from .row           import Row
from .procedure     import Procedure
from .function      import Function
from .package       import Package

from .cached        import Cached

_type_mapping = {
    ObjectType.TABLE                : Table
   ,ObjectType.VIEW                 : View
   ,ObjectType.ROW                  : Row
   ,ObjectType.PROCEDURE            : Procedure
   ,ObjectType.FUNCTION             : Function
   ,ObjectType.PACKAGE              : Package
}

### Exception ##################################################################

class DatabaseObjectError(Exception):
    """
    Defines an error specific to object lookup within the Oracle database
    associated to an OracleDB object.
    """
    pass

################################################################################

class ObjectLookup(Cached):
    """
    This class allows to customize the way objects (e.g. tables, views,
    packages, ...) are looked up from the Oracle database when accessed as
    attributes of an instance of this class.

    Every instance of OracleDB comes with a default ObjectLookup instance
    accessible through the read-only property ``object_lookup``. This can be
    used to specify the custom classes to handle general Oracle object, as well
    as specific items, like individual tables, packages, etc...

    Example:
        Assume that the database we are connected to has families of tables
        with a certain prefix, say ``DATA_``, that can be, in practice, treated
        as a namespace. One might want to be able to access such tables (e.g.
        the ``DATA_CUSTOMER`` table) with an attribute access on a OracleDB
        object as

            >>> from oracle import OracleDB
            >>> db = OracleDB("username", "password", "dsn")
            >>> db.data.customer

        This can be achieved in the following ways. First of all one subclasses
        ``ObjectLookup`` to create a custom lookup with an override of the
        ``renaming`` method

            from oracle import ObjectLookup

            class DataLookup(ObjectLookup):

                def renaming(self, name):
                    return "data_" + name

        The one either assigns a new instance of ``DataLookup`` to ``db.data``,

            >>> db.data = DataLookup()

        or one subclasses OracleDB and initializes ``data`` as an object
        attribute:

            >>> class MyDB(OracleDB):
            >>>     def __init__(self, *args, **kwargs):
            >>>         super(MyDB, self).__init__(*args, **kwargs)
            >>>         self.data = DataLookup(self)
            >>>
            >>> db = MyDB("username", "password", "dsn")

        Thus, ``db.data.customer`` becomes equivalent to ``db.data_customer``.

        By default, the lookup will create an object of type ``Table`` from
        ``oracle`` for the table accessed as ``db.data_customer``. To override
        this, one can subclass ``Table`` and pass the class to the ``replace``
        method as dictionary:

            >>> from oracle import ObjectType, Table
            >>> MyTable(Table):
            >>>     pass
            >>>
            >>> db.object_lookup.replace({ObjectType.TABLE : MyTable})

        Custom table classes can also be assigned to general attributes of an
        OracleDB object by passing the attribute name as key in the dictionary:

            >>> db.object_lookup.replace({"customer" : MyTable})

        This way, the custom table class ``MyTable`` is used only when accessing
        the attribite ``customer`` from ``db`` rather than for every table.
        Observe that this is NOT the same as assigning ``MyTable`` directly to
        the attribute ``customer`` of ``db``.
    """
    __custom_objects__ = {}

    def __init__(self, db):
        super(ObjectLookup, self).__init__()

        self.__db = db

    def renaming(self, name):
        """
        This methods offers an interface to easy customization of subclasses.
        Any attribute accessed on an ObjectLookup object is preprocessed by
        this method. This can be useful when database objects have characters
        which are not allowed in Python to appear in identifiers. For example,
        ``my_package#`` is a valid Oracle package name, however
        ``db.my_package#`` does not produce the desired result in Python. To
        overcome this situation one can subclass ObjectLookup with an
        overridden method ``name`` that does a suitable conversion.

        Example:
            To access the Oracle package ``my_package#`` from Python, one could
            use the convention of replacing any occurrence of # with __.

                >>> from oracle import ObjectLookup
                >>> class MyLookup(ObjectLookup):
                >>>     def renaming(self, name):
                >>>         return name.replace('__', '#')

            Any access to the attribute ``my_package__`` from a ``MyLookup``
            object is translated into ``my_package#`` before being actually
            looked up from the database.

        Args:
            name (str): The attribute accessed on an instance of the class.

        Returns:
            str: The translated attribute for lookup on the database.
        """

        return name

    def __getattr__(self, name):
        name = self.renaming(name)

        # Try to hit the cache
        ret = self.get_cached(name)
        if ret != None:
            return ret

        # Look through custom objects first
        if type(self).__custom_objects__ and name in list(type(self).__custom_objects__.keys()):
            obj_cls = type(self).__custom_objects__[name]

        else: # Return standard object
            # TODO: Uniqueness check needed!
            obj_type = self.__db.fetch_one(
                """
                select object_type
                from   all_objects
                where  object_name     = upper(:obj_name)
                   and object_type    != 'SYNONYM'
                   and subobject_name is null
                """, obj_name = name)

            if obj_type is None:
                raise DatabaseObjectError("No object named '{}' in the database".format(name))
            obj_cls = self.map(obj_type[0])

        ret = obj_cls(self.__db, name)

        # Cache the restult
        self.cache(name, ret)
        return ret

    @classmethod
    def map(cls, type_name):
        """
        Returns the class associated with the given type or attribute.

        Args:
            type_name (str): The type name to map. This is meant to be either
                one of the values exposed by the ``ObjectType`` class, or a
                custom attribute.


        Returns:
            class: The class associated with the given type/attribute.
        """

        try:
            return cls.__custom_objects__[type_name] if type_name in cls.__custom_objects__ else _type_mapping[type_name]
        except KeyError:
            raise TypeError('Unhandled request for object type "{}".'.format(type_name))

    @classmethod
    def replace(cls, types):
        """
        Overrides the classes used to handle types/attributes on the lookup
        instance.

        Args:
            types (dict): A dictionary of key-value pairs where the key
                indicates the type/attribute and the value the class to use
                to handle the specified type/attribute. The standard Oracle
                object types can be overridden by using the constants exposed
                by the ``ObjectType`` class as key values.
        """

        cls.__custom_objects__.update(types)
