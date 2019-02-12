<h1 align="center"> Sibilla</h1>

<h3 align="center">Python ORM for the Oracle database</h3>

<p align="center">
  <img src="https://img.shields.io/badge/version-0.1.0-blue.svg"
       alt="Version 0.1.0">
  <a href="https://github.com/P403n1x87/sibilla/blob/master/LICENSE.md">
    <img src="https://img.shields.io/badge/license-GPLv3-ff69b4.svg"
         alt="LICENSE">
  </a>
</p>

<p align="center">
  <a href="#synopsis"><b>Synopsis</b></a>&nbsp;&bull;
  <a href="#installation"><b>Installation</b></a>&nbsp;&bull;
  <a href="#examples"><b>Examples</b></a>
</p>


## Synopsis

Sibilla is a Python ORM framework for Oracle databases. It wraps around [cx_Oracle](https://oracle.github.io/python-cx_Oracle/) to provide a Pythonic interface to the SQL engine and PL/SQL code. If you have an Oracle database application, you don't have to rewrite it from scratch in Python or code ad-hoc wrapper. Instead Sibilla allows you to call PL/SQL functions/procedures in pure Python code.

Sibilla is mainly meant to be used for prototyping applications that connect to an Oracle database quickly, or for swift tooling. It can also be used to develop non-performance-critical production applications.


## Example

A minimal example to connect to a database and access a table called `CUSTOMER` is

~~~~
from sibilla import OracleDB

db = OracleDB("username", "password", dsn = "dsn")
customer_table = db.customer
~~~~

If the customer table has a primary key on a column named `ID`, and a column `NAME`, we can get the value of the latter on a row with ID 42 (assuming it exists in the database) with

~~~~
customer = customer_table(42)
print(customer.name)
~~~~


---

## License

GPLv3.
