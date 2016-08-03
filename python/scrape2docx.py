#! /usr/bin/env python3

##
## IMPORTS
##

import json
import re
from pydocx import PyDocX
from docx import Document
from bs4 import BeautifulSoup
from lxml import etree as et
from lxml import html as lhtml
from lxml.html.clean import Cleaner
import requests
import logging
import configparser

##
## CONSTANTS and VARIABLES
##

logging.basicConfig(level=logging.DEBUG)

config = configparser.ConfigParser()
config.read("../data/default.ini")

HTML_IDS = config["scraping"]["html_ids"].split(",")
WRITE_DIR = config["DEFAULT"]["root_dir"] + config["scraping"]["write_dir"] + "/"

# doc loading -
country_doc = "../data/countries.json"
org_doc = "../data/organization.json"

with open(country_doc, "r") as d:
  c_dict = json.load(d)

c_list = list(c_dict.values())
logging.info("c_list loaded")

with open(org_doc, "r") as d:
  o_dict = json.load(d)

o_list = list(o_dict.values())
logging.info("o_list loaded")

##
## FUNCTIONS
##

def batchScrape(lst, html_ids):
  '''Accepts a list of URLs and an HTML element id'''
  for item in lst:
    d = Scrape2Docx()
    d.pipeline(item, html_ids)

def main():
  pass

##
## CLASSES
##

class Scrape2Docx(object):
  def __init__(self):
    self._b = None
    self._text = None
    self._text_list = None

  def fetch(self, url):
    self.url = url
    logging.info(url)
    r_ = requests.get(url)

    if r_.status_code != 200:
      logging.warn("returned status code: " + str(r_.status_code))
      return
    else:
      html = r_.text
      self._b = BeautifulSoup(html, 'html.parser')
      logging.info(url + " fetched...")

  def parse(self, html_ids):
    self.h_ids = html_ids
    if self._b is None:
      logging.warn("URL has not been fetched!") # to do
      return
    else:
      for id_ in self.h_ids:
        t_ = self._b.find(id=id_) # target
        if t_ is None:
          logging.warn(id_ + " not found in " + self.url)
        else:
          logging.info("Length of located content in scrape:" + str(len(t_)))
          d_ = lhtml.fromstring(str(t_))  # document

          # lxml cleaner to tidy
          cleaner = Cleaner(style=True)
          c_ = cleaner.clean_html(d_)

          # remove styles, scripts
          # for s_ in d_.xpath("//style"):
          #   s_.getparent().remove(s_)

          # for s_ in d_.xpath("//script"):
          #   s_.getparent().remove(s_)

          # this is the raw text content of the page
          self._html = BeautifulSoup(et.tostring(c_), 'html.parser')
          self._text = self._html.get_text("\n")
          logging.info("Length of extracted text: " + str(len(self._text)))
          self._text_list = [ l for l in self._text.split("\n") if l != "" ]

  def docxify(self, header_len=75, sub_header_level=3, out_path=WRITE_DIR):
    file_name = re.split("/", self.url)[-1]
    if len(file_name) == 0:
      file_name = re.split("/", self.url)[-2]
    logging.info("Writing to file: " + file_name)

    if self._text_list is None:
      logging.warn("_test_list does not exist!")
    else:
      self.document = Document()
      self.document.add_heading(self._text_list[0])
      for line in self._text_list[1:-1]:
        if len(line) >= header_len:
          # infer that item is a header
          self.document.add_paragraph(line)
        else:
          self.document.add_heading(line, sub_header_level)
      self.document.save(out_path + file_name + ".docx")

  def pipeline(self, url, html_ids):
    self.fetch(url)
    self.parse(html_ids)
    self.docxify()

##
## IFMAIN
##

if __name__ == '__main__':
  main()

