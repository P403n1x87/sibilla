from sibilla import DatabaseError
from sibilla.caching import Cached, cachedmethod
from sibilla.object import OracleObject
# from sibilla.record import RecordInstance as RecordI


# ---- Exceptions ----

class CallableError(DatabaseError):
    pass

# -----------------------------------------------------------------------------

class CallableFactory(Cached):

    __slots__ = []

    def __init__(self, callable_class, package=None):
        super().__init__(package.cache if package else None)

        self.__class = callable_class
        self.__package = package

    @cachedmethod
    def __getattr__(self, name):
        return self.__class(self.__package.db, name, self.__package)


# def field_assignment(e, block, parent):
#     for k in e:
#         val = getattr(e, k)
#         if val is None:
#             continue
#
#         if isinstance(val, RecordI):
#             field_assignment(val, block, "{}.{}".format(parent, k))
#         else:
#             block.append("{}.{} := {};".format(
#                 parent, k, "'{}'".format(val) if isinstance(val, str) else str(val)
#             ))


# THREE_STATE = {
#     True: "true",
#     False: "false",
#     None: "null"
# }
#
#
# def bool_to_char(value):
#     return THREE_STATE[value]


# def has_arg_of_type(t, args, kwargs):
#     for arg in args:
#         if isinstance(arg, t):
#             return True
#
#     for _, v in kwargs.items():
#         if isinstance(v, t):
#             return True
#
#     return False
#
#
# def has_bool_args(args, kwargs):
#     return has_arg_of_type(bool, args, kwargs)
#
#
# def has_record_args(args, kwargs):
#     return has_arg_of_type(RecordI, args, kwargs)
#
#
# def record_args(args, kwargs):
#     rec_args = [x for x in args if type(x) == RecordI]
#     rec_kwargs = {k: v for k, v in kwargs.items() if type(v) == RecordI}
#
#     if not rec_args and not rec_kwargs:
#         return "", ""
#
#     declare = []
#     block = []
#
#     if rec_args:
#         for i, e in enumerate(rec_args):
#             declare.append("l_rec_arg{} {};".format(i, e.type))
#             field_assignment(e, block, "l_rec_arg{}".format(i))
#
#     if rec_kwargs:
#         for i, key in enumerate(rec_kwargs):
#             e = kwargs[key]
#             declare.append("l_rec_kwarg{} {};".format(i, e.type))
#             field_assignment(e, block, "l_rec_kwarg{}".format(i))
#
#     return "\n".join(declare), "\n".join(block)


class Callable(OracleObject):
    """Base class for Procedure and Function."""

    def __init__(self, db, name, type, package=None):
        super().__init__(db, name, type)

        self.package = package
        self.callable_name = (
            package.name + "." + self.name if package else self.name
        )

    def __repr__(self):
        return "<{} '{}'{}>".format(
            self.object_type.lower(),
            self.name,
            " from " + repr(self.package) if self.package else ""
        )

    # __positional_bind_var_prefix__ = "ora$bind_var$pos$"
    #
    # def to_string(self, args, kwargs):
    #     arg_str = ""
    #     if args:
    #         arg_str += ', '.join([
    #             ":" + Callable.__positional_bind_var_prefix__ + str(i)
    #             for i in range(len(args))
    #         ])
    #     if kwargs:
    #         arg_str += ', '.join([k + " => :" + k for k in kwargs])
    #
    #     return "{func}{args}".format(
    #         func=self.name,
    #         args="(" + arg_str + ")" if arg_str else ""
    #     )
