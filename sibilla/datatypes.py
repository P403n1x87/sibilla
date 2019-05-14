# This file is part of "sibilla" which is released under GPL.
#
# See file LICENCE or go to http://www.gnu.org/licenses/ for full license
# details.
#
# Sibilla is a Python ORM for the Oracle Database.
#
# Copyright (c) 2019 Gabriele N. Tornetta <phoenix1987@gmail.com>.
# All rights reserved.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import cx_Oracle


class Record(type):
    pass


mapping = {
    # Python ADT
    repr(int): cx_Oracle.NATIVE_INT,
    repr(float): cx_Oracle.NUMBER,
    repr(bool): cx_Oracle.BOOLEAN,
    repr(str): cx_Oracle.STRING,

    # ORACLE ADT
    "VARCHAR2": cx_Oracle.STRING,
    "BOOLEAN": cx_Oracle.BOOLEAN,
    "PLS_INTEGER": cx_Oracle.NATIVE_INT,
    "NUMBER": cx_Oracle.NUMBER,
    "CLOB": cx_Oracle.CLOB,
    "CURSOR": cx_Oracle.CURSOR,
    "TABLE": cx_Oracle.CURSOR,
    # "RECORD": Record,
}
