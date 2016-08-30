#! /usr/bin/env python3

##
## IMPORTS
##

import configparser
import dbIO
import uuid
import glob
import json
import logging
import re
from datetime import datetime
from processing import Html, Docx, MemoHandler

##
## CONSTANTS and VARIABLES
##

config = configparser.ConfigParser()
config.read("../data/default.ini")

if config["DEFAULT"]["log_level"] == "debug":
  logging.basicConfig(level=logging.DEBUG)
else:
  logging.basicConfig(level=logging.INFO)

DOC_DIR = config["DEFAULT"]["root_dir"] + config["scraping"]["write_dir"]

# doc loading -
# country_doc = "../data/countries.json"
# org_doc = "../data/organization.json"

# with open(country_doc, "r") as d:
#   c_list = json.load(d)

# logging.info("c_list loaded")

# with open(org_doc, "r") as d:
#   o_list = json.load(d)

# logging.info("o_list loaded")

# dummy_data = True

##
## FUNCTIONS
##

def main():
  pipe = DataIngest()
  pipe.ingest()
  pipe.convert()
  pipe.load()

def _processDoc(document,
               doc_fmt,
               doc_type,
               encoding="latin-1",
               # depth_func=[0,1],
               has_footer=False,
               start=None):
  '''Processes document according to the format and type specified in doc_fmt and doc_type'''

  logging.debug("doc_type is %s ; doc_fmt is %s" %(doc_type, doc_fmt))

  # set format and intake
  if doc_fmt == "html":
    logging.info("doc format is html")
    doc = Html(document)
    doc.convert(encoding=encoding)
    # depth_func = depth_func
    # doc.tidy(depth_func)
    doc.tidy()

  elif doc_fmt == "docx":
    logging.info("doc format is docx")
    pass

  # pass doc to type parser
  if doc_type == "memo":
    logging.info("doc type is memo")
    type_ = MemoHandler(file_name=doc.file_name, data=doc.data, has_footer=has_footer)
    type_.parse(start=start)

  return type_.output


def _batchProcess(doc_dir, doc_fmt, doc_type):
  docs = glob.glob(doc_dir + "/*")
  # logging.info(docs)
  doc_list = []
  for doc in docs:
    logging.debug(doc)
    d_ = _processDoc(doc, doc_fmt, doc_type)
    doc_list.append(d_)
  return doc_list

##
## CLASSES
##

class DataIngest(object):
  def __init__(self, directory=DOC_DIR):
    # self.doc = doc
    self.docs = directory
    logging.info("directory is %s" % self.docs)
    self.data = []
    # if self.doc is not None and self.docs is not None:
    #   logging.warn("Single doc and list of docs specified")
      # self.docs.append(self.doc)

  def ingest(self, doc_fmt="html", doc_type="memo"):
    self.data = _batchProcess(self.docs, doc_fmt, doc_type)

  def convert(self):

    self.d_list = []

    for doc in self.data:
      # d_ must be kept in sync with schema.sql (among others)
      d_ = {
        "uid": str(uuid.uuid4()),
        "u_date": datetime.now().strftime('%Y-%m-%d'),
        "doc_date": doc["header"]["doc_date"],
        "full_text": doc["full_text"],
        "html": doc["html"],
        "file_name": doc["file_name"]
      }

      if doc["header"] is not None:
        # include header values in d_
        d_["addressee"] = doc["header"]["addressee"]
        d_["classification"] = doc["header"]["classification"]
        d_["category"] = doc["header"]["category"]
        d_["from_bur"] = doc["header"]["from_bur"]
        d_["from_auth"] = doc["header"]["from_auth"]
        d_["title"] = doc["header"]["title"]
      else:
        pass
      #   # insert dummy values for those required fields and None for not-required
      #   d_["addressee"] =
      #   d_["classification"] = "SBU"
      #   d_["category"] =
      #   d_["from_bur"] =
      #   d_["from_auth"] =
      #   d_["title"] =

      if doc["footer"] is not None:
        d_["has_attachments"] = doc["footer"]["has_attachments"],
        d_["attach_urls"] = doc["footer"]["attach_urls"],
        d_["approved_bur"] = doc["footer"]["approved_bur"],
        d_["approved_name"] = doc["footer"]["approved_name"],
        d_["draft_bur"] = doc["footer"]["draft_bur"],
        d_["draft_name"] = doc["footer"]["draft_name"],
        d_["draft_ext"] = doc["footer"]["draft_ext"],
        d_["draft_phone"] = doc["footer"]["draft_phone"],
        d_["clear_blob"] = doc["footer"]["clear_blob"]
      else:
        d_["has_attachments"] = 0

      self.d_list.append(d_)

  def load(self):

    db = dbIO.SQLio()
    db.connect()

    for d_ in self.d_list:
      keys = ",".join(d_.keys())
      logging.debug(keys)

      qs = ",".join(list('?' * len(d_)))
      logging.debug(qs)

      values = tuple(d_.values())
      logging.debug(values)

      db.conn.execute("insert or replace into document (" + keys + ") values (" + qs + ");", values)

    db.conn.commit()
    db.conn.close()

##
## IFMAIN
##

if __name__ == '__main__':
  main()

