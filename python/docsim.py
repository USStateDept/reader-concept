#! /usr/bin/env python3

##
## IMPORTS
##

from sklearn.feature_extraction.text import TfidfVectorizer
# from sklearn.metrics.pairwise import cosine_similarity
import dbIO
import configparser
# import json
import logging
# import re
# import numpy as np

##
## CONSTANTS and VARIABLES
##

logging.basicConfig(level=logging.DEBUG)

config = configparser.ConfigParser()
config.read("../data/default.ini")

custom_stops = []

if len(custom_stops) > 0:
  STOPS = custom_stops
else:
  STOPS = 'english'

##
## FUNCTIONS
##

'''
Initial REPL formulation...

def fetch_content(db_obj=dbIO.SQLio()):
  db = db_obj
  db.connect()
  query = db.cur.execute("""select uid, full_text from document;""")
  results = query.fetchall()
  db.conn.close()
  keys, docs = zip(*results) # unpack list of tuples into two lists w/ matching indices
  return keys, docs

def get_similarity(uids, documents, stops=STOPS):
  # compute tfidf for all documents
  vectorizer = TfidfVectorizer(stop_words=stops, ngram_range=(1,3))
  tfidf = vectorizer.fit_transform(documents)

  # data qc
  try:
    assert len(uids) == len(documents) == tfidf.shape[0]
  except AssertionError:
    logging.warn("lengths of uids, documents, and the tfidf are not the same:")
    logging.warn("%s, %s, %s" % (str(len(uids)), str(len(documents)), str(len(tfidf.shape[0])) ) )
    return

  # compute similarity
  cosine_similarity = tfidf * tfidf.T

  # for each pair (a, b) and (b, a), index similarity
  r_ = range(0, len(uids))
  doc_sims = []
  for i in r_:
    for j in r_:
      uid_1 = uids[i]
      uid_2 = uids[j]
      score = cosine_similarity[i, j]
      doc_sims.append((uid_1, uid_2, score))
  return doc_sims

def get_top_terms(documents, stops=STOPS, n_terms=3):

  # vecotrize using only 1-grams
  vectorizer = TfidfVectorizer(stop_words=stops, ngram_range=(1,3))
  tfidf = vectorizer.fit_transform(documents)

  # enumerate feature names, ie. the actual words
  feature_names = vectorizer.get_feature_names()

  # convert to dense array
  dense = tfidf.todense()

  # container for top terms per doc
  features = []

  for doc in dense:
    doc = doc.tolist()[0]

    # creates a list of tuples, (term_id, score)
    phrase_scores = [pair for pair in zip(range(0, len(doc)), doc) if pair[1] > 0]
    # feature_ids = sorted(phrase_scores, key=lambda t: t[1] * -1)
    doc_features = []

    for f_ in phrase_scores:
      fname = feature_names[f_[0]]
      fscore = f_[1]
      doc_features.append((fscore, fname))

    top_terms = sorted(doc_features, reverse=True)[:n_terms]
    top_terms = ",".join([ x[1] for x in top_terms ])
    features.append(top_terms)
  return features

def write_to_db(lst, db_obj=dbIO.SQLio()):
  keys = ",".join(("uid_1", "uid_2", "score"))
  db = db_obj
  db.connect()
  for item in lst:
    qs = ",".join(list('?' * len(item)))
    db.cur.execute("insert or replace into similar (" + keys + ") values (" + qs + ")", item )
  db.conn.commit()
  db.conn.close()
'''

def main():
  similarity = DocSim()
  similarity.fetch_content()
  similarity.get_similarity()
  similarity.get_top_terms()
  similarity.write_to_db()

##
## CLASSES
##

class DocSim(object):
  def __init__(self, db=dbIO.SQLio()):
    self.db = db

  def fetch_content(self):
    db_ = self.db
    db_.connect()
    query = db_.cur.execute("""select uid, full_text from document;""")
    results = query.fetchall()
    db_.conn.close()
    keys, docs = zip(*results) # unpack list of tuples into two lists w/ matching indices
    self.keys, self.docs = keys, docs

  def get_similarity(self, stops=STOPS):
    # compute tfidf for all documents
    tfidf = TfidfVectorizer(stop_words=stops).fit_transform(self.docs)

    # data qc
    try:
      assert len(self.keys) == len(self.docs) == tfidf.shape[0]
    except AssertionError:
      logging.warn("lengths of uids, documents, and the tfidf are not the same:")
      logging.warn("%s, %s, %s" % (str(len(self.keys)), str(len(self.docs)), str(len(tfidf.shape[0])) ) )
      return

    # compute similarity
    cosine_similarity = tfidf * tfidf.T

    # for each pair (a, b) and (b, a), index similarity
    r_ = range(0, len(self.keys))
    self.doc_sims = []
    for i in r_:
      for j in r_:
        uid_1 = self.keys[i]
        uid_2 = self.keys[j]
        score = cosine_similarity[i, j]
        self.doc_sims.append((uid_1, uid_2, score))


  def get_top_terms(self, stops=STOPS, n_terms=3):

    # vecotrize using only 1-grams
    vectorizer = TfidfVectorizer(stop_words=stops, ngram_range=(1,3))
    tfidf = vectorizer.fit_transform(self.docs)

    # enumerate feature names, ie. the actual words
    feature_names = vectorizer.get_feature_names()

    # convert to dense array
    dense = tfidf.todense()

    # container for top terms per doc
    self.features = []

    for doc in dense:
      doc = doc.tolist()[0]

      # creates a list of tuples, (term_id, score)
      phrase_scores = [pair for pair in zip(range(0, len(doc)), doc) if pair[1] > 0]
      # feature_ids = sorted(phrase_scores, key=lambda t: t[1] * -1)
      doc_features = []

      for f_ in phrase_scores:
        fname = feature_names[f_[0]]
        fscore = f_[1]
        doc_features.append((fscore, fname))

      top_terms = sorted(doc_features, reverse=True)[:n_terms]
      top_terms = ",".join([ x[1] for x in top_terms ])
      self.features.append(top_terms)


  def write_to_db(self):
    # first, similarities
    keys = ",".join(("uid_1", "uid_2", "score"))
    db_ = self.db
    db_.connect()
    for item in self.doc_sims:
      qs = ",".join(list('?' * len(item)))
      db_.cur.execute("insert or replace into similar (" + keys + ") values (" + qs + ")", item )
    db_.conn.commit()

    # then, top_terms
    lst = list(zip(self.features, self.keys))
    for item in lst:
      db_.cur.execute("update document set top_terms = ? where uid = ?;", item )
    db_.conn.commit()

    db_.conn.close()

##
## IFMAIN
##

if __name__ == '__main__':
  main()

