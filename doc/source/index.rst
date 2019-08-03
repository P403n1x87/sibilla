.. image:: images/sibilla.png
   :align: center

.. raw:: html

  <h3 align="center">Python ORM for the Oracle Database</h3>

  <p align="center">
    <a href="https://travis-ci.com/P403n1x87/sibilla">
      <img src="https://travis-ci.com/P403n1x87/sibilla.svg?token=fzW2yzQyjwys4tWf9anS&branch=master"
           alt="Travis CI Build Status"/>
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


.. image:: images/hr.svg
   :align: center
   :height: 48pt


.. toctree::
   :maxdepth: 4
   :hidden:

   api_reference


Sibilla Overview
================

Sibilla is a Python ORM solution for the Oracle Database. It has been designed
with the goal of making database access as Pythonic as possible. SQL queries
and PL/SQL code blocks are `aliens` in Python sources. With Sibilla you can
access table content and call PL/SQL code in a Pythonic way.

The Database Object
-------------------

The central object in Sibilla is the :class:`sibilla.Database` class.
Effectively, this is just a `connection object`_. However, Sibilla treats it as
the object that represents the actual database and its content (e.g. stored
tables, views, procedures, packages etc...) in terms of Oracle Objects.

Sibilla leverages the Oracle Data Dictionaries to look up objects from the
database, allowing you to access them in a Pythonic way. For example, this is
how you connect to an Oracle Database with Sibilla::

  >>> from sibilla import Database
  db = Database("user", "password", "tns")

If no exceptions are thrown, ``db`` is now an open connection to an Oracle
database. One can then query a table, e.g., ``COUNTRY``, with::

  >>> db.country
  <table 'COUNTRY'>
  >>> for row in db.country.fetch_all(region="EU"):
  ...     print(row)

This will match all the rows in ``COUNTRY`` where the value of the column
``REGION`` is ``EU``.

Row Wrappers
~~~~~~~~~~~~

By default, every row in the above loop is an instance of
:class:`sibilla.CursorRow`. This is just a wrapper around the row objects
returned by a plain `cursor object`_ that give extra structure and feature.
This way one can easily access the field values of `row` either as attributes
or as tuple elements. For example, if the ``COUNTRY`` table in the example
above has the column ``NAME`` for the name of the country, one could access it
with ``row.name``::

  >>> for row in db.country.fetch_all(region="EU"):
  ...     print(row.name)

One can change and enhance the default behaviour by subclassing
:class:`sibilla.RowWrapper` and setting the new row wrapper class on a database
object with the :func:`sibilla.Database.set_row_wrapper` method.

Refer to :class:`sibilla.RowWrapper` for more details on how to implement a
custom row wrapper class.


Executing PL/SQL Code
~~~~~~~~~~~~~~~~~~~~~

Oracle databases provide a procedural extension of the SQL language that can be
used to code application that live close to the database itself. The DB API 2.0
documents the |callproc|_ method of the ``Cursor`` object as a way to call a
stored procedure. However, an Oracle database offers stored functions and
packages as well and to use them from Python requires the use of the |execute|_
method and bind variables.

With Sibilla, stored procedures, functions and packages become Python objects
and can be used in a Pythonic way. Suppose, for instance, the the database has
the stored function ``bar(a pls_integer, b varchar2)`` that returns
``boolean``. One can call it with::

  >>> result = db.bar(42, "hello")

or with::

  >>> result = db.bar(a=42, b="hello")

The variable ``result`` will hold the result of the function. Similarly, if the
function ``bar`` were declared inside the package ``foo``, it could have been
called with::

  >>> db.foo
  <package 'FOO'>
  >>> result = db.foo.bar(42, b="hello")


.. |callproc| replace:: ``callproc``
.. _callproc: https://www.python.org/dev/peps/pep-0249/#callproc

.. |execute| replace:: ``execute``
.. _execute: https://www.python.org/dev/peps/pep-0249/#id15

Data Sets and Tables
--------------------

If you have a database you would probably want to extract data from it. The
general approach is to write a SQL query as a string to pass to the `execute`_
method of a cursor instance. For many simple queries, Sibilla allows you to
avoid embedding SQL code in your Python sources.

As an example, suppose that we have a table or view named ``EMPLOYEE`` with
columns ``MANAGER_ID`` and ``SITE_ID``. The former is a foreign key to the
``MANAGER`` table which contains a list of all managers in a company, and
``SITE_ID`` is a foreign key to the ``SITE`` table, which holds the information
about the different sites in which the company operates. We can retrieve the
list of all the employees under the managers with ID 10 and 12, and working at
the site with ID 1 with::

  db.employee.fetch_all(where=(
    {"site_id": 1},
    [
      {"manager_id": 10},
      {"manager_id": 12},
    ]
  ))

Sibilla interprets the tuple constructor ``(,)`` and the list constructor
``[]`` as logical operators for ``where`` statements. In the above example, the
``where`` argument literally translates to:

.. code-block:: sql

  where (SITE_ID = 1 and (MANAGER_ID = 10 or MANAGER_ID = 12))

Refer to :class:`sibilla.dataset.DataSet` for more details on how to control
the results returned by a query.


Primary Keys
~~~~~~~~~~~~

Tables are treated as special kind of data sets, since one can define
constraints on them, such as primary keys. Indeed, a table with a primary key
constraint is not too different from either a list or a dictionary, as the
primary key value can be used to access the associated row.

Suppose that you have a table, ``ACCOUNT``, with a primary key constraint on
the numeric column ``ID``. Assuming that the table ``ACCOUNT`` has a row with
ID 42, one can fetch this row with::

  >>> db.account[42]
  <row from <table 'ACCOUNT'> with PK '{'ID': 42}'>

Refer to the :class:`sibilla.table.Table` for more details on primary keys and
the remarks of the `slice` notation.


Foreign Keys and Smart Rows
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Tables can have foreign key constraints too, creating relations with other
tables and their primary keys. Suppose that the table ``ACCOUNT`` from the
previous section has a foreign key constraint on the column ``CURRENCY``,
referencing the ``ID`` column of the ``CURRENCY`` table. Normally, we would
have the following situation::

  >>> db.account[42].currency
  12

If we now wanted to retrieve the currency name, we would have to first retrieve
the row from the ``CURRENCY`` table with ID 12 and then access its attribute
``name``::

  >>> db.currency[db.account[42].currency].name
  'EURO'

We can simplify the coding by allowing the default table class to be `smarter`
and return the referenced row instead, rather than just the value of the
foreign key. With Sibilla, this can be achieved by changing the row class used
by the :class:`sibilla.table.Table` to return query results::

  >>> from sibilla.table import SmartRow, Table
  >>> Table.set_row_class(SmartRow)
  >>> db.account[42].currency
  <row from <table 'CURRENCY'> with PK '{'ID': 12}'>
  >>> db.account[42].currency.name
  'EURO'


Caching and Performance
-----------------------

Query results are normally cached as they are retrieved for quicker subsequent.
Being aware of this caching is important when changes are committed to the
database.

By default, Sibilla uses a thread-safe TTL cache with a default TTL of 1 day
and maximum size of 1024 cache entries. These parameters can be changed
globally via the :func:`sibilla.caching.set_ttl` and
:func:`sibilla.caching.set_maxsize` module methods.

Any cached object exposes the `cache` attribute, which can be used to manually
flush the `cache` with the `flush` method and force the look-ups to fetch the
data from the database again on the next access.

Another aspect that can affect performance is the `scope` used to query the
database data dictionaries. By default, the scope is set to ``ALL``, which
means that the database-wide data dictionaries like ``ALL_OBJECTS``,
``ALL_PROCEDURES``, ... will be used to look up objects from the database. If
one needs to access objects from the schema of the logged user, it is
recommended that the scope be set to ``USER`` with::

  >>> db.set_scope(Database.Scope.USER)

On databases with many schemas and stored objects, this should provide a
considerable speed up during object look-ups.




.. _connection object: https://www.python.org/dev/peps/pep-0249/#connection-objects
.. _cursor object: https://www.python.org/dev/peps/pep-0249/#cursor-objects
.. _execute: https://www.python.org/dev/peps/pep-0249/#id15


.. image:: images/hr.svg
   :align: center
   :height: 48pt


Advanced Topics
===============

Sibilla offers a customisation API to accommodate for some special needs. This
is documented along with the code so here we will see some typical
customisation scenarios and examples.


Object Look-ups
---------------

The default object look-up mechanism can be customised in different ways. For
example, one can subclass the default class for tables, i.e.
:class:`sibilla.table.Table` and instruct the default look-up to return
instances of the new class whenever a table is requested from the database::

  from sibilla.object import ObjectType
  from sibilla.table import Table


  class MyTable(Table):
      ...


  db.__lookup__.replace({ObjectType.TABLE: MyTable})

Instead of replacing the global class for handling tables, one can define the
table class to use for a particular table (and more generally the class to use
for a particular object). For example::

  >>> db.__lookup__.replace({"customer" : MyTable})

instructs the database object to return an instance of ``MyTable`` whenever the
table ``CUSTOMER`` is accessed.

Refer to :class:`sibilla.object.ObjectLookup` for more details and further
customisation examples.


Data Analytics
--------------

Statisticians, Data Analyists and Data Scientists are likely to need to access
data from a database and perform data analysis on the result. The Sibilla API
has been designed to be flexible enough to allow plugging in external
libraries, like `Pandas`_. In this case, it is enough to define the following
row wrapper::

  from pandas import DataFrame
  from sibilla import CursorRow


  class DataFrameWrapper(CursorRow):

      @staticmethod
      def _to_data_frame(cursor, data):
          return DataFrame.from_records(
              data,
              columns=[c[0] for c in cursor.description]
          )

      @staticmethod
      def from_cursor(cursor):
          return DataFrameWrapper._to_data_frame(cursor, cursor)

      @staticmethod
      def from_list(cursor, data):
          return DataFrameWrapper._to_data_frame(cursor, data)

and then set it on the database with::

  db.set_row_wrapper(DataFrameWrapper)

We also need to make sure that we remove the default row class on data sets
like views and tables, since we want to return the result of the row wrapper
unchanged::

  from sibilla.dataset import DataSet
  from sibilla.table import Table


  DataSet.set_row_class(None)
  Table.set_row_class(None)

Whenever we query a table or a view, or the database directly with
``fetch_all`` and ``fetch_many``, the returned result is now an instance of
``pandas.DataFrame``::

  >>> isinstance(db.account.fetch_all(), DataFrame)
  True


.. _Pandas: https://pandas.pydata.org/


Tweaking the Default Caches
---------------------------

Whilst not recommended, the default cache of a cached object can be replaced
with a custom one by assigning directly to the ``cache`` attribute. Ideally,
the custom cache class should implement a ``flush`` method to reset the cache
and ensure that modified objects can be fetched anew from the database.

Refer to the default cache class,
:class:`sibilla.caching.SynchronizedTTLCache`, for further details.


.. image:: images/hr.svg
   :align: center
   :height: 48pt


Installation
============

Sibilla can be installed directly from PyPI:

.. code-block:: bash

  python3 -m pip install sibilla --upgrade

Alternatively, it can be installed with pip from GitHub with:

.. code-block:: bash

  python3 -m pip install git+https://github.com/P403n1x87/sibilla


.. image:: images/hr.svg
   :align: center
   :height: 48pt


API Reference
=============


The Sibilla :ref:`apireference` documents the public interface and provides
some use and customisation examples.


.. image:: images/hr.svg
   :align: center
   :height: 48pt


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
