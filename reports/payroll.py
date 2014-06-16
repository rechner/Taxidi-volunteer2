# Essentially the same as attendance report, but more terse reporting
# (only person, checkin, checkout, and time worked)

import csv

name = "Payroll"
context = ()

def init(db=None, request=None):
  if request is None or db is None:
    return None
  
  sth = db.execute("""SELECT DISTINCT date(checkin) FROM statistics 
                      ORDER BY date DESC LIMIT 10""")
  return {'datelist' : [ a[0] for a in sth ]}
  

def build(db=None, request=None):
  date = request.args.get('reportdate', None)
  if request is None or db is None or date is None:
    return None
    
  a = db.execute("""SELECT statistics.id, person, users.name, users.surname, 
      checkin, checkout, checkout - checkin AS time
    FROM statistics JOIN users ON 
      users.id = statistics.person WHERE %s = DATE(checkin)
    ORDER BY users.surname;""", 
    (date,))
  output = db.getNestedDictionary(a)
    
  a = db.execute("""SELECT COUNT(DISTINCT person) FROM statistics WHERE 
      %s = DATE(checkin);""", (date,))
  count = a[0][0]
    
  return output, count

def build_csv(results, csvfile):
  #~ raise Exception("Debug")
  csvwriter = csv.DictWriter(csvfile, delimiter=',', quotechar='"', 
    fieldnames=('name', 'surname', 'checkin', 'checkout', 'time'),
    extrasaction='ignore')
  csvwriter.writeheader()
  for row in results[0]:
    row['checkin'] = strftime(row['checkin'])
    row['checkout'] = strftime(row['checkout'])
    row['time'] = strfdelta(row['time'], "{hours}:{minutes:02d}:{seconds:02d}")
    csvwriter.writerow(row)
    
def strftime(date):
  if date is None:
    return "None"
  native = date.replace(tzinfo=None)
  format='%H:%M'  #TODO: i18n
  return native.strftime(format) 

def strfdelta(tdelta, fmt):
  if tdelta is None:
    return "None"
  d = {"days": tdelta.days}
  d["hours"], rem = divmod(tdelta.seconds, 3600)
  d["minutes"], d["seconds"] = divmod(rem, 60)
  return fmt.format(**d)
