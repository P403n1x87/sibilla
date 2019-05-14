<h1>
  <p align="center"><img src="art/sibilla.png" alt="Sibilla"></p>
</h1>
<!-- <h1 align="center"> Sibilla</h1> -->

<h3 align="center">Python ORM for the Oracle Database</h3>

<p align="center">
  <a href="https://travis-ci.org/P403n1x87/sibilla">
    <img src="https://travis-ci.org/P403n1x87/sibilla.svg?branch=master"
         alt="Travis CI Build Status">
  </a>
  <img src="https://img.shields.io/badge/coverage-99%25-green.svg"
       alt="Test coverage at 99%">
  <a href="https://badge.fury.io/py/sibilla">
    <img src="https://badge.fury.io/py/sibilla.svg" alt="PyPI version">
  </a>
  <a href="http://pepy.tech/project/sibilla">
    <img src="http://pepy.tech/badge/sibilla"
         alt="PyPI Downloads">
  </a>
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
  <a href="#examples"><b>Examples</b></a>&nbsp;&bull;
  <a href="#documentation"><b>Documentation</b></a>
</p>

## Synopsis

Sibilla is a Python ORM solution for the Oracle Database. It has been designed
with the goal of making database access as Pythonic as possible. SQL queries
and PL/SQL code blocks are _aliens_ in Python sources. With Sibilla you can
access table content and call PL/SQL code in a Pythonic way.

Internally, Sibilla relies on the
[cx_Oracle](https://oracle.github.io/python-cx_Oracle/) package to perform
queries against the Oracle Data Dictionaries to retrieve stored objects and the
data they contain.


## Installation

Sibilla can be installed directly from PyPI

~~~~ bash
python3 -m pip install sibilla --upgrade
~~~~

Alternatively, it can be installed with pip from GitHub with

~~~ bash
python3 -m pip install git+https://github.com/P403n1x87/sibilla
~~~

## Example

A minimal example to connect to a database and access a table called `CUSTOMER`
is

~~~~ python
from sibilla import OracleDB


db = OracleDB("username", "password", dsn="dsn")
customer_table = db.customer
~~~~

If the customer table has a primary key on a column named `ID`, and a column
`NAME`, we can get the value of the latter on a row with ID 42 (assuming it
exists in the database) with

~~~~ python
>>> customer = customer_table[42]
>>> customer.name
'John Smith'
~~~~

## Documentation

For more examples and customisation details, please refer to the official
[Sibilla Documentation](https://p403n1x87.github.io/sibilla/).

---

## License

GPLv3.
