#! /usr/bin/env python3

##
## IMPORTS
##

import os
import dbIO
import sys
from datetime import datetime
import json
import sqlite3
import configparser
import logging
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
  cur = g.db.execute("""select uid, u_date, title, full_text
                        from document
                        where category = 'bureaus'
                        order by u_date desc
                        limit 5; """)

  docs = cur.fetchall()

  issue_docs = []
  if docs != []:
    for result in docs:
      d_ = {}
      d_["id"] = result[0]
      d_["date"] = result[1]
      d_["title"] = result[2]
      d_["preview"] = preview(result[3])
      issue_docs.append(d_)

  else:
    pass

  # grab most recent country docs
  cur = g.db.execute("""select uid, u_date, title, full_text
                        from document
                        where category = 'countries'
                        order by u_date desc
                        limit 5; """)

  docs = cur.fetchall()
  country_docs = []
  if docs != []:
    for result in docs:
      d_ = {}
      d_["id"] = result[0]
      d_["date"] = result[1]
      d_["title"] = result[2]
      d_["preview"] = preview(result[3])
      country_docs.append(d_)

  else:
    pass

  # rss feed from reuters
  # to-do

  # top terms
  # order by == looking at most recent/trending
  cur = g.db.execute("""select top_terms
                        from document
                        order by u_date desc
                        limit 30; """)

  terms = cur.fetchall()
  top_terms = count_terms(terms)

  return render_template("home.html", issues=top_terms, issue_docs=issue_docs, country_reports=country_docs)


@app.route('/search/<q>', methods=['GET', 'POST'])
def search(q=""):
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
  query = "%" + q + "%" # for LIKE operation
  cur = g.db.execute("""select uid, title, full_text
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
      d_["title"] = doc[1]
      d_["preview"] = preview(doc[2])
      results.append(d_)

  return render_template("search.html", issues=top_terms, results=results)


@app.route('/document/<doc_id>', methods=['GET', 'POST'])
def document(doc_id):
  '''Viewer page for an individual document'''

  # document data
  cur = g.db.execute("""select u_date, title, html, top_terms
                        from document
                        where uid = ?; """, (doc_id,))

  doc = cur.fetchall()[0]

  document = {}
  document["date"] = doc[0]
  document["title"] = doc[1]
  document["html"] = doc[2]
  document["key_terms"] = doc[3].split(",")

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

  # fetch google news
  # to do

  # fetch google trends
  # to do

  return render_template("document.html", document=document, related=related )


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

