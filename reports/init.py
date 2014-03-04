import pkgutil

report_index = [name for _, name, _ in pkgutil.iter_modules(['reports'])]
report_index.remove('init')

report_titles = []
for report in report_index:
  module = __import__('reports.{0}'.format(report), fromlist=[''])
  report_titles.append(module.name)
  
available_reports = [ {'path' : i[0], 'title' : i[1] } for i in zip(report_index, report_titles) ]
