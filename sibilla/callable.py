from .record import RecordInstance as RecordI


def field_assignment(e, block, parent):
    for k in e:
        val = getattr(e, k)
        if val is None:
            continue

        if type(val) == RecordI:
            field_assignment(val, block, "{}.{}".format(parent, k))
        else:
            block.append("{}.{} := {};".format(
                parent, k, "'{}'".format(val) if type(val) == str else str(val)
            ))


def bool_to_char(value):
    if value is True:
        return "true"

    if value is False:
        return "false"

    return "null"


class Callable(object):
    """
    Mixin class for code reuse in Procedure and Function
    """

    __positional_bind_var_prefix__ = "ora$bind_var$pos$"

    def to_string(self, *args, **kwargs):
        arg_str = ""
        if args:
            arg_str += ', '.join([
                ":" + Callable.__positional_bind_var_prefix__ + str(i)
                for i in range(len(args))
            ])
        if kwargs:
            arg_str += ', '.join([k + " => :" + k for k in kwargs])

        return "{func}{args}".format(
            func=self.name,
            args="(" + arg_str + ")" if arg_str else ""
        )

    def has_bool_args(self, *args, **kwargs):
        ret = False

        for arg in args:
            if type(arg) == bool:
                ret = True
                break

        for k in kwargs:
            if isinstance(kwargs[k], bool):
                ret = True
                break

        return ret

    def has_record_args(self, *args, **kwargs):
        ret = False

        for arg in args:
            if type(arg) == RecordI:
                ret = True
                break

        for k in list(kwargs.keys()):
            if type(kwargs[k]) == RecordI:
                ret = True
                break

        return ret

    def record_args(self, *args, **kwargs):
        rec_args = [x for x in args if type(x) == RecordI]
        rec_kwargs = {k: v for k, v in kwargs.items() if type(v) == RecordI}

        if not rec_args and not rec_kwargs:
            return "", ""

        declare = []
        block = []

        if rec_args:
            for i, e in enumerate(rec_args):
                declare.append("l_rec_arg{} {};".format(i, e.type))
                field_assignment(e, block, "l_rec_arg{}".format(i))

        if rec_kwargs:
            for i, key in enumerate(rec_kwargs):
                e = kwargs[key]
                declare.append("l_rec_kwarg{} {};".format(i, e.type))
                field_assignment(e, block, "l_rec_kwarg{}".format(i))

        return "\n".join(declare), "\n".join(block)
