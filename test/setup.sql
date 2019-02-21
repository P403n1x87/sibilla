alter session set "_ORACLE_SCRIPT"=true;
create user g identified by g;
alter session set "_ORACLE_SCRIPT"=false;
grant connect                                     to g;
grant create procedure                            to g;
grant change notification                         to g; -- Requires documentation. See https://docs.oracle.com/database/121/ADFNS/adfns_cqn.htm#ADFNS018
/
