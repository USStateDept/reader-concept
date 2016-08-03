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

##
## CONSTANTS and VARIABLES
##

logging.basicConfig(level=logging.DEBUG)

TEST_DOC = "../test/Test_Document.docx"
DOC_TAG = "body"
HTML_CLASS = "document"

CLASSIFICATIONS = ["unclassified", "sensitive but unclassified", "confidential", "secret", "noforn"]
PARA_MARKINGS = ["U", "SBU", "C", "S", "noforn"]

header = {
  "classification": None,
  "doc_date": None,
  "addressee": None,
  "category": None,
  "from_bur": None,
  "from_auth": None,
  "title": None
}

body = []

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
## FUNCTIONS
##

def main():
  pass

##
## CLASSES
##

class Doc2Web(object):
  def __init__(self, docx, doc_tag=DOC_TAG, _class=HTML_CLASS):
    self.doc_path = docx
    self.raw_html = None
    self.clean_html = None
    self.content = None
    self.doc_tag = doc_tag
    self._class = _class
    self._header = header
    self._body_lst = body
    self._footer = footer

  def _parse_header(self, header_len=10):
    '''parses header (first n lines) for the content expected in official
    documents '''
    for line in self._bs.contents[:header_len]:
      for c in CLASSIFICATIONS:
        if re.match("^"+c, line.get_text().lower()):
          # we are on the line with the classification marking
          self._header["classification"] = c
          date = re.search("[JFMASOND][a-z]* [0-9]*, [0-9]...", line.get_text())
          if date:
            self._header["doc_date"] = date.group(0)

      if re.search(" FOR ", line.get_text()):
        # matches line that indicates addressee
        category, addressee = line.get_text().split(" FOR ")
        self._header["category"] = category
        self._header["addressee"] = addressee

      elif re.match("^FROM:", line.get_text()):
        # matches line that indicates from
        # currently assumes single from. would need to add in additional split
        # to accomodate additional authors
        from_bur, from_auth = re.split(" [-–] ", line.get_text().split("FROM:")[1])
        self._header["from_bur"] = from_bur
        self._header["from_auth"] = from_auth

      elif re.match("^SUBJECT:", line.get_text()):
        # matches the subject line
        title = re.split("\([A-Z]*\) ", line.get_text())[1]
        self._header["title"] = title

    for key in self._header:
      if self._header[key] is None:
        logging.warn("%s : could not locate header value for %s, adding 'unknown'" % (self.doc_path, key))
        self._header[key] = "unknown"

  def _get_linenos(self, *regex):
    '''searches document for regex matches, returns list of line numbers'''
    results = []
    for i in range(len(self._bs.contents)):
      for patt in regex:
        if re.search(patt, self._bs.contents[i].get_text()):
          results.append(i)
    return results

  def _parse_doc(self):
    '''identify the bounds of the core document, and parse it into a list of html strings'''
    l_ = self._get_linenos("^SUBJECT:", "^Approved:")
    try:
      assert len(l_) == 2
    except AssertionError:
      logging.warn("%s : could not determine bounds of document body" % self.doc_path)
      self.body = ["<p>Could not load document - check logs</p>"]
      return

    start = l_[0] + 1
    end = l_[1]

    # tidy the body html
    cleaner = Cleaner()
    for element in self._bs.contents[start:end]:
      html_str = str(element)
      d_ = lhtml.fromstring(html_str)
      c_ = cleaner.clean_html(d_)
      c_str = et.tostring(c_).decode('utf-8')

      # add paragraph classification markings
      for mark in PARA_MARKINGS:
        patt = ">\\(" + mark + "\\)" # proper escape for literals
        repl = '><span class="label-' + mark.lower() + '">' + mark + '</span>'
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
    attach_check = self._get_linenos("^Attachments:")
    if attach_check != []:
      # we have attachments
      self._footer["has_attachments"] = 1
      # tbd - get URLs for attachment docs
    else:
      self._footer["has_attachments"] = 0
      self._footer["attach_urls"] = None

    # parse and structure clearances
    start_l = self._get_linenos("^Approved:")
    try:
      assert len(start_l) == 1
    except:
      logging.warn("%s : could not locate start of clearances - skipping" % self.doc_path)
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
        c_l = self._get_linenos("^Cleared:")
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

  def convert_parse(self, doc_type=None):
    '''convert doc from docx into html and parse into structured fields'''
    self.raw_html = PyDocX.to_html(self.doc_path)
    bs = BeautifulSoup(self.raw_html, 'html.parser')
    self._bs = bs.body
    if None in self._header.values():
      self._parse_header()

    if self._body_lst == []:
      self._parse_doc()

    if None in self._footer.values():
      self._parse_footer()

    # we now have the header, body, and footer content


  def convert(self):
    '''dev/prototype - should not be used'''
    # simple convert to html
    # converts images to inline data
    self.raw_html = PyDocX.to_html(self.doc_path)

    doc = lhtml.fromstring(self.raw_html)
    # remove all styles
    # for s_ in doc.xpath("//style"):
    #   s_.getparent().remove(s_)

    # locate core of document
    body = doc.find(self.doc_tag)

    # stringify core doc
    b_string = et.tostring(body)

    # re-read as xmltree
    b_ = lhtml.fromstring(b_string)

    # add class element and convert to string
    b_.attrib["class"] = self._class
    self.clean_html = et.tostring(b_)

    # extract text content
    s_ = BeautifulSoup(self.clean_html, 'html.parser')
    self.content = s_.get_text(" ")
    self.title = s_.h1.get_text()

  def dumps(self):
    if self.content is not None:
      return self.content

##
## IFMAIN
##

if __name__ == '__main__':
  main()

##
## SCRATCH
##


