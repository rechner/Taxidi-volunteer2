#!/usr/bin/env python
#-*- coding:utf-8 -*-

from flask import Flask, Response, render_template, request, session, g
from flask import flash, abort, redirect, url_for, get_flashed_messages
from flask import Markup
from flask import json
from contextlib import closing
import re
import datetime, dateutil
from time import mktime

from dblib import postgres as database
import config

app = Flask(__name__)
app.config.from_object("config.DevelopmentConfig")
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RB'

@app.route('/')
def index():
  if session.get('logged_in'):
    return redirect(url_for('admin'))
  return redirect(url_for('login'))
   
@app.route('/profile')      
def profile(): #Perhaps this should just be a shortlink to /user/<id>
  if session.get('logged_in'):
    return render_template('admin-edit-profile.html', user=session.get('user'), form=None)
    
@app.route('/profile/password')
def change_password():
  if session.get('logged_in'):
    return render_template('admin-change-password.html', user=session.get('user'))

@app.route('/admin')
def admin():
  if session.get('logged_in'):
    return render_template('admin.html', user=session.get('user'))  
  else:
    return redirect(url_for('login'))
    
@app.route('/admin-register', methods=['GET', 'POST'])
def register():
  if session.get('logged_in'):
    if request.method == 'POST':
      #Grab the form values and validate them:
      name = request.form['name']
      surname = request.form['surname']
      email = request.form['email']
      admin = request.form.get('admin', False)
      password = request.form['password']      
      confirm_pass = request.form['confirm_pass']
      dob = request.form['dob']
      license_number = request.form['license_number']
      home_phone = request.form['home_phone']
      mobile_phone = request.form['mobile_phone']
      sms_capable = request.form.get('sms_capable', False)
      newsletter = request.form.get('newsletter', False)
      error = False
      
      #checkboxes are weird
      if admin == "on": admin = True
      if sms_capable == "on": sms_capable = True
      if newsletter == "on": newsletter
      
      if name == "":
        flash("First name is a required field", 'error')
        error = True
      if surname == "":
        flash("Surname is a required field", 'error')
        error = True
      if dob == "":
        flash("Date of birth is a required field", 'error')
        error = True
        
      #Validate date
      try:
        datetime.datetime.strptime(dob, "%Y-%m-%d").date()
      except ValueError as e:
        flash("Date of birth must be in YYYY-MM-DD format (e.g. 1990-10-21):" + \
              " {0}".format(e.message), 'error')
        error = True
        
      #validate email:
      if email != "":
        if not re.match("^[a-zA-Z0-9._%-+]+@[a-zA-Z0-9._%-]+.[a-zA-Z]{2,6}$", email):
          flash("Please enter a valid email address", 'error')
          error = True
        
      #validate password
      if admin:
        if email == "":
          flash("You must specify an email to allow administrative access", 'error')
          error = True
        if password == "":
          flash("You must specify a password to allow administrative access", 'error')
          error = True
        if password != confirm_pass:
          flash("The passwords provided do not match.", 'error')
          error = True
      if password == "": password = None
             
      #Populate form with pre-filled values if there was an error
      form = { 'name' : name, 'surname' : surname, 'email' : email,
               'admin' : admin, 'dob' : dob, 'home_phone' : home_phone,
               'license_number' : license_number, 'newsletter' : newsletter,
               'mobile_phone' : mobile_phone, 'sms_capable' : sms_capable }
      
      #FIXME: For some reason, this delays flashing by one request.
      #~ if not get_flashed_messages(category_filter=["error"]):
      if not error:
        app.logger.debug("Passed registration validation, adding user to database")
        #Check to see if someone with the same name and email exists already:
        with app.app_context():
          db = get_db()
          
          exists, id = db.userExists(name, surname, email)
          if exists:
            flash('The user <a class="alert-link" href="/details/{0}">{1} {2}</a> already exists.' \
              .format(id, Markup.escape(name), Markup.escape(surname)), 'error')
          else:
            app.logger.debug("No duplicates found.  Registering user in database.")
            db.addUser(name, surname, email, home_phone, mobile_phone, \
                     sms_capable, dob, license_number, newsletter=newsletter,
                     admin=admin, password=password)                     
            db.commit()
            flash("<b>{0} {1}</b> has been registered successfully." \
              .format(Markup.escape(name), Markup.escape(surname)), 'success')
        form = None #clear the form
    
    if request.method == 'GET':
      form = None #Return a blank form
    return render_template('admin-register.html', user=session.get('user'), form=form)
  else:
    return redirect(url_for('login'))
  
@app.route('/login', methods=['GET', 'POST'])
def login():
  with app.app_context():
    db = get_db()
    site_title = db.getMeta('site_title')
    
    error = None
    if request.method == 'POST':
      email = request.form["email"]
      password = request.form["password"]
      auth = db.authenticate(email, password)
      if auth[0]: #Success
        session['logged_in'] = True
        #~ auth[1]['dob'] = auth[1]['dob'].isoformat() if hasattr('isoformat')
        session['user'] = auth[1]
        return redirect(url_for('index'))
      else:
        flash("Username or password is incorrect", "error")
    
  return render_template('login.html', site_title=site_title)
  
@app.route('/logout')
def logout():
  session.pop('logged_in', None)
  session.pop('user', None)
  flash("You were logged out succesfully", "info")
  return redirect(url_for('index'))
    
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
  
@app.route('/timeclock-search')
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
                
@app.route('/search')
def searchAdmin():
  if session.get('logged_in'):
    return render_template('search-results.html', user=session.get('user'))
  
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
  activitiesID = request.form.getlist("activity")
  servicesID = request.form.getlist("service")
  note = request.form.get('message', None)
  if note == '': note = None
  
  with app.app_context():
    db = get_db()
    kiosk = fetchKioskConstants()
    person = db.getUserByID(ID)
    note_title = db.getMeta('kiosk_note_title')
    
    #Dereference activities and services by ID to their names:
    activities = db.getActivityNameList(activitiesID)  
    activitiesString = ", ".join(activities)
    activitiesString = activitiesString.decode('utf8')
    services = db.getServiceNameList(servicesID)
    servicesString = ", ".join(services)
    servicesString = servicesString.decode('utf8')
    
    #Record the check-in
    db.doCheckin(person['id'], activities, services, note)
    db.commit()
    
  return render_template('checkin-confirm.html', person=person, activities=activitiesString,
                    services=servicesString, note=note, note_title=note_title)
              
  
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
  
  
"""
Custom JSON encoder to handle datetime representations:
"""
class DatetimeJSONEncoder(json.JSONEncoder):
  
  def default(self, obj):
    #datetimes encoded in UNIX time
    if isinstance(obj, datetime.datetime):
      return int(mktime(obj.timetuple()))
    
    elif isinstance(obj, datetime.date):
      return int(mktime(obj.timetuple()))
  
    return json.JSONEncoder.default(self, obj)

#~ app.json_encoder = DatetimeJSONEncoder
app.logger.debug(app.json_encoder)

if __name__ == "__main__":
  app.run()
