#!/usr/bin/env python
#-*- coding:utf-8 -*-

import os
import config
os.chdir(os.path.dirname(config.__file__)) #Override wsgi directory change

from flask import Flask, Response, render_template, request, session, g
from flask import flash, abort, redirect, url_for, get_flashed_messages
from flask import Markup, make_response
from flask import json, jsonify
from flask_sslify import SSLify
from contextlib import closing
import re
import datetime, dateutil
import jinja2
import tempfile
from time import mktime
from functools import wraps

from dblib import postgres as database
import reports.init as report_plugins

app = Flask(__name__)
sslify = SSLify(app)
app.config.from_object("config.DevelopmentConfig")

#Login decorator:
def login_required(original_function):
  @wraps(original_function)
  def decorated_function(*args, **kwargs):
    if session.get('logged_in') is None or session.get('user') is None:
      return redirect(url_for('login', next=request.url))
    return original_function(*args, **kwargs)
  return decorated_function

@app.route('/')
@login_required
def index():
  return redirect(url_for('admin'))
   
@app.route('/profile')
@login_required
def profile(): #Perhaps this should just be a shortlink to /id/<id>
  return redirect(url_for('displayRecord', id=session.get('user')['id']))
  #~ return render_template('admin-edit-profile.html', user=session.get('user'), form=None)
    
@app.route('/profile/password')
@login_required
def change_password():
  return render_template('admin-change-password.html', user=session.get('user'))
  
@app.route('/admin/kiosk')
@login_required
def kiosk_settings():
  return render_template('kiosk-settings.html', user=session.get('user'), form={})
    
@app.route('/admin/activities/')
@login_required
def edit_activities():
  with app.app_context():
    db = get_db()
    activities = db.getActivities()
    return render_template('admin-edit-activites.html', activities=activities,
         user=session.get('user'),)
         
@app.route('/admin/activities/add', methods=['POST'])
@login_required
def add_activity():
  name = request.form.get('name', None)
  admin = request.form.get('admin', None)
  admin_name = request.form.get('admin_name', '')
  if name == '':
    flash('Name field cannot be blank.', 'error')
  if admin == '':
    admin = None
  if admin_name == '':
    flash('No administrator matching the name provided was found. '
          'No administrator will be assigned', 'info')
  with app.app_context():
    try:
      db = get_db()
      db.addActivity(name, admin)
      db.commit()
      flash('Activity added successfully', 'success')
    except database.DatabaseError:
      flash('There was a database error while trying to add this activity.', 'error')
    except database.IntegrityError:
      flash('The activity name "{0}" already exists.'.format(name), 'error')
    return redirect(url_for('edit_activities'))
  return redirect(url_for('edit_activities'))

@app.route('/admin/activities/delete', methods=['POST'])
@login_required
def delete_activity():
  id = request.form.get('id', None)
  if id is not None:
    with app.app_context():
      try:
        db = get_db()
        activity = db.getActivity(id)
        db.deleteActivity(id)
        db.commit()
        flash('The activity "{0}" has been deleted successfully.'
         .format(activity['name']), 'success')
      except database.DatabaseError as e:
        flash('There was a problem deleting the specified activity.', 'error')
      return redirect(url_for('edit_activities'))
  return abort(400)

@app.route('/admin/activities/edit', methods=['POST'])
@login_required
def edit_activities_ajax():
  id = request.form.get('pk', None)
  name = request.form.get('name', None)
  value = request.form.get('value', None)
  
  if name == 'name':
    if value == '':
      return make_response('"value" parameter cannot be blank'), 400
    with app.app_context():
      try:
        db = get_db()
        db.updateActivity(id, value)
        db.commit()
        return make_response('OK'), 200
      except database.DatabaseError:
        return make_response('Database error.  Unable to save.'), 400
      except database.IntegrityError:
        return make_response('Name is already in use.'), 400
  elif name == 'admin':
    if value == '':
      # Remove the administrator (?)
      return make_response('"value" parameter cannot be blank'), 400
    with app.app_context():
      try:
        db = get_db()
        db.updateActivity(id, name=None, admin=value)
        db.commit()
        app.logger.debug("Saved {0}, {1}, {2}".format(id, name, value))
        return make_response('OK'), 200
      except database.DatabaseError:
        return make_response('Database error.  Unable to save.'), 400
      except database.IntegrityError:
        return make_response('Name is already in use.'), 400
  return make_response('Expected "name", "admin" for name, but got "{0}" instead'.format(name)), 400

@app.route('/admin')
@login_required
def admin():
  with app.app_context():
    db = get_db()
    activities = db.getActivities()
  return render_template('admin.html', user=session.get('user'), activities=activities)  

    
@app.route('/admin-register', methods=['GET', 'POST'])
@login_required
def register():
  if request.method == 'POST':
    #Grab the form values and validate them:
    name = request.form['name']
    surname = request.form['surname']
    email = request.form['email']
    admin = request.form.get('admin', False)
    password = request.form['password']      
    confirm_pass = request.form['confirm_pass']
    dob = request.form['dob']
    barcode = request.form['barcode']
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
          flash('The user <a class="alert-link" href="{0}">{1} {2}</a> already exists.' \
            .format(url_for('displayRecord', id=id), Markup.escape(name), 
              Markup.escape(surname)), 'error')
        else:
          app.logger.debug("No duplicates found.  Registering user in database.")
          id = db.addUser(name, surname, email, home_phone, mobile_phone, \
                   sms_capable, dob, license_number, newsletter=newsletter,
                   admin=admin, password=password) 
          if barcode != '':
            db.storeBarcode(id, barcode)
          db.commit()
          flash("<a class=\"alert-link\" href=\"{2}\"><b>{0} {1}</b></a> has been registered successfully." \
            .format(Markup.escape(name), Markup.escape(surname), 
                    url_for('displayRecord', id=id)),
              'success')
      form = None #clear the form
  
  if request.method == 'GET':
    form = None #Return a blank form
  return render_template('admin-register.html', user=session.get('user'), form=form)
    
@app.route('/reports')
@login_required
def reports():
  with app.app_context():
    db = get_db()
    note_title = db.getMeta('kiosk_note_title')
    
    #get list of report modules:
    available_reports = report_plugins.available_reports
    app.logger.debug("Availble reporting plugins:")
    app.logger.debug(available_reports)
  return render_template('reports.html', user=session.get('user'), 
    note_title=note_title, show_actions=False, available_reports=available_reports)
  
@app.route('/reports/<name>')
@login_required
def reportBuild(name):
  show_actions = False
  with app.app_context():
    db = get_db()
    note_title = db.getMeta('kiosk_note_title')
    
    # Attempt to import the requested reporting library and logic:
    try:
      #Import witchcraft
      report_function = __import__('reports.{0}'.format(name), fromlist=[''])
      output = report_function.build(db=db, request=request)
      if output is not None:
        if len(output) > 0:
          show_actions = True
      app.logger.debug("OUTPUT: {0}".format(output))
    except ImportError:
      return abort(404)
      
    # Run report initializer function
    init_data = None
    if hasattr(report_function, 'init'):
      init_data = report_function.init(db=db, request=request)
      
    #import the appropriate context:
    if hasattr(report_function, 'context'):
      if 'activities' in report_function.context:
        session.activities = db.getActivities()
      if 'services' in report_function.context:
        session.services = db.getServices()

  try:
    return render_template('reports-{0}.html'.format(name), user=session.get('user'), 
      note_title=note_title, show_actions=show_actions, output=output, args=request.args,
      available_reports=report_plugins.available_reports, name=name,
      query_string=request.query_string, init=init_data)
  except jinja2.exceptions.TemplateNotFound:
    app.logger.error("Reporting plugin '{0}' has no matching template.".format(name))
    flash(u"Reporting plugin '{0}' has no matching template. ".format(name), 'error')
    return abort(500)

@app.route('/download/reports/<name>')
@login_required
def reportBuildCSV(name):
  with app.app_context():
    db = get_db()
    note_title = db.getMeta('kiosk_note_title')
    
    # Attempt to import the requested reporting library and logic:
    try:
      #Import witchcraft
      report_function = __import__('reports.{0}'.format(name), fromlist=[''])
      output = report_function.build(db=db, request=request)
      
      if output is not None and len(output) > 0:        
        with tempfile.NamedTemporaryFile(delete=False) as csvfile:
          report_function.build_csv(output, csvfile)
        with open(csvfile.name) as f:
          data = f.read()
        
        date = request.args.get('reportdate', '')
        if date == '':
          date = request.args.get('startdate', '')
        filename = "report-{0}-{1}.csv".format(name, date)
        #Serve up the file:
        response = make_response(data)
        response.headers["Content-Disposition"] = "attachment; filename=" + filename
        return response
        
    except ImportError:
      return abort(404)

@app.route('/print/reports/<name>')
@login_required
def reportBuildPrint(name):
  with app.app_context():
    db = get_db()
    note_title = db.getMeta('kiosk_note_title')
    
    # Attempt to import the requested reporting library and logic:
    try:
      #Import witchcraft
      report_function = __import__('reports.{0}'.format(name), fromlist=[''])
      output = report_function.build(db=db, request=request)
      if output is not None:
        if len(output) > 0:
          show_actions = True
      app.logger.debug("OUTPUT: {0}".format(output))
    except ImportError:
      return abort(404)
      
    #import the appropriate context:
    if hasattr(report_function, 'context'):
      if 'activities' in report_function.context:
        session.activities = 'activities', db.getActivities()
      if 'services' in report_function.context:
        session.services = db.getServices()

  try:
    return render_template('reports-{0}-print.html'.format(name), 
      user=session.get('user'), note_title=note_title, output=output, 
      args=request.args, name=name, query_string=request.query_string)
  except jinja2.exceptions.TemplateNotFound:
    app.logger.error("Reporting plugin '{0}' has no matching template.".format(name))
    flash(u"Reporting plugin '{0}' has no matching template. ".format(name), 'error')
    return abort(500)
    
@app.route('/search', methods=['GET'])
@login_required
def searchAdmin():
  query = request.args.get('q', '')
  if query == '':
    return redirect(url_for('admin'))
  
  with app.app_context():
    db = get_db()
    results = db.search(query)
    if len(results) == 0:
      flash(u"No results for \"{0}\"".format(query), "error")
    
  if len(results) == 1:
    #Go directly to the single result:
    return redirect(url_for('displayRecord', id=results[0]['id']))
  return render_template('search-results.html', user=session.get('user'),
                results=results)
                
@app.route('/autocomplete/names', methods=['GET'])
@login_required
def autocomplete_names():
  term = request.args.get('term', None)
  if term is None:
    return abort(400)
  term = term.strip()
  with app.app_context():
    db = get_db()
    results = db.searchName(term, autocomplete=True)
    response = make_response(json.dumps(results))
    response.headers['Content-Type'] = 'application/json; charset=utf-8'
    return response
    
  
@app.route('/id/<id>', methods=['GET', 'POST'])
@login_required
def displayRecord(id):
  if request.method == "POST":
    name = request.form['name']
    surname = request.form['surname']
    email = request.form['email']
    admin = request.form.get('admin', False)
    password = request.form['password']      
    confirm_pass = request.form['confirm_pass']
    dob = request.form['dob']
    barcode = request.form['barcode']
    license_number = request.form['license_number']
    home_phone = request.form['home_phone']
    mobile_phone = request.form['mobile_phone']
    sms_capable = request.form.get('sms_capable', False)
    newsletter = request.form.get('newsletter', False)
    error = False
    
    #This might not be needed
    if admin == "true": admin = True
    if sms_capable == "true": sms_capable = True
    if newsletter == "true": newsletter = True
    app.logger.debug("SMS: " + str(sms_capable))
    
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
    if password == "********************":
      password = None
      confirm_pass = None
    if password == "": password = None
    
    if error:
      form = request.form #Carryover entered form values
    else:
      with app.app_context(): #Show the saved values
        db = get_db()
        db.updateUser(id, name, surname, email=email, admin=admin, 
                      password=password, dob=dob, newsletter=newsletter,
                      license_number=license_number, home_phone=home_phone,
                      mobile_phone=mobile_phone, sms=sms_capable)
        db.storeBarcode(id, barcode)
        db.commit()
        form = db.getUserByID(id)
        form['barcode'] = db.getBarcodeForId(id)
        flash('Changes saved.', 'success')
    
  else: #Render GET request
    with app.app_context():
      db = get_db()
      form = db.getUserByID(id)
      form['barcode'] = db.getBarcodeForId(id)
  return render_template('profile.html', user=session.get('user'), form=form)


@app.route('/delete/<id>', methods=['POST'])
@login_required
def deleteUser(id):
  with app.app_context():
    db = get_db()
    user = db.getUserByID(id)
    if user is not None:
      db.deleteUser(id)
      db.commit()
      flash('{0} {1} has been succesfully deleted.'
        .format(Markup.escape(user['name']), 
                Markup.escape(user['surname'])),
        'success')
    else:
      flash('Unable to delete user id {0}: User does not exist.'.format(id), 'error')
  return redirect(url_for('index'))

@app.route('/login', methods=['GET', 'POST'])
def login():
  with app.app_context():
    db = get_db()
    site_title = db.getMeta('site_title')
    
    error = None
    if request.method == 'POST':
      email = request.form["email"]
      password = request.form["password"]
      next = request.form["next"]
      auth = db.authenticate(email, password)
      if auth[0]: #Success
        session['logged_in'] = True
        #~ auth[1]['dob'] = auth[1]['dob'].isoformat() if hasattr('isoformat')
        session['user'] = auth[1]
        if next is not None:
          return redirect(next)
        else:
          return redirect(url_for('index'))
      else:
        flash("Username or password is incorrect", "error")
    else:
      next = request.args.get("next", None)
    
    #First time setup?
    user_count = db.userCount()
    if user_count == 1:
      return redirect(url_for('install'))
  return render_template('login.html', site_title=site_title, next_url=next)
  
@app.route('/logout')
def logout():
  session.pop('logged_in', None)
  session.pop('user', None)
  flash("You were logged out succesfully", "info")
  return redirect(url_for('index'))
  
@app.route('/install', methods=['GET', 'POST'])
def install():
  with app.app_context():
    db = get_db()
    user_count = db.userCount()
    
    if user_count == 1:
      if request.method == 'POST':
        name = request.form.get("name", '')
        surname = request.form.get("surname", '')
        email = request.form.get("email", '')
        password = request.form.get("password", '')
        confirm_pass = request.form.get("confirm_pass", '')
        
        #Validate form:
        error = False
        if name == '':
          flash("Display name is required", "error")
          error = True
        if email == '':
          flash("Login name or email is required", "error")
          error = True
        if password == '':
          flash("A password is required for the administrator account", "error")
          error = True
        if password != confirm_pass:
          flash("The passwords entered do not match", "error")
          error = True
        if len(password) < 6:
          flash("Passwords should be six or more characters. " + 
                "Consider changing your password", "info")
        
        if not error:
          db.addUser(name, surname, email=email, admin=True, password=password)
          db.commit()
          flash("Admin account created succesfully.  "+
                "Login with the username '{0}'".format(email), "success")
          return redirect(url_for('admin'))
      
      return render_template('install.html', form=request.form)
        
  return redirect(url_for('admin'))
  
    
def fetchKioskConstants():
  #TODO: This should probably get cached
  db = get_db()
  timeout = db.getMeta('kiosk_timeout')
  warning = db.getMeta('kiosk_timeout_warning')
  title = db.getMeta('kiosk_timeout_title')
  msg = db.getMeta('kiosk_timeout_message')
  clock_in = db.getMeta('kiosk_clock_in')
  clock_out = db.getMeta('kiosk_clock_out')
  kiosk_activity = dbBool(db.getMeta('kiosk_activity'))
  kiosk_service = dbBool(db.getMeta('kiosk_service'))
  return { 'timeout' : timeout, 'timeout_warning' : warning,
            'timeout_title' : title, 'timeout_message' : msg,
            'clock_in' : clock_in, 'clock_out' : clock_out,
            'kiosk_activity' : kiosk_activity, 
            'kiosk_service' : kiosk_service}
    
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
    kiosk_activity = dbBool(db.getMeta('kiosk_activity'))
    kiosk_service = dbBool(db.getMeta('kiosk_service'))
    target = 'checkinNote'
    if kiosk_service:
      target = 'selectService'
    if kiosk_activity:
      target = 'selectActivity'
    
    for record in results:
      record['checked_in'] = db.getCheckinStatus(record['id'])
    
  return render_template('checkin-results.html', results_message=results_message,
        results=results, search = search, kiosk=kiosk,target=target)
  
@app.route('/clock-out', methods=['GET'])
def clockOut():
  ID = request.args.get('id', '')
  with app.app_context():
    db = get_db()
    if db.getUserByID(ID) is not None:
      db.doCheckout(ID)
      db.commit()
  return redirect(url_for('timeclock'))
  
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
    kiosk_activity = db.getMeta('kiosk_activity')
    if not dbBool(kiosk_activity):  #Skip activity selection if disabled
      app.logger.debug("Activity selection disabled.  Skipping to service selection")
      return redirect(url_for('selectServices', ID=ID))
    
    activities = db.getActivities()
    kiosk = fetchKioskConstants()
    title = db.getMeta('kiosk_activity_title')
    allow_multiple = db.getMeta('kiosk_activity_allow_multiple')
  
  return render_template('checkin-activity.html', search=search, id=ID,
              activities=activities, kiosk=kiosk, title=title, allow_multiple=allow_multiple)
  
@app.route('/select-services', methods=['GET'])
def selectServices():
  with app.app_context():
    db = get_db()
    kiosk_activity = dbBool(db.getMeta('kiosk_activity'))
    if not dbBool(db.getMeta('kiosk_service')): #Skip service selection if disabled
      app.logger.debug("Service selection disabled.  Skipping to note entry")
      return redirect(url_for('checkinNote'))
  
    search = request.args.get('search', '')
    ID = request.args.get('id', '')
    #parse and validate selected activities:
    activities = request.args.getlist("activity")
    #validate only if activity selection was enabled
    if len(activities) == 0 and kiosk_activity:
      flash("You must pick at least one activity", "error")
      return redirect(url_for('selectActivity', ID=ID))
    
    services = db.getServices()
    kiosk = fetchKioskConstants()
    title = db.getMeta('kiosk_service_title')
    allow_multiple = dbBool(db.getMeta('kiosk_service_allow_multiple'))
    kiosk["opt_service"] = dbBool(db.getMeta('kiosk_opt_service'))
    
  return render_template('checkin-services.html', search=search, activities=activities, id=ID,
                services=services, kiosk=kiosk, title=title, allow_multiple=allow_multiple)
      
@app.route('/select-opt-service', methods=['GET'])
def checkinOptService():
  with app.app_context():
    db = get_db()
    kiosk_service = dbBool(db.getMeta('kiosk_service'))
    search = request.args.get('search', '')
    ID = request.args.get('id', '')
    activities = request.args.getlist("activity")
    services = request.args.getlist("service")
    opt_services = db.getServices()
    kiosk = fetchKioskConstants()
    title = db.getMeta('kiosk_service_opt_title')
    allow_multiple = dbBool(db.getMeta('kiosk_service_opt_allow_multiple'))
    
    #validate only if service selection was enabled
    if len(services) == 0 and kiosk_service:
      flash("You must pick at least one service", "error")
      return selectServices()
    
  return render_template('checkin-opt-services.html', search=search, activities=activities, id=ID,
                services=services, kiosk=kiosk, title=title, allow_multiple=allow_multiple,
                opt_services=opt_services)
  pass
  
@app.route('/checkin-note', methods=['GET'])
def checkinNote():
  search = request.args.get('search', '')
  ID = request.args.get('id', '')
  #parse and validate selected activities:
  activities = request.args.getlist("activity")
  services = request.args.getlist("service")
  opt_services = request.args.getlist("opt_services")
    
  with app.app_context():
    db = get_db()
    kiosk_service = dbBool(db.getMeta('kiosk_service'))
    kiosk = fetchKioskConstants()
    title = db.getMeta('kiosk_note_title')
    
    if len(services) == 0 and kiosk_service:
      flash("You must pick at least one service", "error")
      return selectServices()
    
  return render_template('checkin-note.html', kiosk=kiosk, title=title, id=ID, search=search,
                  activities=activities, services=services, opt_services=opt_services)
  
@app.route('/checkin-confirm', methods=['POST'])
def checkinConfirm():
  search = request.form['search']
  ID = int(request.form['id'])
  #parse and validate selected activities:
  activitiesID = request.form.getlist("activity")
  servicesID = request.form.getlist("service")
  opt_servicesID = request.form.getlist("opt_services")
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
    opt_services = db.getServiceNameList(opt_servicesID)
    opt_servicesString = ", ".join(opt_services)
    opt_servicesString = servicesString.decode('utf8')
    
    #Record the check-in
    db.doCheckin(person['id'], activities, services, note, opt_services)
    db.commit()
    
  return render_template('checkin-confirm.html', person=person, activities=activitiesString,
                    services=servicesString, note=note, note_title=note_title,
                    opt_services=opt_servicesString)
              
  
@app.errorhandler(500)
def applicationError(error):
  return render_template('error.html'), 500

def get_db():
  app.logger.debug("Enter get_db()")
  if not hasattr(g, 'db'):
    app.logger.debug("No cached database cursor.  Opening new connection...")
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
  
def dbBool(string):
  if string == 't':
    return True
  elif string == 'f':
    return False
  else:
    raise ValueError("Expected either 't' or 'f'")
  
@app.teardown_request
@app.teardown_appcontext
def teardown_request(exception):
  db = getattr(g, 'db', None)
  if db is not None:
    app.logger.debug("Close db")
    db.close()
    
@app.template_filter('strftime')
def _jinja2_filter_datetime(date, fmt=None):
  native = date.replace(tzinfo=None)
  format='%H:%M'  #TODO: i18n
  return native.strftime(format) 
  
@app.template_filter('timedelta')
def _jinja2_filter_timedelta(timedelta):
  hours, remainder = divmod(timedelta.seconds, 3600)
  minutes, seconds = divmod((timedelta.seconds - (3600*hours)), 60)
  return '%s:%02d:%02d' % (hours, minutes, seconds)

@app.template_filter('userbyid')
def _jinja2_filter_userbyid(id):
  app.logger.debug("Filter dereference on id {0}".format(id))
  db = get_db()
  user = db.getUserByID(id)
  return user
  
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

app.json_encoder = DatetimeJSONEncoder

if __name__ == "__main__":
  #~ app.run(host='0.0.0.0')
  app.run()
