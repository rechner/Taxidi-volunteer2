#!/usr/bin/env python
#-*- coding:utf-8 -*-

from flask import Flask, Response, render_template, request, session, g, flash, abort, redirect, url_for
from contextlib import closing

from dblib import postgres as database
import config

app = Flask(__name__)
app.config.from_object("config.DevelopmentConfig")
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RB'

@app.route('/')
def index():
  return Response("Hello world!")
  
@app.route('/hello/')
def hello():
  with app.app_context():
    db = get_db()
    test = db.getMeta('site_title')
  return render_template('hello.html', test = test)
  
@app.route('/login', methods=['GET', 'POST'])
def login():
  #TODO
  error = None
  if request.method == 'POST':
    pass
  else:
    pass
    
  return render_template('login.html')
    
def fetchKioskConstants():
  with app.app_context():
    db = get_db()
    timeout = db.getMeta('kiosk_timeout')
    warning = db.getMeta('kiosk_timeout_warning')
    title = db.getMeta('kiosk_timeout_title')
    msg = db.getMeta('kiosk_timeout_message')
    return { 'timeout' : timeout, 'timeout_warning' : warning,
              'timeout_title' : title, 'timeout_message' : msg }
    
@app.route('/timeclock')
def timeclock(error=None):
  if request.method == 'POST':
    return redirect(url_for('timeclock-search'))

  with app.app_context():
    db = get_db()
    site_title = db.getMeta('site_title')
    search_message = db.getMeta('kiosk_search_message')    
    
  return render_template('checkin-search.html', site_title=site_title, search_message=search_message)
  
@app.route('/timeclock-search', methods=['GET', 'POST'])
def timeclockSearch():
  search = request.args.get('search', '')
  if search == '':
    return redirect(url_for('timeclock'))
  
  with app.app_context():
    db = get_db()
    results = db.search(search)
    if len(results) == 0:
      flash(u"No results for \"{0}\"".format(search), "error")
      return redirect(url_for('timeclock'))
    
    kiosk = fetchKioskConstants()
    
  return render_template('checkin-results.html', 
        results=results, search = search, kiosk=kiosk)
  
  
@app.route('/select-activity', methods=['GET'])
def selectActivity(error=None):
  search = request.args.get('search', '')
  if search == '': 
    #For some reason, when following a link to here browsers fetch
    #?id=nnn first, and then ?id=nnn&query=s and causes a broken pipe.
    abort(200)
  ID = request.args.get('id', '')
  
  with app.app_context():
    db = get_db()
    activities = db.getActivities()
  
  return render_template('checkin-activity.html', search=search, id=ID, error=error,
              activities=activities)
  
@app.route('/select-services', methods=['GET'])
def selectServices():
  search = request.args.get('search', '')
  personID = request.args.get('id', '')
  #parse and validate selected activities:
  activities = request.args.getlist("activity")
  if len(activities) == 0:
    return selectActivity(error="You must pick at least one activity")
  return render_template('checkin-services.html', search=search, activities=activities)
  
@app.route('/checkin-note', methods=['GET'])
def checkinNote():
  return render_template('checkin-note.html')
  
@app.route('/checkin-confirm', methods=['GET', 'POST'])
def checkinConfirm():
  #~ return str(request.args.getlist("service"))
  #~ return render_template('checkin-confirm.html')
  return render_template('checkin-confirm.html')
  
@app.errorhandler(500)
def applicationError(error):
  flash(u'<strong>Configuration Error</strong>: Invalid database password provided', 'error')
  return render_template('error.html'), 500

def get_db():
  if not hasattr(g, 'db'):
    try:
      g.db = connect_db()
    except database.DatabaseError as e:
      app.logger.error(e)
      if e.code == database.INVALID_PASSWORD:
        flash(u'Configuration Error: Invalid database password provided', 'error')
      elif e.code == database.FAIL:
        flash(u'Unable to connect to database.  Please check your configuration', 'error')
      abort(500)
  return g.db
  
   
def connect_db():
  hostname = app.config['DB_HOSTNAME'] + ':' + str(app.config['DB_PORT'])
  dbname = app.config['DB_NAME']
  user = app.config['DB_USER']
  passwd = app.config['DB_PASSWORD']
  return database.Database(hostname, dbname, user, passwd) 
  
@app.teardown_request
@app.teardown_appcontext
def teardown_request(exception):
  db = getattr(g, 'db', None)
  if db is not None:
    app.logger.warn("Close db")
    db.close()

if __name__ == "__main__":
  app.run()
