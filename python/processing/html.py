

##
## IMPORTS
##

import re
from pydocx import PyDocX
from bs4 import BeautifulSoup
import lxml.html
import logging
import configparser

# to resolve paring issues using isinstance()
import bs4

##
## CONSTANTS and VARIABLES
##

config = configparser.ConfigParser()
config.read("/home/ubuntu/workspace/data/default.ini")

# if config["DEFAULT"]["log_level"] == "debug":
logging.basicConfig(level=logging.DEBUG)
# else:
#   logging.basicConfig(level=logging.INFO)

CHARS = ["\xa0"]

REGEX = [("SUBJECT\s?:", "SUBJECT:"), ("FROM\s?:", "FROM:")]

classification_re = config["DEFAULT"]["classifications"].upper().split(",")

regex = REGEX + list(zip(classification_re, classification_re))

##
## FUNCTIONS
##

def _fix_header(data_obj, regex=regex, header_len=3):
  # first check doc len to make sure it is not too short
  if len(data_obj) < header_len:
    header_len = len(data_obj) - 1
  '''
  Algorithm:
  - regex is an ORDERED list of regular expressions and the values to which
    they map. Example:

      [("FROM\s+:", "FROM:")]
  - order is from LAST expected regex to FIRST expected regex
  For each line in the header,
    if the line matches a regular expression,
      split on that regex
      split[1] == the regex attribute
      add regex name (regex[x][1]) to the beginning of the string
      add new string to beginning of list
  '''
  affected_lines = []
  data_container = []
  for i in range(header_len):
    line = data_obj.contents[i].get_text()
    for j in range(len(regex)):
      if re.search(regex[j][0], line):
        affected_lines.append(i)
        # if line[i] is matched by regex[j]
        one, two = re.split(regex[j][0], line, maxsplit=1)
        # reasign line to the 'remainder' of the line
        line = one
        data = "<p>" + regex[j][1] + " " + two.strip() + "</p>"
        data_container = [data] + data_container
  # return list(set(affected_lines)), data_container
  # re-build data_object



##
## CLASSES
##

class Html(object):
  def __init__(self, path_to_file):
    self.path = path_to_file
    self.file_name = re.split("/", path_to_file)[-1]
    self.data = None
    self._raw_data = None

  def convert(self, encoding="utf-8"):
    with open(self.path, "r", encoding=encoding) as f:
      bs = BeautifulSoup(f.read(), 'html.parser')
      self.data = bs.body

  # def _recurse_contents(self, item, integer):
  #   if integer > 0:
  #     output = self._recurse_contents(item.contents[0], integer - 1)
  #   elif integer < 0:
  #     output = item
  #   else:
  #     output = item.contents[0]
  #   return output

  def _remove_chars(self, string, chars=CHARS):
    for char in chars:
      string = re.subn(char, "", string)[0]
    return string

  def _remove_dups(self, seq):
      seen = set()
      seen_add = seen.add
      return [x for x in seq if not (x in seen or seen_add(x))]

  def untidy(self):
    self.data = self._raw_data
    self._raw_data = None

  def tidy(self,
           elems=['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'],
           list_elems=["ol", "ul"],
           doc_open="<body>",
           doc_close="</body>"):

    self._raw_data = self.data

    # remove unwanted characters
    html_str = str(self.data)
    logging.debug("removing characters:" + str(CHARS))
    for c in CHARS:
      html_str = re.subn(c, "", html_str)[0]
    self.data = BeautifulSoup(html_str, "html.parser")

    # iterate through all doc descendants
    html_list = [doc_open]
    for t in self.data.descendants:
      if t.name in elems:
        # print(t.name)
        logging.debug(t.name)
        if t.get_text().strip() != "":
          tag = t.name
          h_text = "<"+tag+">" + t.get_text("").strip() + "</"+tag+">"
          # print(h_text)
          logging.debug(h_text)
          html_list.append(h_text)
      elif t.name in list_elems:
        logging.debug(t.name)
        list_type = t.name
        l_open = "<" + list_type + ">"
        l_close = "</" + list_type + ">"
        l_ = [l_open]
        for u in t.contents:
          if u.get_text().strip() != "":
            tag = u.name
            h_text = "<"+tag+">" + u.get_text("").strip() + "</"+tag+">"
            logging.debug(h_text)
            l_.append(h_text)
        l_.append(l_close)
        html_list.append("".join(l_))
    html_list.append(doc_close)
    html_list = self._remove_dups(html_list)
    html_text = "".join(html_list)
    bs = BeautifulSoup(html_text, 'html.parser')
    self.data = bs.body

  # def tidy(self, depth_function, test=False):
  #   '''Processes nested html to produce a flat structure.
  #   Requires "depth_function" which is an array of integers that defines the number of
  #   html elements IMMEDIATELY below the body element, and then for each how deep to
  #   extract the content, e.g., [0, 1] indicates that there are two sections to the
  #   document, and the first is more shallow than the latter'''
  #   self._raw_data = self.data
  #   item = self.data
  #   self.clean_lst = []

  #   # if depth func matches expected length of contents, we have (likely)
  #   # guessed correctly
  #   if len(depth_function) == len(self.data.contents):
  #     logging.info("html parse - using depth function")
  #     for i in range(len(depth_function)):
  #       item = self.data.contents[i]
  #       lst = self._recurse_contents(item, depth_function[i]-1)
  #       for j in range(len(lst)):
  #         # logging.debug((i,j))
  #         # logging.debug(lst.contents[j])
  #         if isinstance(lst.contents[j], bs4.element.Tag):
  #           if lst.contents[j].get_text().strip() != "":
  #             # remove empty elements
  #             # clean_lst.append(str(lst.contents[j]))
  #             text = lst.contents[j].get_text(" ").strip()
  #             text = re.subn("\s+", " ", text)[0]
  #             # h_text = "<p>" + text + "</p>"
  #             self.clean_lst.append(text)
  #         elif isinstance(lst.contents[j], bs4.element.NavigableString):
  #           if lst.contents[j].strip() != "":
  #             # remove empty elements
  #             # clean_lst.append(str(lst.contents[j]))
  #             text = lst.contents[j].get_text(" ").strip()
  #             text = re.subn("\s+", " ", text)[0]
  #             self.clean_lst.append(text)

  #   # else if the contents are larger than depth func, we have guessed too deeply
  #   elif len(depth_function) < len(self.data.contents):
  #     logging.warn("html parse - depth function ignored")
  #     for i in range(len(self.data.contents)):
  #       item = self.data.contents[i]
  #       # logging.debug(item)
  #       if isinstance(item, bs4.element.Tag):
  #         if item.get_text().strip() != "":
  #           # clean_lst.append(str(item))
  #           text = item.get_text(" ").strip()
  #           text = re.subn("\s+", " ", text)[0]
  #           # h_text = "<p>" + text + "</p>"
  #           self.clean_lst.append(text)
  #       elif isinstance(item, bs4.element.NavigableString):
  #         if item.strip() != "":
  #           # remove empty elements
  #           # clean_lst.append(str(item))
  #           text = item.strip()
  #           text = re.subn("\s+", " ", text)
  #           self.clean_lst.append(text)

  #   # if contents are shorter than depth func, we have guessed too shallow
  #   # try to use depth func on those components that are present
  #   else:
  #     logging.warn("html parse - contents block shorter then depth function")
  #     for i in range(len(self.data.contents)):
  #       item = self.data.contents[i]
  #       lst = self._recurse_contents(item, depth_function[i]-1)
  #       for j in range(len(lst)):
  #         # print((i,j))
  #         # logging.debug(lst.contents[j])
  #         if isinstance(lst.contents[j], bs4.element.Tag):
  #           if lst.contents[j].get_text().strip() != "":
  #             # remove empty elements
  #             # clean_lst.append(str(lst.contents[j]))
  #             text = lst.contents[j].get_text(" ").strip()
  #             text = re.subn("\s+", " ", text)
  #             # h_text = "<p>" + text + "</p>"
  #             self.clean_lst.append(text)
  #         elif isinstance(lst.contents[j], bs4.element.NavigableString):
  #           if lst.contents[j].strip() != "":
  #             # remove empty elements
  #             # clean_lst.append(str(lst.contents[j]))
  #             text = lst.contents[j].get_text(" ").strip()
  #             text = re.subn("\s+", " ", text)
  #             self.clean_lst.append(text)

  #   # self.clean_lst.append("</body>")
  #   # html_doc = lxml.html.fromstring("".join(clean_lst))

  #   # call _fix_header() here
  #   # call _htmlify_list() here
  #   html_doc = "".join(self.clean_lst)
  #   html_doc = self._remove_chars(html_doc)
  #   bs = BeautifulSoup(html_doc, 'html.parser')
  #   self.data = bs.body


##
## SCRATCH
##

'''
import glob
from processing import Html

docs = glob.glob("./static/documents/*")

doc_lst = []

for doc in docs:
  html = Html(doc)
  html.convert(encoding="latin-1")
  html.tidy()
  doc_lst.append((html.file_name, html.data))

'''