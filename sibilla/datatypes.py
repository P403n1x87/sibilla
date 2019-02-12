import cx_Oracle


class Record(type):
    pass

mapping = {
    # Python ADT
    repr(int)             : cx_Oracle.NATIVE_INT
   ,repr(float)           : cx_Oracle.NUMBER
   ,repr(bool)            : cx_Oracle.BOOLEAN
   ,repr(str)             : cx_Oracle.STRING

   # ORACLE ADT
   ,"VARCHAR2"            : cx_Oracle.STRING
   ,"BOOLEAN"             : cx_Oracle.BOOLEAN
   ,"PLS_INTEGER"         : cx_Oracle.NATIVE_INT
   ,"NUMBER"              : cx_Oracle.NUMBER
   ,"CLOB"                : cx_Oracle.CLOB
   ,"CURSOR"              : cx_Oracle.CURSOR
   ,"TABLE"               : cx_Oracle.CURSOR
   ,"RECORD"              : Record
}
