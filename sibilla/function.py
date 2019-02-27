import cx_Oracle
from . import datatypes

from sibilla.object import OracleObject, ObjectType
from .callable      import Callable, bool_to_char
from .record        import Record


class Function(OracleObject, Callable):
    __datatype_mapping = datatypes.mapping

    def __init__(self, db, name):
        super(Function, self).__init__(db, name, ObjectType.FUNCTION)

        path = self.name.split('.')
        if len(path) == 1:
            func_name = self.name
            pkg_name  = None
        else:
            pkg_name, func_name = path[-2:]

        self.pkg_name = pkg_name
        self.__name__ = func_name

        # Try to determine the return type
        if pkg_name == None:
            res = self.db.fetch_all("""
                SELECT pls_type, data_type
                FROM   all_arguments
                where  object_name   = :func_name
                   and package_name  is null
                   and argument_name is null
                   and position      = 0""", func_name = func_name.upper())
        else:
            res = self.db.fetch_all("""
                SELECT pls_type, data_type
                FROM   all_arguments
                where  object_name   = :func_name
                   and package_name  = :pkg_name
                   and argument_name is null
                   and position      = 0""", func_name = func_name.upper(), pkg_name = pkg_name.upper())

        res = list(res)
        values = [e.values for e in res]
        if not values:
            raise ValueError("The function return values are not available from ALL_ARGUMENTS")

        elif len(set(values)) == 1:
            ret_type = res[0][1] if res[0][0] is None else res[0][0]

            if "CURSOR" in ret_type:
                self.__ret_type = "CURSOR"
            elif "RECORD" in ret_type:
                # TODO: Return the function call as a string of PL/SQL code to
                #       feed to the Record class.
                self.__ret_type = "RECORD"
            else:
                self.__ret_type = ret_type
            self.__ora_ret_type = Function.__datatype_mapping[self.__ret_type] if self.__ret_type in Function.__datatype_mapping else (getattr(cx_Oracle, self.__ret_type, None))
        else:
            self.__ora_ret_type = None

    @property
    def return_type(self):
        return self.__ret_type

    def __call__(self, *args, **kwargs):
        ret_type = kwargs.pop("ret_type", None)
        if ret_type == None and self.__ora_ret_type == None:
            raise ValueError("A return type must be specified for function '{}'.".format(self.name))

        # Type override
        if ret_type != None:
            ora_ret_type = Function.__datatype_mapping[repr(ret_type)] if repr(ret_type) in list(Function.__datatype_mapping.keys()) else ret_type
        else:
            ora_ret_type = self.__ora_ret_type

        # Begin execution
        cur = self.db.cursor()

        if ora_ret_type in (bool, cx_Oracle.BOOLEAN) and self.has_bool_args(*args, **kwargs):
            # For boolean functions with boolean arguments, Cursor.execute
            # cannot accept bool variables
            stmt = "begin :o_ret_val := case {} when true then '+' when false then '-' end; end;".format(self.to_string(*args, **kwargs))

            for i in range(len(args)):
                if type(args[i]) == bool:
                    stmt = stmt.replace(":{}{}".format(Callable.__positional_bind_var_prefix__, i), bool_to_char(args[i]))

            for k in kwargs:
                if type(kwargs[k]) == bool:
                    stmt = stmt.replace(":{}".format(k), bool_to_char(kwargs[k]))

            args   = [a for a in args if type(a) != bool]
            kwargs = {k : kwargs[k] for k in kwargs if type(kwargs[k]) != bool}

            o_ret_val = cur.var(cx_Oracle.STRING)
            kwargs.update({"o_ret_val" : o_ret_val})
            kwargs.update({"{}{}".format(Callable.__positional_bind_var_prefix__, i) : args[i] for i in range(len(args))})
            cur.execute(stmt, **kwargs)
            if o_ret_val:
                ret = o_ret_val.getvalue()
                if ret == '+': return True
                if ret == '-': return False
            return ret

        # TODO: Support for Records is not complete
        # elif ora_ret_type == datatypes.Record or self.has_record_args(*args, **kwargs):
        #     declare, block = self.record_args(*args, **kwargs)
        #     if ora_ret_type == datatypes.Record:
        #         rec_type = self.db.fetch_all("""
        #             select     name
        #             from       all_identifiers
        #             start with name        = upper(:name)
        #                    and type        = 'FUNCTION'
        #                    and object_name = upper(:obj_name)
        #                    and object_type = upper(:obj_type)
        #                    and usage       = 'DECLARATION'
        #             connect by prior usage_id    = usage_context_id
        #                    and prior object_name = object_name
        #                    and prior object_type = object_type
        #             order by   usage_id
        #             """, name = self.func_name, obj_name = self.pkg_name if self.pkg_name != None else self.func_name, obj_type = 'PACKAGE' if self.pkg_name != None else 'FUNCTION')
        #
        #         if len(rec_type) == 2:
        #             pkg = self.pkg_name
        #             rec = rec_type[1][0]
        #         elif len(rec_type) == 3:
        #             pkg = rec_type[1][0]
        #             rec = rec_type[2][0]
        #         else:
        #             # Try to find the definition in ALL_SOURCE
        #             # TODO: To implement, but not straightforward
        #             raise ValueError("Unable to determine the return value of function '{}'".format(self.func_name))
        #
        #         ret_type = getattr(getattr(self.db, pkg), rec)
        #         ret = ret_type()
        #         stmt = """
        #             declare
        #                 l_ret {pkg_name}.{rec_name};
        #                 {declare}
        #             begin
        #                 l_ret := {call};
        #                 {block}
        #                 {bindings};
        #             end;
        #             """.format(declare = declare, block = block, pkg_name = pkg, rec_name = rec, call = self.to_string(*args, **kwargs), bindings =  ";".join([":{k} := l_ret.{k}".format(k = key) for key in ret.keys()]))
        #         cur.execute(stmt, **ret)
        #     else:
        #         stmt = """
        #             declare
        #                 {declare}
        #             begin
        #                 {block}
        #                 :o_ret_val := {call};
        #             end;
        #             """.format(declare = declare, block = block, call = self.to_string(*args, **kwargs))
        #         o_ret_val = cur.var(ora_ret_type)
        #         print stmt
        #         cur.execute(stmt, o_ret_val = o_ret_val)
        #         ret       = o_ret_val.getvalue()
        else:
            ret = cur.callfunc(self.name, ora_ret_type, args, kwargs)

        self.__ret_type = ret_type
        self.__ora_ret_type = ora_ret_type

        return ret
