import sibilla

from sibilla.caching import Cached, cachedmethod


class ObjectType(type):
    TABLE           = "TABLE"
    VIEW            = "VIEW"
    PACKAGE         = "PACKAGE"
    PROCEDURE       = "PROCEDURE"
    FUNCTION        = "FUNCTION"
    RECORD          = "RECORD"


class OracleObject:
    def __init__(self, db, object_name, object_type):
        self.__db = db
        self.__name = sibilla.sql_identifier(self.renaming(object_name))
        self.__type = object_type

    def renaming(self, name):
        return name

    @property
    def db(self):
        return self.__db

    @property
    def name(self):
        return self.__name

    @property
    def object_type(self):
        return self.__type

    def __repr__(self):
        return "<{} '{}'>".format(self.__type.lower(), self.__name)

### Exception ##################################################################

class ObjectError(sibilla.DatabaseError):
    """
    Defines an error specific to object lookup within the Oracle database
    associated to an Database object.
    """
    pass


class ObjectLookupError(ObjectError):
    """Raised when an object lookup fails."""
    pass


class ObjectTypeError(ObjectError):
    """Problems with Oracle object types."""
    pass


from sibilla.table import Table
from sibilla.view import View
from sibilla.procedure import Procedure
from sibilla.function import Function
from sibilla.package import Package

_type_mapping = {
    ObjectType.TABLE                : Table
   ,ObjectType.VIEW                 : View
   ,ObjectType.PROCEDURE            : Procedure
   ,ObjectType.FUNCTION             : Function
   ,ObjectType.PACKAGE              : Package
}

# -----------------------------------------------------------------------------

class ObjectLookup(Cached):
    """
    This class allows to customize the way objects (e.g. tables, views,
    packages, ...) are looked up from the Oracle database when accessed as
    attributes of an instance of this class.

    Every instance of Database comes with a default ObjectLookup instance
    accessible through the read-only property ``__lookup__``. This can be
    used to specify the custom classes to handle general Oracle object, as well
    as specific items, like individual tables, packages, etc...

    Example:
        Assume that the database we are connected to has families of tables
        with a certain prefix, say ``DATA_``, that can be, in practice, treated
        as a namespace. One might want to be able to access such tables (e.g.
        the ``DATA_CUSTOMER`` table) with an attribute access on a Database
        object as

            >>> from sibilla import Database
            >>> db = Database("username", "password", "dsn")
            >>> db.data.customer

        This can be achieved in the following ways. First of all one subclasses
        ``ObjectLookup`` to create a custom lookup with an override of the
        ``renaming`` method

            from sibilla import ObjectLookup

            class DataLookup(ObjectLookup):

                def renaming(self, name):
                    return "data_" + name

        The one either assigns a new instance of ``DataLookup`` to ``db.data``,

            >>> db.data = DataLookup()

        or one subclasses Database and initializes ``data`` as an object
        attribute:

            >>> class MyDB(Database):
            >>>     def __init__(self, *args, **kwargs):
            >>>         super(MyDB, self).__init__(*args, **kwargs)
            >>>         self.data = DataLookup(self)
            >>>
            >>> db = MyDB("username", "password", "dsn")

        Thus, ``db.data.customer`` becomes equivalent to ``db.data_customer``.

        By default, the lookup will create an object of type ``Table`` from
        ``sibilla`` for the table accessed as ``db.data_customer``. To override
        this, one can subclass ``Table`` and pass the class to the ``replace``
        method as dictionary:

            >>> from sibilla import ObjectType, Table
            >>> MyTable(Table):
            >>>     pass
            >>>
            >>> db.__lookup__.replace({ObjectType.TABLE : MyTable})

        Custom table classes can also be assigned to general attributes of an
        Database object by passing the attribute name as key in the dictionary:

            >>> db.__lookup__.replace({"customer" : MyTable})

        This way, the custom table class ``MyTable`` is used only when accessing
        the attribite ``customer`` from ``db`` rather than for every table.
        Observe that this is NOT the same as assigning ``MyTable`` directly to
        the attribute ``customer`` of ``db``.
    """
    __custom_objects__ = {}

    def __init__(self, db):
        super().__init__()

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

                >>> from sibilla import ObjectLookup
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

    @cachedmethod
    def __getattr__(self, name):
        name = sibilla.sql_identifier(self.renaming(name)).strip('"')

        # Look through custom objects first
        try:
            object_class = self.__custom_objects__[name]

        except KeyError: # Return standard object
            object_type = self.__db.fetch_many(
                """
                select object_type
                from   {}_objects
                where  object_name = :object_name
                   and object_type not in ('SYNONYM', 'PACKAGE BODY')
                   and subobject_name is null
                """.format(self.__db.__scope__),
                n=2,
                object_name=name
            )

            if not object_type:
                raise ObjectLookupError("No such object: '{}'".format(name))

            if len(object_type) != 1:
                # TODO: handle with disambiguator?
                raise ObjectLookupError(
                    "Multiple objects returned for name '{}'".format(name)
                )

            object_class = self.get_class(object_type[0][0])

        return object_class(self.__db, name)

    def get_class(self, type_name):
        """
        Returns the class associated with the given type or attribute.

        Args:
            type_name (str): The type name to whose associated class is to be
                retrieved. This is meant to be either one of the values exposed
                by the ``ObjectType`` class, or a custom attribute.

        Returns:
            class: The class associated with the given type/attribute.
        """

        try:
            return self.__custom_objects__.get(
                type_name,
                _type_mapping[type_name]
            )
        except KeyError:
            raise ObjectTypeError(
                'Object type not supported: {}.'.format(type_name)
            )

    def replace(self, types):
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

        self.__custom_objects__.update({
            sibilla.sql_identifier(k): v for k, v in types.items()
        })
