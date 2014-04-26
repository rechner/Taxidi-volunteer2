import csv

name = "Birthday"

def init(db=None, request=None):
  return None
  
def build(db=None, request=None):
  startdate = request.args.get('startdate', None)
  enddate = request.args.get('enddate', None)
  
  if request is None or request is None or startdate is None:
    return None
  if enddate is None:
    enddate = startdate
  
  sth = db.execute("""SELECT id, name, surname, email, dob, last_seen,
        home_phone, mobile_phone, date_part('year', age(dob)) as age 
      FROM "users" WHERE
         date_part('month', dob) >= date_part('month', date(%s))
       AND
         date_part('day', dob) >= date_part('day', date(%s))
       AND
         date_part('month', dob) <= date_part('month', date(%s))
       AND
         date_part('day', dob) <= date_part('day', date(%s))
      ORDER BY
        concat(date_part('month', dob), date_part('day', dob));""",
        (startdate, startdate, enddate, enddate))
  return db.getNestedDictionary(sth)

def build_csv(results, csvfile):
  csvwriter = csv.DictWriter(csvfile, delimiter=',', quotechar='"', 
    fieldnames=results[0].keys())
  csvwriter.writeheader()
  for row in results:
    csvwriter.writerow(row)
