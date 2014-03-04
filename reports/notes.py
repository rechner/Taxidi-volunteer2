import csv

name = "%note_title%"

def build(db=None, request=None):
  if request is not None and db is not None:
    date = request.args.get('reportdate', None)
    if date is not None:
      a = db.execute("""SELECT person, users.name, users.surname,
        statistics.note FROM statistics JOIN users ON 
        users.id = statistics.person WHERE %s = DATE(checkin)
        AND note IS NOT NULL;""", (date,))
      return db.getNestedDictionary(a)
  return None
  
  
def build_csv(results, csvfile):
  csvwriter = csv.DictWriter(csvfile, delimiter=',', quotechar='"', 
    fieldnames=results[0].keys())
  csvwriter.writeheader()
  for row in results:
    csvwriter.writerow(row)
  
