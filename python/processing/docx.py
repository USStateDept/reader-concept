

##
## IMPORTS
##

import re
from pydocx import PyDocX
from bs4 import BeautifulSoup
import logging
import configparser


##
## CONSTANTS and VARIABLES
##

config = configparser.ConfigParser()
config.read("/home/ubuntu/workspace/data/default.ini")

if config["DEFAULT"]["log_level"] == "debug":
  logging.basicConfig(level=logging.DEBUG)
else:
  logging.basicConfig(level=logging.WARN)

##
## FUNCTIONS
##



##
## CLASSES
##

class Docx(object):
  def __init__(self, path_to_docx):
    self.path = path_to_docx
    self.file_name = re.split("/", path_to_docx)[-1]

  def convert(self):
    self._raw = PyDocX.to_html(self.path)
    bs = BeautifulSoup(self._raw, 'html.parser')
    self.data = bs.body



