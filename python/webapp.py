#! /usr/bin/env python3

##
## IMPORTS
##

import os
import dbIO
import sys
import re
from datetime import datetime
import json
import sqlite3
import configparser
import logging
import urllib
from time import sleep
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash
from webapp_helper import preview, count_terms

##
## CONSTANTS and VARIABLES
##

logging.basicConfig(level=logging.DEBUG)

config = configparser.ConfigParser()
config.read("../data/default.ini")

if config["webapp"]["debug"] == 'true':
  DEBUG = True
else:
  DEBUG = False

SECRET_KEY = config["webapp"]["secret_key"]
USERNAME = config["webapp"]["default_usr"]
PASSWORD = config["webapp"]["default_pwd"]

db_handler = dbIO.SQLio()

## lookup dictionary loading
## for sidebar / related content
countries = "../data/countries.json"
with open(countries, "r") as d:
  countries_dict = json.load(d)

partners_names = "../data/partners_names.json"
with open(partners_names, "r") as d:
  part_names_dict = json.load(d)

partners_urls = "../data/partners_urls.json"
with open(partners_urls, "r") as d:
  part_urls_dict = json.load(d)

org_names = "../data/org_names.json"
with open(org_names, "r") as d:
  org_names_dict = json.load(d)

org_urls = "../data/org_urls.json"
with open(org_urls, "r") as d:
  org_urls_dict = json.load(d)

##
## INIT FLASK
##

app = Flask(__name__)
app.config.from_object(__name__)

if DEBUG == True:
  print(app.config['USERNAME'])
  print(app.config['PASSWORD'])

##
## FUNCTIONS
##

def connect_db():
  '''Connects to the specific database.'''
  try:
    return sqlite3.connect(db_handler.db) # to do - use the dbIO.SQLio() object directly
  except sqlite3.OperationalError:
    return sqlite3.connect("../../sql/polis.db")

def get_db():
    '''Opens a new database connection if there is none yet for the
    current application context.'''
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db

##
## DECORATORS
##

@app.before_request
def before_request():
    g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()

##
## ROUTES
##

## VIEWER ROUTES

@app.route("/", methods=['GET', 'POST'])
def home():
  '''Pulls docs and trends for the main page'''

  # grab most recent issue docs
  cur = g.db.execute("""select uid,
                               doc_date,
                               title,
                               full_text,
                               from_auth,
                               from_bur
                        from document
                        order by doc_date desc
                        limit 10; """)

  docs = cur.fetchall()

  issue_docs = []
  if docs != []:
    for result in docs:
      d_ = {}
      d_["id"] = result[0]
      d_["date"] = result[1]
      d_["title"] = result[2]
      d_["preview"] = preview(result[3], length=50)
      d_["author"] = result[4]
      d_["bur"] = result[5]
      issue_docs.append(d_)

  else:
    pass

  # top terms
  # order by == looking at most recent/trending
  cur = g.db.execute("""select top_terms
                        from document
                        order by u_date desc
                        limit 30; """)

  terms = cur.fetchall()
  top_terms = count_terms(terms)

  return render_template("home.html", issues=top_terms, issue_docs=issue_docs)


@app.route('/search', methods=['GET'])
def search():
  q = request.args.get("q")
  q = urllib.parse.quote_plus(q)
  return redirect(url_for('results', q=q))


@app.route('/results/<q>', methods=['GET'])
def results(q):
  '''Display search results and documents connected to a given query'''
  # top terms
  # order by == looking at most recent/trending
  cur = g.db.execute("""select top_terms
                        from document
                        order by u_date desc
                        limit 30; """)

  terms = cur.fetchall()
  top_terms = count_terms(terms)

  # search results
  p = urllib.parse.unquote_plus(q)
  query = "%" + p + "%" # for LIKE operation
  cur = g.db.execute("""select uid,
                               doc_date,
                               title,
                               full_text,
                               from_auth,
                               from_bur
                        from document
                        where full_text like ?
                        order by u_date desc
                        limit 20; """, (query,))

  docs = cur.fetchall()

  results = []
  if docs != []:
    # if the result set is not empty
    for doc in docs:
      d_ = {}
      d_["id"] = doc[0]
      d_["date"] = doc[1]
      d_["title"] = doc[2]
      d_["preview"] = preview(doc[3], length=50)
      d_["author"] = doc[4]
      d_["bur"] = doc[5]
      results.append(d_)

  return render_template("results.html", issues=top_terms, results=results)


@app.route('/document/<doc_id>', methods=['GET', 'POST'])
def document(doc_id):
  '''Viewer page for an individual document'''

  # document data
  cur = g.db.execute("""select classification,
                               title,
                               doc_date,
                               from_auth,
                               from_bur,
                               category,
                               addressee,
                               file_name,
                               html,
                               full_text,
                               top_terms
                        from document
                        where uid = ?; """, (doc_id,))

  doc = cur.fetchall()[0]

  document = {
    "classification": doc[0],
    "title": doc[1],
    "doc_date": doc[2],
    "from_auth": doc[3],
    "from_bur": doc[4],
    "category": doc[5],
    "addressee": doc[6],
    "file_name": doc[7],
    "html": doc[8],
    "full_text": doc[9],
    "top_terms": doc[10].split(",")
  }

  # get related documents
  num = 3
  score_co = 0.95 # prevent self-similarity
  cur = g.db.execute("""select d.uid, d.title, d.full_text
                        from document d
                        join similar s on d.uid = s.uid_2
                        where s.uid_1 = ?
                        and s.score < ?
                        order by s.score desc
                        limit ? ; """, (doc_id, score_co, num))

  sim_ = cur.fetchall()

  related = []
  for doc in sim_:
    d_ = {}
    d_["id"] = doc[0]
    d_["title"] = doc[1]
    d_["preview"] = preview(doc[2], length=15)

    related.append(d_)

  # check document text for known entities:
  # bureaus and offices
  bureaus = []
  for b in org_names_dict:
    if re.search("\W" + b + "\W", document["full_text"]):
      logging.debug(org_names_dict[b] + ": " + org_urls_dict[b])
      bureaus.append({ "name": org_names_dict[b], "url": org_urls_dict[b] })

  # partner orgs
  partners = []
  for p in part_names_dict:
    if re.search(p, document["full_text"]):
      partners.append({ "name": part_names_dict[p], "url": part_urls_dict[p] })

  # countries
  countries = []
  for c in countries_dict:
    if re.search(c, document["full_text"]):
      countries.append({ "name": c, "url": countries_dict[c] })

  return render_template("document.html",
                         document=document,
                         related=related,
                         bureaus=bureaus,
                         partners=partners,
                         countries=countries)


## ADMIN ROUTES

# # LOGIN
# @app.route('/login', methods=['GET', 'POST'])
# def login():
#   error = None
#   if request.method == 'POST':
#     if request.form['username'] != app.config['USERNAME'] or request.form['password'] != app.config['PASSWORD']:
#         error_message = 'Invalid username or password'
#         flash(error_message)
#     else:
#         session['logged_in'] = True
#         flash('You were logged in')
#         return redirect(url_for('home'))
#   return render_template('admin.html')

# @app.route('/logout')
# def logout():
#   session.pop('logged_in', None)
#   flash('You were logged out')
#   return redirect(url_for('home'))

##
## IFMAIN
##

if __name__ == '__main__':
  if DEBUG == False:
    app.run(host='0.0.0.0', port=80)
  else:
    app.run(host=os.getenv('IP', '0.0.0.0'),port=int(os.getenv('PORT', 8080)))

