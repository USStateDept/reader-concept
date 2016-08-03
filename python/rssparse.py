#! /usr/bin/env python3

##
## IMPORTS
##

import requests
import re
import html
import configparser

##
## CONSTANTS and VARIABLES
##



##
## FUNCTIONS
##

def fetch(url):
  pass


def trim_description(description):
  doc = html.unescape(description)
  patt = re.compile('<div.*', re.MULTILINE | re.DOTALL)
  doc = patt.sub("", doc)
  return doc


def main():
  pass

##
## CLASSES
##



##
## IFMAIN
##

if __name__ == '__main__':
  main()

