set feedback on
set sqlblanklines on

-------------------------------------------------------------------------------

create or replace procedure z.print(what varchar2)
is
begin
  dbms_output.put_line(what);
end;
/


create materialized view z.students
build immediate
refresh force
on demand
as
select * from g.students;
/


-------------------------------------------------------------------------------

create or replace package z.callable_package
is
  procedure print(what varchar2);
end callable_package;
/


create or replace package body z.callable_package
is

  procedure print(what varchar2)
  is
  begin
    dbms_output.put_line(what);
  end print;

end callable_package;
/
