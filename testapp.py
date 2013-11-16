#!/usr/bin/env python
#-*- coding:utf-8 -*-

from flask import Flask, Response, render_template, request, session, g, flash, abort, redirect, url_for
from contextlib import closing
import dateutil
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
    results_message = db.getMeta('kiosk_results_message')
    
  return render_template('checkin-results.html', results_message=results_message,
        results=results, search = search, kiosk=kiosk)
  
  
@app.route('/select-activity', methods=['GET'])
def selectActivity():
  search = request.args.get('search', '')
  #~ if search == '': 
    #~ #For some reason, when following a link to here browsers fetch
    #~ #?id=nnn first, and then ?id=nnn&query=s and causes a broken pipe.
    #~ abort(200)
  ID = request.args.get('id', '')
  
  with app.app_context():
    db = get_db()
    activities = db.getActivities()
    kiosk = fetchKioskConstants()
    title = db.getMeta('kiosk_activity_title')
    allow_multiple = db.getMeta('kiosk_activity_allow_multiple')
  
  return render_template('checkin-activity.html', search=search, id=ID,
              activities=activities, kiosk=kiosk, title=title, allow_multiple=allow_multiple)
  
@app.route('/select-services', methods=['GET'])
def selectServices():
  search = request.args.get('search', '')
  ID = request.args.get('id', '')
  #parse and validate selected activities:
  activities = request.args.getlist("activity")
  if len(activities) == 0:
    flash("You must pick at least one activity", "error")
    return selectActivity()
    
  with app.app_context():
    db = get_db()
    services = db.getServices()
    kiosk = fetchKioskConstants()
    title = db.getMeta('kiosk_service_title')
    allow_multiple = db.getMeta('kiosk_service_allow_multiple')
    
  return render_template('checkin-services.html', search=search, activities=activities, id=ID,
                services=services, kiosk=kiosk, title=title, allow_multiple=allow_multiple)
  
@app.route('/checkin-note', methods=['GET'])
def checkinNote():
  search = request.args.get('search', '')
  ID = request.args.get('id', '')
  #parse and validate selected activities:
  activities = request.args.getlist("activity")
  services = request.args.getlist("service")
  if len(services) == 0:
    flash("You must pick at least one service", "error")
    return selectServices()
    
  with app.app_context():
    db = get_db()
    kiosk = fetchKioskConstants()
    title = db.getMeta('kiosk_note_title')
    
  return render_template('checkin-note.html', kiosk=kiosk, title=title, id=ID, search=search,
                  activities=activities, services=services)
  
@app.route('/checkin-confirm', methods=['POST'])
def checkinConfirm():
  search = request.form['search']
  ID = int(request.form['id'])
  #parse and validate selected activities:
  activities = request.form.getlist("activity")
  services = request.form.getlist("service")
  note = request.form.get('message', None)
  
  #TODO Dereference activities and services to their names:
  
  
  with app.app_context():
    db = get_db()
    kiosk = fetchKioskConstants()
    person = db.getUserByID(ID)
    note_title = db.getMeta('kiosk_note_title')
    
  return render_template('checkin-confirm.html', person=person, activities=activities)
  
@app.errorhandler(500)
def applicationError(error):
  return render_template('error.html'), 500

def get_db():
  app.logger.debug("Enter get_db()")
  if not hasattr(g, 'db'):
    try:
      g.db = connect_db()
    except database.DatabaseError as e:
      app.logger.error(e)
      if e.code == database.INVALID_PASSWORD:
        app.logger.error("Invalid password")
        flash(u'Configuration Error: Invalid database password provided', 'error')
      elif e.code == database.FAIL:
        app.logger.error("Unable to connect to database.")
        flash(u'<strong>Error: </strong>Unable to connect to database.  Please check your configuration.', 'error')
        flash(u'<br>Details:<pre>{0}</pre>'.format(str(e)), 'error')
      abort(500)
  return g.db
  
   
def connect_db():
  hostname = app.config['DB_HOSTNAME'] + ':' + str(app.config['DB_PORT'])
  dbname = app.config['DB_NAME']
  user = app.config['DB_USER']
  passwd = app.config['DB_PASSWORD']
  app.logger.debug("Attempting to open database {0}@{1}...".format(dbname, hostname))
  return database.Database(hostname, dbname, user, passwd) 
  
@app.teardown_request
@app.teardown_appcontext
def teardown_request(exception):
  db = getattr(g, 'db', None)
  if db is not None:
    app.logger.warn("Close db")
    db.close()
    
@app.template_filter('strftime')
def _jinja2_filter_datetime(date, fmt=None):
  native = date.replace(tzinfo=None)
  format='%H:%M'  #TODO: i18n
  return native.strftime(format) 
  

if __name__ == "__main__":
  app.run()
