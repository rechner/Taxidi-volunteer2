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

import os
import sys
import logging
import psycopg2
import hashlib
import datetime

# one directory up
_root_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, _root_dir)
import config

debug = True

#Signaling constants
SUCCESS = 1
OK = 1
FAIL = 2
EMPTY_RESULT = 4
USER_EXISTS = 8
CONSTRAINT_FAILED = 16
UNKNOWN_ERROR = 32
INVALID_PASSWORD = 64
AUTHORIZED = 1
UNAUTHORIZED = 0
NEW = 128
RESET_TABLES = 256

_schema_version = 0

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
    def __init__(self, host, dbname, user, password, location='pyTimeClock', timeout=10):
        logging.getLogger(__name__)
        logging.debug("Setting up database connection")
        self.host = host
        self.dbname = dbname
        self.user = user
        self.password = password
        
        #Create connection:
        try: #TODO: Add SSL/SSH tunnel
            if ':' in host:
                host, port = host.split(':')
            else:
                port = 5432
            self.conn = psycopg2.connect(host=host, database=dbname, 
                user=user, password=password, port=port, connect_timeout=timeout)
                #application_name=location)
                
            self.cursor = self.conn.cursor()
        except psycopg2.OperationalError, e:
            if e.pgcode == '28P01' or e.pgcode == '28000':
                raise DatabaseError(INVALID_PASSWORD)
            elif e.pgcode is None:
                #Usually an issue with the client itself
                logging.error(str(e))
                raise DatabaseError(FAIL, str(e))
            else:
                #Unhandled error.  Show it to the user.
                logging.error(e)
                raise DatabaseError(e.pgcode, e.diag.message_primary)

        logging.info("Created PostgreSQL database instance on host {0}:{1}.".format(host, port))
        logging.debug("Checking for tables and creating them if not present....")
        
        self.InitDb()
        
        self.columns = """id, name, surname, email, salt, hash, home_phone, 
            mobile_phone, sms_capable, dob, license_number, email_verified, 
            newsletter, admin, join_date, last_login, last_seen, 
            last_updated, locked"""

        
    def spawnCursor(self):
        """
        Returns a new cursor object (for multi-threadding use).
        Delete it when done to prevent hogging of db connections.
        """
        return self.conn.cursor()
        
    def commit(self):
        logging.debug('Committed database')
        self.conn.commit()

    def close(self):
        """
        Close the connection and clean up database objects.
        Don't forget to call this before exiting the program.
        """
        self.cursor.close()
        self.conn.close()
        del self.cursor
        del self.conn
        
    def execute(self, sql, args=(''), cursor=None):
        """Executes SQL, reporting debug to the log. For internal use."""
        if debug:
            sql = sql.replace('    ', '').replace('\n', ' ')  #make it pretty
            if args != (''):
                logging.debug(sql % args)
            else:
                logging.debug(sql)
        try:
            self.cursor.execute(sql, args)
            try:
                return self.cursor.fetchall()
            except psycopg2.ProgrammingError:
                return True
        except (psycopg2.ProgrammingError, psycopg2.OperationalError) as e:
            logging.error('psycopg2 returned operational error: {0}'
                .format(e))
            if self.conn:
                self.conn.rollback()    #drop any changes to preserve db.
            raise
            
    def dict_factory(self, row):
        d = {}
        for idx, col in enumerate(self.cursor.description):
            d[col[0]] = row[idx]
            if isinstance(row[idx], str):
                d[col[0]] = row[idx].decode('utf-8')
        return d

    def to_dict(self, a):
        """
        Converts results from a cursor object to a nested dictionary.
        """
        ret = []
        for i in a:
            ret.append(self.dict_factory(i)) #return as a nested dictionary
        return ret
        
    
    def InitDb(self):
        """
        Creates tables for the first time (init schema version 0)
        """
        logging.debug("Enter InitDb()")
        try:
            dbVersion = self.getMeta('schema_version')
            logging.debug("Database schema version: ({0})".format(dbVersion))
        except psycopg2.OperationalError as e:
            #Database hasn't been initialized (or _meta table is missing)
            logging.warn(e)
            self.cursor.set_isolation_level(0) #Enter autocommit mode
            self.upgradeSchema(0)
            
        if dbVersion < _schema_version:
            logging.warn("Database schema version %n is older than code schema version %n", 
                         dbVersion, _schema_version)
            logging.warn("You should backup the database before upgrading.")
            

    def upgradeSchema(self):
        if dbVersion >= _schema_version:
            logging.warn("Database schema version %n is older than code schema version %n", 
                         dbVersion, _schema_version)
            #Get number of versions behind:
            upgradeVersions = range(dbVer+1, curVer+1)
            #logging.warn("Backing up database for schema upgrade.")
            for version in upgradeVersions:
                self.upgradeSchema(version)
            
    def _upgradeSchema(self, version):
        self.warn("Performing schema version upgrade.")
        self.cursor.set_isolation_level(0) #Enter autocommit mode
        self.debug("Enter autocomit mode: set_isolation_level(0)")
        with open(os.join("schema", str(version) + ".sql")) as f:
            self.debug("Execute schema file: {0}".format(f.name))
            try:
                self.cursor.execute(f.read())
            except psycopg2.OperationalError as e:
                logging.error("Database returned operational error.")
                logging.error("Is there a configuration error?")
                logging.error(e)
                raise DatabaseError(RESET_TABLES|FAIL, 
                    "Unable to initialize database schema version "+str(version))
        self.cursor.set_isolation_level(1) #Go back to transaction mode
        self.debug("Exit autocommit mode: set_isolation_level(1)")
            
    #FIXME
    def backupDatabase(self, filename):
        """
        Like the module-level `backupDatabase()`, this attempts a backup using
        connection information in the database instance.
        :param `filename`
        """
        import subprocess
        subprocess.check_call("PGPASSWORD=\"{0}\"; ".format(config.database.password) + 
            config.database.pg_dump + " -C -h " + config.database.hostname + 
            " -p " + str(config.database.port) + " -U " + config.database.user +
            "-f \"" + filename + "\"", shell=True)
            
    def getNestedDictionary(self, resultSet):
        ret = []
        for i in resultSet:
            #Pretty None objects up for display
            if i == None: i = u'—'
            ret.append(self.dict_factory(i)) #return as a nested dictionary
        return ret
        
    #== Data Functions ==
    #=== Activities ===
    """
    Returns all activities as a list of dictionaries
    """
    def getActivities(self):
        logging.debug("Fetch all activities getActivities()")
        a = self.execute("SELECT id, name, admin FROM activities;")
        return self.getNestedDictionary(a)
        
    """
    Returns a dictionary of attributes for a single activity referenced by id
    """
    def getActivity(self, id):
        logging.debug("Fetch activity ({0})".format(id))
        a = self.execute("SELECT id, name, admin FROM activities WHERE id = %s", (id,))
        return self.getNestedDictionary(a)[0]
        
    """
    Pass a list of ID's (string or integer) and will return a list of their 
    corresponding sting names.
    """
    def getActivityNameList(self, IDList):
        IDList = tuple(IDList)
        logging.debug("Get activity name list ({0})".format(id))
        a = self.execute("SELECT name FROM activities WHERE id IN %s;", (IDList,))
        return map(lambda x: x[0], a) #flatten the list
        
    """
    Adds an activity.  Optionally specify an administrator who will receive
    reports about their activity, referenced by user id.
    """
    def addActivity(self, name, admin=None):
        logging.debug(u"Adding activity '{0}' with admin '{1}'".format(name, admin))
        self.execute("INSERT INTO activities(name, admin) VALUES (%s, %s);", 
                     (name, admin))
                     
    """
    Deletes activity by id.
    """
    def deleteActivity(self, id):
        logging.debug("Deleting activity id = {0}".format(id))
        self.execute("DELETE FROM activities WHERE id = %s;", (id,))
    
    #=== Services ===
    def getServices(self):
        logging.debug("Fetch all services getServices()")
        a = self.execute("SELECT id, name, day, start_time, end_time FROM services;")
        return self.getNestedDictionary(a)
        
    """
    Pass a list of ID's (string or integer) and will return a list of their 
    corresponding service names.
    """
    def getServiceNameList(self, IDList):
        IDList = tuple(IDList)
        logging.debug("Get activity name list ({0})".format(id))
        a = self.execute("SELECT name FROM services WHERE id IN %s;", (IDList,))
        return map(lambda x: x[0], a) #flatten the list
        
    def addService(self, name, day, start_time, end_time):
        logging.debug("Adding service '{0}'".format(name))
        self.execute("""INSERT INTO services(name, day, start_time, end_time)
            VALUES (%s, %s, %s, %s);""", (name, day, start_time, end_time))
    
    def deleteService(self, id):
        logging.debug("Deleting service id = {0}".format(id))
        self.execute("DELETE FROM services WHERE id = %s;", (id,))
        
    #=== Meta (settings) keys: ===
    def getMeta(self, key):
        a = self.execute("SELECT int_value, str_value FROM _meta WHERE key = %s;", (key,));
        if a:
            ret = self.getNestedDictionary(a)[0]
        else:
            return None
        if ret['int_value'] is None:
            return ret['str_value']
        else:
            return ret['int_value']
    
    def setMeta(self, key, int_value=None, str_value=None):
        if str_value is not None:
            logging.debug(u"Set meta {0} = '{1}'".format(key, str_value))
        else:
            logging.debug("Set meta {0} = '{1}'".format(key, int_value))
        self.execute("UPDATE _meta SET int_value = %s, str_value = %s WHERE key = %s",
            (key, int_value, str_value))
    
    #=== Statistics ===
    """
        ("id" SERIAL PRIMARY KEY, 
    "person" INT REFERENCES users(id) ON DELETE SET DEFAULT 1, 
    "checkin" timestamp, "checkout" timestamp,
    "service" text[], "activity" text[], "note" text); 
    """
    def doCheckin(self, person, activities, services, note):
        a = self.execute("""INSERT INTO statistics
        (person, checkin, service, activity, note) VALUES 
        (%s, NOW(), %s, %s, %s);""", (person, services, activities, note))
        
    
    #=== Users ===
    #==== CRUD ====
    def addUser(self, name, surname, email=None, home_phone=None, mobile_phone=None, \
                sms=False, dob=None, license_number=None, email_verified=False, \
                newsletter=False, admin=False, join_date=None,
                last_login=None, last_seen=None, last_updated=None,
                locked=False, password=None):
        
        salt = os.urandom(42).encode('base_64').strip('\n') #Get a salt
        #Login disallowed by setting a non-computable hash:
        if password == None:
            hash = "disabled"
        else:
            hash = hashlib.sha256(password).hexdigest()
            
        if join_date == None:
            join_date = datetime.datetime.now()
            
        self.execute("""INSERT INTO users({0}) VALUES 
            (DEFAULT, %(name)s, %(surname)s, %(email)s, %(salt)s, %(hash)s,
             %(home_phone)s, %(mobile_phone)s, %(sms)s, %(dob)s, %(license)s,
             %(email_verified)s, %(newsletter)s, %(admin)s, %(join_date)s,
             %(last_login)s, %(last_seen)s, %(last_updated)s, %(locked)s);""".format(self.columns),
            {'name': name, 'surname': surname, 'email': email, 'salt': salt,
             'hash': hash, 'home_phone': home_phone, 'mobile_phone': mobile_phone,
             'sms': sms, 'dob': dob, 'license': license_number,
             'email_verified': email_verified, 'newsletter': newsletter,
             'admin': admin, 'join_date': join_date, 'last_login': last_login,
             'last_seen': last_seen, 'last_updated': last_updated,
             'locked': locked})
             
    def deleteUser(self, id):
        self.execute("DELETE FROM users WHERE id = %s", (id,))
        
    def getUserByID(self, id):
        a = self.execute("SELECT {0} FROM users WHERE id = %s;".format(self.columns), (id,))
        if len(a) == 0:
            return None
        return self.getNestedDictionary(a)[0]
    
    #==== Search ====
    """
    Generic search function.  Searches by last four digits of phone number, name,
    or entire phone number.
    """
    def search(self, query):
        a = ()
        if query == '':
            return a
        if query.isdigit() and (len(query) == 4 or len(query) == 7) or query[0] == '+':
            #Looks like the last four digits of a phone number:
            a = self.searchPhone(query)
        if not query.isdigit():  #Search in names.
            a = self.searchName(query)
            if len(a) == 0:
                #Search partial names, if no exact name was matched:
                a = self.searchName(query+'%')
                
        return a
    """
    Searches by name.
    Returns *.  '*' and '%' are treated as wild-card characters, and will
    search using the LIKE operator.
    """
    def searchName(self, query):        
        if ("%" in query) or ("*" in query):
            query = query.replace("*", "%")
            
        a = self.execute("""SELECT DISTINCT {0} FROM "users" WHERE
                name ILIKE %s OR surname ILIKE %s;""".format(self.columns),
                (query,)*2)
                
        return self.getNestedDictionary(a)
                        
    def searchPhone(self, query):
        query = str(query)
        
        if len(query) == 4:
            #Search by last four:
            query = '%' + query
            a = self.execute("""SELECT DISTINCT {0} FROM "users"
                                WHERE home_phone LIKE %s
                                OR mobile_phone LIKE %s
                                ORDER BY surname;
                                """.format(self.columns), (query,)*2)
                                
        elif query.isdigit() and len(query) == 10 \
            and query[0] not in '01' and query[3] not in '01':  #US: '4805551212'
            a = self.execute("""SELECT DISTINCT {0} FROM "users"
                                WHERE home_phone = %s
                                OR mobile_phone = %s
                                ORDER BY surname;
                                """.format(self.columns), (query,)*2)
                                
        elif len(query) == 12 and query[3] in '.-/' \
          and query[7] in '.-/':  #US: '334-555-1212'
            trans = Translator(delete='+(-)./ ')
            query = trans(query.encode('ascii'))
            a = self.execute("""SELECT DISTINCT {0} FROM "users"
                                WHERE home_phone = %s
                                OR mobile_phone = %s
                                ORDER BY surname;
                                """.format(self.columns), (query,)*2)
                                
        elif query[0] == '(' and len(query) == 14: #US: (480) 555-1212
            query = query[1:4] + query[6:9] + query[10:14]
            a = self.execute("""SELECT DISTINCT {0} FROM "users"
                                WHERE home_phone = %s
                                OR mobile_phone = %s
                                ORDER BY surname;
                                """.format(self.columns), (query,)*2)
                                
        elif query[0] == '+':  #International format
            trans = Translator(delete='+(-)./ ')
            query = trans(query.encode('ascii'))
            a = self.execute("""SELECT DISTINCT {0} FROM "users"
                                WHERE home_phone = %s
                                OR mobile_phone = %s
                                ORDER BY surname;
                                """.format(self.columns), (query,)*2)
                                
        elif len(query) == 7:
            #Search by last seven:
            query = '%' + query
            a = self.execute("""SELECT DISTINCT {0} FROM "users"
                                WHERE home_phone LIKE %s
                                OR mobile_phone LIKE %s
                                ORDER BY surname;
                                """.format(self.columns), (query,)*2)
                                
        else:
            logging.warn("Search key {0} probably isn't a phone number.")
            a = self.execute("""SELECT DISTINCT {0} FROM "users"
                                WHERE home_phone = %s
                                OR mobile_phone = %s
                                ORDER BY surname;
                                """.format(self.columns), (query,)*2)
                                
        return self.getNestedDictionary(a)

    
    
    
#FIXME: .pgpass will probably have to go into user's home directory
def backupDatabase(filename):
    """
    Attempts to backup the database by running pg_dump with the stored
    connection information and storing the resulting file in a specified
    location.
    :param `filename`
    """
    import subprocess
    import tempfile
    passfile = tempfile.NamedTemporaryFile(delete=False)
    with passfile as f:
        f.write(config.database.hostname + ":" + str(config.database.port) + ":" +
                  config.database.user + ":" + config.database.password+"\n")
    subprocess.check_call("PGPASSFILE={0} ".format(passfile.name) + 
        config.database.pg_dump + " -C -h " + config.database.hostname + 
        " -p " + str(config.database.port) + " -U " + config.database.user +
        " -f " + filename, shell=True)
            

class DatabaseError(Exception):
    def __init__(self, code, value=''):
        if value == '':
            self.error = 'Generic database error.'
            if code == EMPTY_RESULT:
                self.error = 'Query returned empty result'
            elif code == CONSTRAINT_FAILED:
                self.error = 'Unique key constraint failed.'
            elif code == USER_EXISTS:
                self.error = 'The user specified already exists.'
            elif code == INVALID_PASSWORD:
                self.error = 'Invalid username, password, or authorization specification.'
        else:
            self.error = str(value).replace('\t', '').capitalize()
        self.code = code
        Exception.__init__(self, self.error)
        logging.error(self.error)
    def __str__(self):
        return str(self.error).replace('\t', '').capitalize()

"""
Thrown whenever the schema version of the database doesn't match that of
this code.  Notify user to backup and upgrade before continuing.
"""
class SchemaVersionException(Exception):
    pass

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    #db = Database("127.0.0.1:15432", "volunteers", "volunteers", "LamePass")
    db = Database("127.0.0.1:15432", "volunteers", "volunteers", "lamepass") #GITIGNORE
    
    #~ db.addActivity('Parking')
    #~ db.addActivity(u'Café')
    #~ db.addActivity('Greeter')
    #~ db.commit()
    #~ 
    #~ activities = db.getActivities()
    #~ for activity in activities:
        #~ db.deleteActivity(activity['id'])
    #~ print db.getActivities()
    #~ db.commit()
    #~ 
    #~ db.addService('First Service', 0, '08:00', '10:29')
    #~ db.addService('Second Service', 0, '10:30', '12:00')
    #~ db.commit()
    #~ services = db.getServices()
    #~ import pprint
    #~ pprint.pprint(services)
    #~ for service in services:
        #~ db.deleteService(service['id'])
    #~ db.commit()
    
    #db.addUser('Zachary', 'Sturgeon', 'jkltechinc@gmail.com') #GITIGNORE
    #~ db.addUser('John', 'Smith', 'email@example.com', home_phone="(317) 455-5832")
    #~ db.commit()
    
    #~ print db.getActivity(60)
    #~ print db.search("1231213212")
    
    #~ print db.getActivityNameList((61, 59, 60))
    
    db.close() 
   
