# Essentially the same as attendance report, but more terse reporting
# (only person, checkin, checkout, and time worked) and compiles total
# hours worked for each person in a given date range.

import csv

name = "Payroll Range"
context = ()

def init(db=None, request=None):
  return None  

def build(db=None, request=None):
  startdate = request.args.get('startdate', None)
  enddate = request.args.get('enddate', None)
  if request is None or db is None or startdate is None or enddate is None:
    return None
  if startdate == '' or enddate == '':
    return None
    
  # Get id's of people in this date range and flatten into a list
  a = db.execute("""SELECT DISTINCT person 
     FROM statistics
    WHERE DATE(checkin) >= %s and DATE(checkout) <= %s
    ORDER BY person ASC""",
    (startdate, enddate))
  people = [ row['person'] for row in db.getNestedDictionary(a) ]
  
  # Get missing punches
  a = db.execute("""SELECT statistics.id, person, users.name, users.surname, 
      checkin, checkout, checkout - checkin AS time
    FROM statistics JOIN users ON 
      users.id = statistics.person 
    WHERE DATE(checkin) >= %s AND checkout IS NULL
    ORDER BY users.surname""", (startdate,))
  missing_punches = db.getNestedDictionary(a)
  
  output = []
  for person in people:
    # Get total hours worked:
    a = db.execute("""SELECT EXTRACT(epoch FROM SUM(checkout - checkin))/3600 AS hours
       FROM statistics
      WHERE person = %s AND checkin >= DATE(%s) AND checkout <= DATE(%s)""", 
      (person, startdate, enddate))
    if len(a) == 0 or a[0][0] is None:
      continue #Nothing here for some reason: skip it (shouldn't happen!)
    hours = round(a[0][0], 2)
    
    # Get person details:
    a = db.execute("""SELECT name, surname FROM users WHERE id = %s;""", (person,))
    if len(a) == 0:
      continue
    name = db.getNestedDictionary(a)[0]
    
    output.append({ 'name'    : name['name'],
                    'surname' : name['surname'],
                    'time'    : hours,
                    'id'      : person })
    
  return sorted(output, key=lambda row: row['surname']), missing_punches

def build_csv(results, csvfile):
  #~ raise Exception("Debug")
  csvwriter = csv.DictWriter(csvfile, delimiter=',', quotechar='"', 
    fieldnames=('surname', 'name', 'time'),
    extrasaction='ignore')
  csvwriter.writeheader()
  for row in results[0]:
    csvwriter.writerow(row)
    
