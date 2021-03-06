Taxidi Volunteer Tracking
=========================
This project contains a volunteer check-in system, intended for use with
[Taxidi](http://jkltech.net/taxidi/).

Why is this a separate codebase?
--------------------------------
I had originally intended to make the volunteer tracking code a part of
Taxidi itself, but schema and coding complications have lead me to
start afresh.  The Flask microframework makes development much more
smooth, and this will serve as a testing grounds for an overhaul of
the Taxidi web interface.

What features can be expected?
------------------------------
+ Time in/out of each volunteer (like a time clock)
+ Track which activity (ministry) and shift (service) they worked
+ Reports for each activity and shift, birthdays, staff attendance
+ Individual online account management

Requirements 
-------------
+ [Flask](http://flask.pocoo.org/)
+ [Flask-SSLify](https://github.com/kennethreitz/flask-sslify)
+ Psycopg2 and a PostgreSQL database
