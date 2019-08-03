alter session set "_ORACLE_SCRIPT"=true;
create user g identified by g;
create user z identified by z;
alter session set "_ORACLE_SCRIPT"=false;

alter user g quota unlimited on users;
alter user z quota unlimited on users;

grant connect                                     to g;
grant create procedure                            to g;
grant create table                                to g;
grant create materialized view                    to g;
grant create sequence                             to g;
grant change notification                         to g;
-- Requires documentation. See https://docs.oracle.com/database/121/ADFNS/adfns_cqn.htm#ADFNS018
/

grant connect                                     to z;
grant create procedure                            to z;
grant create table                                to z;
grant create sequence                             to z;
grant change notification                         to z;


-- NOTE: This will fail on first execution
grant execute on z.print                          to g;
grant execute on z.callable_package               to g;
grant all     on g.students                       to z WITH GRANT OPTION;
grant all     on z.students                       to g WITH GRANT OPTION;
/
