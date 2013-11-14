#!/usr/bin/env python
#-*- coding:utf-8 -*-
from flask import Flask, Response, render_template, request, session, g
from contextlib import closing

import config

app = Flask(__name__)
app.config.from_object("config.DevelopmentConfig")

@app.route('/')
def index():
  return Response("Hello world!")
  
@app.route('/hello/')
def hello():
  return render_template('hello.html')
  
@app.route('/login', methods=['GET', 'POST'])
def login():
  error = None
  if request.method == 'POST':
    pass
  else:
    pass
    
  return render_template('login.html')
    
    
@app.route('/timeclock', methods=['GET', 'POST'])
def timeclock():
  if request.method == 'POST':
    return render_template('checkin-results.html', 
      results=({'id' : 1234, 'name' : 'John', 'lastname' : 'Volunteer', 'phone' : '(317) 555-5555'},
               {'id' : 1234, 'name' : 'John', 'lastname' : 'Volunteer', 'phone' : '(317) 555-5555'})
    )
  return render_template('checkin-search.html', error=None)
  
@app.route('/timeclock-search')
def timeclockSearch():
  search = request.args.get('search', '')
  
  return render_template('checkin-results.html', 
        results=({'id' : 1234, 'name' : 'John', 'lastname' : 'Volunteer', 'phone' : '(317) 555-5555'},
                 {'id' : 1234, 'name' : 'John', 'lastname' : 'Volunteer', 'phone' : '(317) 555-5555'}),
        search = search
  )
  
  
@app.route('/select-activity', methods=['GET'])
def selectActivity(error=None):
  search = request.args.get('search', '')
  ID = request.args.get('id', '')
  return render_template('checkin-activity.html', search=search, id=ID, error=error,
              activities=({'id': 1, 'name': 'Parking'},{'id': 2, 'name': 'Greeter'},
                          {'id': 3, 'name': 'Usher'}, {'id': 4, 'name': 'Bleh'},
                          {'id': 5, 'name': 'Test'}))
  
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

#~ @app.before_request
#~ def before_request():
    #~ g.db = connect_db()
#~ 
#~ @app.teardown_request
#~ def teardown_request(exception):
    #~ db = getattr(g, 'db', None)
    #~ if db is not None:
        #~ db.close()

if __name__ == "__main__":
  app.run()
