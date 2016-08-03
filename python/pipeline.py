#! /usr/bin/env python3

##
## IMPORTS
##

import configparser
import doc2web as dw
import docsim
import dbIO
import uuid
import glob
import json
import logging
import re
from datetime import datetime

##
## CONSTANTS and VARIABLES
##

logging.basicConfig(level=logging.DEBUG)

config = configparser.ConfigParser()
config.read("../data/default.ini")

# doc loading -
country_doc = "../data/countries.json"
org_doc = "../data/organization.json"

with open(country_doc, "r") as d:
  c_list = json.load(d)

logging.info("c_list loaded")

with open(org_doc, "r") as d:
  o_list = json.load(d)

logging.info("o_list loaded")

##
## FUNCTIONS
##

def main():
  pass

def processDoc(document):
  doc = dw.Doc2Web(document)
  doc.convert()
  return (doc.doc_path, doc.clean_html, doc.content, doc.title)

def batchProcessDocs(doc_dir):
  docs = glob.glob(doc_dir + "*docx")
  doc_list = []
  for doc in docs:
    d_ = processDoc(doc)
    doc_list.append(d_)
  return doc_list

##
## CLASSES
##

class DataIngest(object):
  def __init__(self, doc=None, directory=None, category=None):
    # self.doc = doc
    self.docs = directory
    self.data = []
    self.category = category
    # if self.doc is not None and self.docs is not None:
    #   logging.warn("Single doc and list of docs specified")
      # self.docs.append(self.doc)

    if self.docs:
      self.batch_mode = True


  def ingest(self):
    if self.batch_mode:
      self.data = batchProcessDocs(self.docs)
    # else:
    #   self.data = processDoc(self.doc)


  def load(self):

    db = dbIO.SQLio()
    db.connect()

    for doc in self.data:
      # d_ must be kept in sync with schema.sql (among others)
      d_ = {
        "uid": str(uuid.uuid4()),
        "category" : self.category,
        "u_date" : datetime.now().isoformat(),
        "title" : doc[3],
        "full_text" : doc[2],
        "html" : doc[1].decode("utf-8"),
        "doc_path" : doc[0]
      }
      logging.info(d_)

      keys = ",".join(d_.keys())
      logging.info(keys)

      qs = ",".join(list('?' * len(d_)))
      logging.info(qs)

      values = tuple(d_.values())
      logging.info(values)

      db.conn.execute("insert or replace into document (" + keys + ") values (" + qs + ");", values)

    db.conn.commit()
    db.conn.close()



##
## IFMAIN
##

if __name__ == '__main__':
  main()

