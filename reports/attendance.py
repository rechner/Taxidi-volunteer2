#!/usr/bin/env python
#-*- coding:utf-8 -*-

import csv

#TODO: Cache counts from here for building graphs

name = "Attendance"
context = ('activities', 'services')

def init(db=None, request=None):
  if request is None or db is None:
    return None
  
  sth = db.execute("SELECT DISTINCT date(checkin) FROM statistics LIMIT 10")
  return {'datelist' : [ a[0] for a in sth ]}
  

def build(db=None, request=None):
  date = request.args.get('reportdate', None)
  if request is None or db is None or date is None:
    return None
  
  selected_services = request.args.getlist('services')
  selected_activities = request.args.getlist('activities')
  
  #Names from the above lists are passed in as integer id's so we need to
  #dereference them first from the stored hashes:
  db_services = db.getServices()
  db_activities = db.getActivities()
  
  services =   [ service['name'] for service in db_services \
                 if str(service['id']) in selected_services ]
  activities = [ activity['name'] for activity in db_activities \
                 if str(activity['id']) in selected_activities ]
                 
  if selected_activities == []:
    activities = [ activity['name'] for activity in db_activities ]
    
  if selected_services == []:
    services = [ service['name'] for service in db_services ]
    
  counts = {}
  output = {}
  #Fetch order by activity for each service:
  for service in services:
    a = db.execute("""SELECT person, users.name, users.surname, statistics.activity,
        statistics.note, checkin, checkout - checkin AS time, statistics.service
      FROM statistics JOIN users ON 
        users.id = statistics.person WHERE %s = DATE(checkin)
        AND %s = ANY(service) AND
        activity && %s ORDER BY activity;""", 
      (date, service, activities))
    output[service] = db.getNestedDictionary(a)
    
    a = db.execute("""SELECT COUNT(person) FROM statistics WHERE 
        %s = DATE(checkin) AND
        %s = ANY(service) AND
        activity && %s;""", (date, service, activities))
    counts[service] = a[0][0]
    
  a = db.execute("""SELECT COUNT(person) FROM statistics WHERE 
        %s = DATE(checkin);""", (date,))
  counts['__total__'] = a[0][0]
    
  return output, counts

def build_csv(results, csvfile):
  csvwriter = csv.DictWriter(csvfile, delimiter=',', quotechar='"', 
    fieldnames=results[0][results[0].keys()[0]][0].keys()) #KEYS KEYS KEYS
  csvwriter.writeheader()
  for service in sorted(results[0].keys()):
    csvfile.write("Service: " + service)
    for row in results[0][service]:
      csvwriter.writerow(row)
