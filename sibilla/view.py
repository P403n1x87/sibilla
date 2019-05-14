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

from sibilla import DatabaseError
from sibilla.object import ObjectType, OracleObject


# ---- Exceptions -------------------------------------------------------------


class ViewError(DatabaseError):
    """View-related database error."""
    pass


# -----------------------------------------------------------------------------


from sibilla.dataset import DataSet


class View(OracleObject, DataSet):
    """Oracle view class."""

    __view__ = None

    def __init__(self, db, name=None, schema=None):
        name = name or self.__view__

        if name is None:
            raise ViewError("No view name given")
        super().__init__(db, name, ObjectType.VIEW, schema)
