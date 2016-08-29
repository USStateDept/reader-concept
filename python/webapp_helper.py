#! /usr/bin/env python3

##
## IMPORTS
##

import re
import logging

##
## CONSTANTS and VARIABLES
##

logging.basicConfig(level=logging.DEBUG)

##
## FUNCTIONS
##

def preview(string, length=30):
  token_len = len(string.split(" "))
  logging.info(token_len)

  if token_len > length:
    split_string = string.split(" ")
    preview = " ".join(split_string[:length]) + " ..."
    return preview
  else:
    return string


def count_terms(lst_of_csv, num_terms=5, offset=0):
  term_list = []
  for s_ in lst_of_csv:
    l_ = s_[0].split(",")
    term_list = term_list + l_

  term_set = set(term_list)
  t_ = []
  for term in term_set:
    count = term_list.count(term)
    t_.append((count, term))
  t_.sort(reverse=True)
  result = [ item[1] for item in t_[offset:offset+num_terms] ]
  return result


##
## CLASSES
##



##
## IFMAIN
##

if __name__ == '__main__':
  main()

