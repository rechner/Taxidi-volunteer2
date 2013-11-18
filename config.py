#!/usr/bin/env python
# Sample configuration file. 
import platform

class Config(object):
    DB_HOSTNAME = "localhost"
    DB_PORT = 5432
    DB_NAME = "volunteers"
    DB_USER = "volunteers"
    DB_PASSWORD = "lamepass" #GITIGNORE
    PG_DUMP = "/usr/bin/pg_dump"
    PG_PSQL = "/usr/bin/psql"
    if platform.system() == "Windows":
        #FIXME: hope it's in the PATH
        PG_DUMP = "pg_dump.exe"
        PG_PSQL = "psql.exe"
    
class DevelopmentConfig(Config):
    DEBUG = True

