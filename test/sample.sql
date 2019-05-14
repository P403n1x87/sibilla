set sqlblanklines on

---- DDL ----

drop table marks;
drop table modules;
drop table students;

create table students(
  no                          varchar(10),
  surname                     varchar(20),
  forename                    varchar(20),

  constraint student_no#p     primary key (no)
);

create table modules(
  code                        varchar(8),
  name                        varchar(64),

  constraint module_code#p    primary key (code)
);

create table marks(
  student_no                  varchar(10),
  module_code                 varchar(8),
  mark                        integer,

  constraint student_no#f     foreign key (student_no)  references students (no),
  constraint module_code#f    foreign key (module_code) references modules  (code)
);

---- DML ----

insert into students values ('20060101','Dickens','Charles');
insert into students values ('20060102','ApGwilym','Dafydd');
insert into students values ('20060103','Zola','Emile');
insert into students values ('20060104','Mann','Thomas');
insert into students values ('20060105','Stevenson','Robert');

insert into modules values ('CM0001', 'Databases');
insert into modules values ('CM0002', 'Programming Languages');
insert into modules values ('CM0003', 'Operating Systems');
insert into modules values ('CM0004', 'Graphics');

insert into marks values ('20060101', 'CM0001', 80);
insert into marks values ('20060101', 'CM0002', 65);
insert into marks values ('20060101', 'CM0003', 50);
insert into marks values ('20060102', 'CM0001', 75);
insert into marks values ('20060102', 'CM0003', 45);
insert into marks values ('20060102', 'CM0004', 70);
insert into marks values ('20060103', 'CM0001', 60);
insert into marks values ('20060103', 'CM0002', 75);
insert into marks values ('20060103', 'CM0004', 60);
insert into marks values ('20060104', 'CM0001', 55);
insert into marks values ('20060104', 'CM0002', 40);
insert into marks values ('20060104', 'CM0003', 45);
insert into marks values ('20060105', 'CM0001', 55);
insert into marks values ('20060105', 'CM0002', 50);
insert into marks values ('20060105', 'CM0004', 65);

commit;
