set feedback on
set sqlblanklines on

-------------------------------------------------------------------------------

create or replace procedure print(what varchar2)
is
begin
  dbms_output.put_line(what);
end;
/

create or replace function len(string varchar2)
return pls_integer
is
begin
  return length(string);
end;
/

create or replace function is_positive(n pls_integer)
return boolean
is
begin
  return n > 0;
end;
/

create or replace function negate(b boolean)
return boolean
is
begin
  return not b;
end;
/

create or replace function return_cursor
return sys_refcursor
is
  l_cursor sys_refcursor;
begin
  open l_cursor for select * from students;
  return l_cursor;
end;
/

-------------------------------------------------------------------------------

create or replace package callable_package
is

  function is_negative(n pls_integer)
  return boolean;

  function logic_and(a boolean, b boolean)
  return boolean;

  function ret_overloaded(a pls_integer)
  return boolean;

  function ret_overloaded(b pls_integer)
  return varchar2;

  procedure print(what varchar2);

end callable_package;
/

create or replace package body callable_package
is

  function is_negative(n pls_integer)
  return boolean
  is
  begin
    return n < 0;
  end is_negative;

  function logic_and(a boolean, b boolean)
  return boolean
  is
  begin
    return a and b;
  end logic_and;

  function ret_overloaded(a pls_integer)
  return boolean
  is
  begin
    return is_negative(a);
  end ret_overloaded;

  function ret_overloaded(b pls_integer)
  return varchar2
  is
  begin
    return b;
  end ret_overloaded;

  procedure print(what varchar2)
  is
  begin
    dbms_output.put_line(what);
  end print;

end callable_package;
/
