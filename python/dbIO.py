

##
## IMPORTS
##

import sys
import sqlite3
import configparser
import logging

##
## CONSTANTS and VARIABLES
##

config = configparser.ConfigParser()
config.read("../data/default.ini")

# to-do use config for logging level
logging.basicConfig(level=logging.DEBUG)

ROOT_DIR = config["DEFAULT"]["root_dir"]
DB_FILE = config["sql"]["db_file"]

DB = ROOT_DIR + DB_FILE

SCHEMA_FILE = config["sql"]["schema"]
SCHEMA = ROOT_DIR + SCHEMA_FILE

##
## FUNCTIONS
##

def initializeDB(database):
  db = SQLio(database)
  db.connect()
  with open(SCHEMA, "r") as s:
    schema = s.read()
    db.conn.executescript(schema)
    db.conn.commit()
    db.conn.close()

def main():
    '''Running as a CLI tool, the assumption is that you are creating / rewriting the database'''
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["init", "purge"], help="Initialize the database, or purge it.")

    args = parser.parse_args()

    if args.action == "init":
      initializeDB(DB)
      sys.exit(0)
    elif args.action == "purge":
      initializeDB(DB)
      sys.exit(0)
    else:
      pass
      sys.exit(2)

##
## CLASSES
##

class SQLio:
  '''
  Handles connection (reads, mostely) to SQL DB
  '''
  def __init__(self, db=DB):
    self.db = db
    self.conn = None
    self.cur = None

  def connect(self):
    self.conn = sqlite3.connect(self.db)
    self.cur = self.conn.cursor()

##
## IFMAIN
##

if __name__ == '__main__':
  main()

