#!/usr/bin/env python
#-*- coding:utf-8 -*-

# Copyright 2013 Zac Sturgeon <admin@jkltech.net>

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA 02110-1301, USA.

# All database tables and features are documented here:
#   http://jkltech.net/taxidi/wiki/Volunteers

import psycopg2

debug = True

"""
PostgreSQL driver for Taxidi volunteer tracking.
"""
class Database:
    """
    :param host: IP or hostname of database to connect to.
    :param dbname: Database name (usually `volunteers`
    :param user: Username for database authentication
    :param password: Password for database authentication
    :param location: Physical check-in location for reporting purposes (e.g. lobby)
    """
    def __init__(self, host, dbname, user, password, location='pyTimeClock')
        
