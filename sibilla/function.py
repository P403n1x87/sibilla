# This file is part of "sibilla" which is released under GPL.
#
# See file LICENCE or go to http://www.gnu.org/licenses/ for full license
# details.
#
# Sibilla is a Python ORM for the Oracle Database.
#
# Copyright (c) 2019 Gabriele N. Tornetta <phoenix1987@gmail.com>.
# All rights reserved.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import cx_Oracle

from sibilla import datatypes
from sibilla.callable import Callable, CallableError
from sibilla.object import ObjectType

# from sibilla.record import Record


class Function(Callable):
    """Oracle stored function.

    This class implements Oracle stored functions, including those stored
    inside packages as Python callable objects so that they can be called as
    native Python functions and methods.
    """

    __datatype_mapping = datatypes.mapping

    __slots__ = []

    def __init__(self, db, name, schema, package=None):
        super().__init__(db, name, ObjectType.FUNCTION, schema, package)

        # Try to determine the return type
        bind_variables = {"func_name": self.name}
        if package is None:
            package_query = "is null"
        else:
            package_query = "= :pkg_name"
            bind_variables["pkg_name"] = package.name

        values = list(self.db.plsql("""
            select pls_type, data_type
            from   {}_arguments
            where  object_name   = :func_name
               and package_name  {}
               and argument_name is null
               and position      = 0
               {}
        """.format(
            "all" if self.__schema__ else self.db.__scope__,
            package_query,
            ("and owner= '"+self.__schema__+"'") if self.__schema__ else ""
        ), **bind_variables))

        if not values:
            raise CallableError(
                "No such function: {}".format(self.callable_name)
            )

        elif len(set(values)) == 1:
            ret_type = values[0][0] or values[0][1]

            if "CURSOR" in ret_type or "CURSOR" in values[0][1]:
                self.__ret_type = "CURSOR"
            # elif "RECORD" in ret_type:
            #     # TODO: Return the function call as a string of PL/SQL code to
            #     #       feed to the Record class.
            #     self.__ret_type = "RECORD"
            else:
                self.__ret_type = ret_type

            self.__ora_ret_type = self.__datatype_mapping.get(
                self.__ret_type,
                getattr(cx_Oracle, self.__ret_type, None)
            )
        else:
            self.__ret_type = set([v[0] for v in values])
            self.__ora_ret_type = None

    @property
    def return_type(self):
        """The function return type."""
        return self.__ret_type

    def __call__(self, *args, **kwargs):
        ret_type = kwargs.pop("ret_type", None)

        if ret_type is None and self.__ora_ret_type is None:
            # TODO: The kwargs can be used to discriminate
            raise CallableError(
                "Explicit return value type required for {}".format(self)
            )

        # Type override
        if ret_type is not None:
            ora_ret_type = self.__datatype_mapping.get(
                repr(ret_type),
                ret_type
            )
        else:
            ora_ret_type = self.__ora_ret_type

        # Begin execution
        cur = self.db.cursor()

        # ---- NOTE -----------------------------------------------------------
        # This code is no longer required with cx_Oracle 7
        # ---------------------------------------------------------------------
        # if ora_ret_type in (bool, cx_Oracle.BOOLEAN) \
        #     and has_bool_args(args, kwargs):
        #     # For boolean functions with boolean arguments, Cursor.execute
        #     # cannot accept bool variables
        #     stmt = """begin
        #         :o_ret_val := case {}
        #             when true then '+'
        #             when false then '-'
        #         end;
        #     end;""".format(self.to_string(args, kwargs))
        #
        #     # Replace boolean variables with literal PL/SQL booleans
        #     for i in range(len(args)):
        #         if isinstance(args[i], bool):
        #             stmt = stmt.replace(
        #                 ":{}{}".format(
        #                     Callable.__positional_bind_var_prefix__, i
        #                 ),
        #                 bool_to_char(args[i])
        #             )
        #
        #     # Replace boolean variables with literal PL/SQL booleans
        #     for k, v in kwargs.items():
        #         if isinstance(v, bool):
        #             stmt = stmt.replace(
        #                 ":" + k,
        #                 bool_to_char(v)
        #             )
        #
        #     args = [a for a in args if not isinstance(a, bool)]
        #     kwargs = {
        #         k: v for k, v in kwargs.items() if not isinstance(v, bool)
        #     }
        #
        #     o_ret_val = self.db.var(cx_Oracle.STRING)
        #     kwargs["o_ret_val"] = o_ret_val
        #     for i in range(len(args)):
        #         k = Callable.__positional_bind_var_prefix__ + str(i)
        #         kwargs[k] = args[i]
        #
        #     self.db.plsql(stmt, **kwargs)
        #
        #     ret = o_ret_val.getvalue()
        #
        #     if ret == '+':
        #         return True
        #     if ret == '-':
        #         return False
        #     return None
        # ---------------------------------------------------------------------

        # ---- TODO -----------------------------------------------------------
        # Support for Records is not complete
        # ---------------------------------------------------------------------
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
        #             """, name = self.func_name, obj_name = self.pkg_name or self.func_name, obj_type = 'PACKAGE' if self.pkg_name is not None else 'FUNCTION')
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
        # ---------------------------------------------------------------------

        # else:
        try:
            return cur.callfunc(self.callable_name, ora_ret_type, args, kwargs)
        except cx_Oracle.DatabaseError as e:
            raise CallableError(e) from e

        # self.__ret_type = ret_type
        # self.__ora_ret_type = ora_ret_type

        # return ret
