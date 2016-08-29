#! /usr/bin/env python3

##
## IMPORTS
##

from pydocx import PyDocX
from lxml import etree as et
from lxml import html as lhtml
from lxml.html.clean import Cleaner
from bs4 import BeautifulSoup
import logging
import re
import configparser
from copy import deepcopy

##
## CONSTANTS and VARIABLES
##

# logging.basicConfig(level=logging.DEBUG)

DOC_TAG = "body"
HTML_CLASS = "document"

config = configparser.ConfigParser()
config.read("/home/ubuntu/workspace/data/default.ini")

if config["DEFAULT"]["log_level"] == "debug":
  logging.basicConfig(level=logging.DEBUG)
else:
  logging.basicConfig(level=logging.INFO)

CLASSIFICATIONS = config["DEFAULT"]["classifications"].split(",") # ["unclassified", "sensitive but unclassified", "confidential", "secret", "noforn"]
PARA_MARKINGS = config["DEFAULT"]["para_markings"].split(",") # ["U", "SBU", "C", "S", "noforn"]

# deafults for header, footer, and body

# header should be None, unless processing docs that are of a known, unspecified type (eg, dummy data)
header = {
  "classification": None,
  "doc_date": None,
  "addressee": "The Secretary",
  "category": "Information Memo",
  "from_bur": None,
  "from_auth": None,
  "title": None
}

# body should be empty list
body = []

# footer should be none, with the exception of "clear_blob", which is empty list
footer = {
  "has_attachments": None,
  "attach_urls": None,
  "approved_bur": None,
  "approved_name": None,
  "draft_bur": None,
  "draft_name": None,
  "draft_ext": None,
  "draft_phone": None,
  "clear_blob": [] # plain list of clearances
}

##
## CLASSES
##

class MemoHandler(object):
  def __init__(self,
               file_name=None,
               data=None,
               doc_tag=DOC_TAG,
               _class=HTML_CLASS,
               has_header=True,
               has_footer=True):
    self.file_name = file_name
    self._bs = data
    self.clean_html = None
    self.content = None
    self.doc_tag = doc_tag
    self._class = _class
    self.has_header = has_header
    self._header = deepcopy(header)
    self._body_lst = deepcopy(body)
    self.has_footer = has_footer
    self._footer = deepcopy(footer)
    self.length = len(data.contents)

  def _parse_header(self, header_len=5):
    '''parses header (first n lines) for the content expected in official
    documents '''
    for line in self._bs.contents[:header_len]:
      for c in CLASSIFICATIONS:
        # once classification is set, we do not attempt to re-set it
        if self._header["classification"] is None:
          if re.search(c, line.get_text(" ").lower()):
            # we are on the line with the classification marking
            self._header["classification"] = c
            date = re.search("[JFMASOND][a-z]* [0-9]*, [0-9]...", line.get_text(" "))
            if date:
              self._header["doc_date"] = date.group(0)

            # break on first classification encountered
            break

      if re.search(" FOR ", line.get_text()):
        # matches line that indicates addressee
        category, addressee = line.get_text().split(" FOR ")
        self._header["category"] = category
        self._header["addressee"] = addressee

      elif re.match("^FROM:", line.get_text()):
        # matches line that indicates from
        # currently assumes single from. would need to add in additional split
        # to accomodate additional authors
        from_l = re.split(" [-–] ", " - ".join(line.get_text().split("FROM:")[1].split(" and ")).strip())
        # assert len(from_l) % 2 == 0 # there are co-authored docs from BUR - Person 1 and Person 2

        # from_bur, from_auth = re.split(" [-–] ", line.get_text().split("FROM:")[1])
        self._header["from_bur"] = from_l[0].strip()
        self._header["from_auth"] = from_l[1].strip()

      elif re.match("SUBJECT:", line.get_text()):
        # matches the subject line
        title = re.split(": ", line.get_text(), maxsplit=1)[1]
        self._header["title"] = title.strip()

    for key in self._header:
      if self._header[key] is None:
        logging.warn("%s : could not locate header value for %s, adding 'unknown'" % (self.file_name, key))
        self._header[key] = "unknown"

  def _get_lineno(self, regex):
    '''searches document for regex matches, returns list of indices (line numbers)'''
    results = []
    for i in range(len(self._bs.contents)):
      if re.search(regex, self._bs.contents[i].get_text()):
        results.append(i)
    return results

  def _parse_doc(self, is_dummy=False, start_regex="^SUBJECT:", end_regex=None, start=None):
    '''identify the bounds of the core document, and parse it into a list of html strings'''
    if not is_dummy:
      if start is None:
        start = self._get_lineno(start_regex)
        # end = self._get_lineno(end_regex)
        try:
          assert len(start) > 0
          start = start[0] + 1
        except AssertionError:
          logging.warn("%s : could not determine start of document body" % self.file_name)
          self._body_lst.append("<p>Could not locate start of document - check logs</p>")
      else:
        start = start

      if end_regex is not None:
        end = self._get_lineno(end_regex)
        try:
          assert len(end) > 0
          end = end[0]
        except AssertionError:
          logging.warn("%s : could not determine start of document body" % self.file_name)
          self._body_lst.append("<p>Could not locate start of document - check logs</p>")
      else:
        end = self.length

    else:
      # for dummy data, use the whole document
      start = 1
      end = self.length

    # tidy the body html
    cleaner = Cleaner()
    for element in self._bs.contents[start:end]:
      html_str = str(element)
      d_ = lhtml.fromstring(html_str)
      c_ = cleaner.clean_html(d_)
      c_str = et.tostring(c_).decode('utf-8')

      # add paragraph classification markings
      for mark in PARA_MARKINGS:
        patt = "\\(" + mark + "\\)" # proper escape for literals
        repl = '<span class="label label-' + mark.lower() + '">' + mark + '</span>'
        c_str = re.subn(patt, repl, c_str)[0] # re-assign same c_str variable to accumiate labels

      self._body_lst.append(c_str)

    # we now have the body isolated and tagged, need to convert it into single html element
    div_open = '<div class="' + self._class + '">'
    div_close = '</div>'
    body_str = " ".join([div_open] + self._body_lst + [div_close])
    self.html = BeautifulSoup(body_str, 'html.parser').prettify()
    self.full_text = BeautifulSoup(body_str, 'html.parser').get_text(" ")

  def _parse_footer(self):
    '''parse footer (clearance, etc.) and attachment info'''
    # check for attachments
    attach_check = self._get_lineno("^Attachments:")
    if attach_check != []:
      # we have attachments
      self._footer["has_attachments"] = 1
      # tbd - get URLs for attachment docs
    else:
      self._footer["has_attachments"] = 0
      self._footer["attach_urls"] = None

    # parse and structure clearances
    start_l = self._get_lineno("^Approved:")
    try:
      assert len(start_l) == 1
    except:
      logging.warn("%s : could not locate start of clearances - skipping" % self.file_name)
      return

    start = start_l[0]
    for element in self._bs.contents[start:]:
      if re.match("^Approved:", element.get_text()):
        # we have an approval line
        approved_bur, approved_name = re.split(" [-–] ", element.get_text().split(":")[1])
        self._footer["approved_bur"] = approved_bur
        self._footer["approved_name"] = approved_name
      elif re.match("^Drafted:", element.get_text()):
        # we have a drafter line
        data = element.get_text().split(":", 1)[1]
        person_info, contact_info = data.split(",")
        draft_bur, draft_name = re.split(" [-–] ", person_info)
        draft_ext = re.search("[0-9]-[0-9]...", contact_info).group(0)
        draft_phone = re.search("[0-9]..-[0-9]..-[0-9]...", contact_info).group(0)
        self._footer["draft_bur"] = draft_bur
        self._footer["draft_name"] = draft_name
        self._footer["draft_ext"] = draft_ext
        self._footer["draft_phone"] = draft_phone
      elif re.match("^Cleared:", element.get_text()):
        # we have entered the clearances
        c_l = self._get_lineno("^Cleared:")
        c_ = c_l[0]

        # get first line of clearances
        # remove the "cleared" comment from the line
        l1 = [ self._bs.contents[c_].get_text().split(": ")[1] ]

        # get rest
        l2 = [ e.get_text() for e in self._bs.contents[c_+1:] ]
        l = l1 + l2
        self._footer["clear_blob"] = l
        # force return to halt iteration
        # we expect clearances to be the last content
        return

  def parse(self, verbose=False, is_dummy=False, start=None):
    '''parse doc into structured fields'''
    # this assumes that the data are in "official" memo format
    if self.has_header:
      self._parse_header()

    if self._body_lst == []:
      self._parse_doc(is_dummy=is_dummy, start=start)

    if self.has_footer:
      self._parse_footer()

    # we now have the header, body, and footer content
    # write it all to output
    self.output = {}
    if self.has_header:
      self.output["header"] = self._header
      if None in self._header.keys():
        logging.warn("Header section has missing values - check .output")
    else:
      self.output["header"] = None
      logging.info("header not included - not written to .output")

    self.output["html"] = self.html
    self.output["full_text"] = self.full_text
    self.output["file_name"] = self.file_name

    if self.has_footer:
      self.output["footer"] = self._footer
      if None in self._footer.keys():
        logging.warn("Footer section has missing values - check .output")
    else:
      self.output["footer"] = None
      logging.info("footer not included - not written to .output")

    if verbose:
      return self.output

##
## SCRATCH
##

'''
from processing import Html
doc = "../scratch/0102201360309944.htm"
html = Html(doc)
html.convert(encoding="latin-1")
depth_func = [0,1]
html.tidy(depth_func)

from processing import MemoHandler
memo = MemoHandler(file_name=html.file_name, data=html.data, has_footer=False)
memo.parse(start=3, end=memo.length)

'''