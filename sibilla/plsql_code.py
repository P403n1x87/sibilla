class PLSQLCode(object):

    __generator_class__ = "__generator__"

    def __init__(self):
        self.declare        = []
        self.code           = []
        self.bind_variables = {}
        self.value          = None

        self._generated     = False
        self._cached        = None

    def merge(self, block):
        # In-memory object should have different IDs. If not, something
        # unexpected happened and we should stop.
        for k in self.bind_variables:
            if k in block.bind_variables:
                raise RuntimeError("In-memory object clash when generating PL/SQL Code.")

        self.bind_variables.update(block.bind_variables)

    def get_generator(self, obj):
        try:
            generator = getattr(obj.__class__, self.__class__.__generator_class__)(obj)
            if not generator._generated:
                generator.generate()
                generator._generated = True
            return generator
        except AttributeError:
            value = str(id(obj))
            self.bind_variables[value] = obj

            code = PLSQLCode()
            code.value = ":" + value

            return code

    def generate(self):
        """
        This method should fill the three class attributes.
        """
        for d in self.declare:
            try:
                self.merge(d)
            except:
                pass

        for c in self.code:
            try:
                self.merge(c)
            except:
                pass

    def __str__(self):
        if self._cached:
            return self._cached

        if not self._generated:
            self.generate()
            self._generated = True

        code = ""

        if self.declare:
            code += "declare\n" + "  \n".join([str(s) for s in self.declare])

        if self.code:
            code += "\nbegin\n  {}\nend;".format("\n  ".join([str(s) for s in self.code]))

        self._cached = code

        return code

    def execute(self, db):
        stmt = str(self)
        db.plsql(stmt, **self.bind_variables)

class Declare(PLSQLCode):
    def __init__(self, name, typ, value = None):
        super(Declare, self).__init__()

        self.name  = name
        self.type  = typ
        self.value = value

        if value:
            self.key = str(id(value))
            self.bind_variables = {self.key : value}

    def __str__(self):
        declare = "  {:48}{}".format(self.name, self.type)
        if self.value: declare += " := :{}".format(self.key)

        return declare + ";"

# TODO: This messes up with dest!
class Assign(PLSQLCode):
    def __init__(self, dest, src):
        super(Assign, self).__init__()

        self.code = src.code
        self.code.append("{} := {}".format(dest.value, src.value))
        self.code += dest.code

        self.declare = src.declare + dest.declare

        self.merge(src)
        self.merge(dest)


class LCode(PLSQLCode):
    __generator_class__ = "__lgenerator__"

    def merge(self, block):
        super(LCode, self).merge(block)

        self.declare += block.declare
        self.code    += block.code


class RCode(PLSQLCode):
    __generator_class__ = "__rgenerator__"

    def merge(self, block):
        super(RCode, self).merge(block)

        self.declare = block.declare + self.declare
        self.code    = block.code    + self.code










class RecordRCode(RCode):
    def __init__(self, record):
        super(RecordRCode, self).__init__()

        self.record = record
        self.value  = "l_" + str(id(record))
        self.declare.append(Declare(self.value, record.__type__.name))

        for f in self.record.__type__.fields:
            # Try to merge with other datatypes that require code generation

            value = self.get_generator(record[f])
            if value == None:
                raise RuntimeError("Invalid value in record field assignment.")

            self.merge(value)

            self.code.append("{key}.{field} := {value};".format(
                key   = self.value
               ,field = f
               ,value = value.value
            ))






class RecordLCode(LCode):
    def __init__(self, record):
        super(RecordLCode, self).__init__()

        self.record = record
        self.value  = "l_" + str(id(record))
        self.declare.append(Declare(self.value, record.__type__.name))

        for f in self.record.__type__.fields:
            # Try to merge with other datatypes that require code generation

            value = self.get_generator(record[f])
            if value == None:
                raise RuntimeError("Invalid value in record field assignment.")

            self.code.append("{value} := {key}.{field};".format(
                key   = self.value
               ,field = f
               ,value = value.value
            ))

            self.merge(value)



class MockRecordInstance(dict):

    __rgenerator__ = RecordRCode
    __lgenerator__ = RecordLCode

    def __init__(self, t):
        self.__dict__["__type__"] = t
        for f in t.fields:
            self[f] = None

    def __getattr__(self, name):
        return self[name]

    def __setattr__(self, name, value):
        if name not in self:
            raise KeyError("{} is not a valid field for record type {}".format(name, self.__type__.name))

        self[name] = value



class MockRecord(object):
    def __init__(self, name):
        self.name = name

    def __call__(self):
        return MockRecordInstance(self)




class FunctionCode(RCode):
    def __init__(self, name, *args, **kwargs):
        super(FunctionCode, self).__init__()

        p_args  = ", ".join([self.get_value(a) for a in args])
        kw_args = ", ".join(["{} => {}".format(k, self.get_value(kwargs[k])) for k in kwargs])

        if not p_args:
            all_args = kw_args
        elif not kw_args:
            all_args = p_args
        else:
            all_args = ", ".join([p_args, kw_args])
        if all_args: all_args = "({})".format(all_args)

        self.value = "{name}{args};".format(name = name, args = all_args)

    def get_value(self, obj):
        generator = self.get_generator(obj)
        self.merge(generator)
        return generator.value


# TEST
if __name__ == "__main__":
    # code = PLSQLCode()
    # code.declare.append(Declare("l_text", "varchar2(10)"))
    # code.declare.append(Declare("l_init_text", "varchar2(400)", "Hallo World"))
    # print(str(code))


    record_type = MockRecord("t_record_type")
    record_type.fields = ['value1', 'value2']

    record_inst = record_type()
    record_inst.value1 = 1

    record_inst_2 = record_type()
    record_inst_2.value1 = 10
    record_inst.value2 = record_inst_2

    # gen = RecordRCode(record_inst)
    # print(str(gen))
    # print gen.bind_variables

    f = FunctionCode("k.debug", 42, "test", rec_arg = record_inst)
    print(str(f))
    print f.bind_variables

    record_instb = record_type()
    record_instb.value1 = 12

    record_instb_2 = record_type()
    record_instb_2.value1 = 14
    record_instb_2.value2 = 16
    record_instb.value2 = record_instb_2

    rec = RecordLCode(record_instb)

    gen = Assign(rec, f)
    print(str(gen))
    print gen.bind_variables
