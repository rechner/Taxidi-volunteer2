# Creating a New Report #

Adding a new report is relatively simple.  For reference, it is recommended 
you look at the "notes" report.  To create a report module, there's three
files that need to be created:

* reports/&lt;reportname&gt;.py
* templates/report-&lt;reportname&gt;.html
* templates/report-&lt;reportname&gt;-print.html

The first contains the report logic, and is detailed in the section below.
The two templates are responsible for presentation for the web interface and
a printer-friendly view.  See the presentation section for more details.

# &lt;reportname&gt;.py #

Reporting logic files must implement the following attributes:

  name = "Friendly Report Name"
  context = () #Optional
  
  def init(db=None, request=None):
    pass
  
  def build(db=None, request=None):
    pass
    
  def build_csv(results, csvfile):
    pass
    
The name attribute is a string representation for the name of the report.
This can be anything, but the special name `"%note_title%"` will be replaced
by the meta name for the `note` column in the database.

## init() ##

This function is run each time the form is requested, either as part of a
report or when displaying a blank form.  The result from this function is
available from the template in the `init` variable.

## build() ##

This is the primary report building section.  The db file passed in can be
used to build queries, which are then called and passed into the report 
template to be displayed.

## build_csv() ##

`build_csv()` is used as the logic for building a downloadable comma-separated
value spreadsheet from the results of the `build()` method.  In most cases,
this will be handled by calls to the `csv` python module, although anything
can be written to the `csvfile` file handle.

## importing context ##

Sometimes it will be necessary or convenient to pull in some of the flask
views.py context for the rendered template via the `request` session object. 
Currently the following contexts are supported:

* `activities` - A list of system activities, as reported by 
  `db.getActivities()`
* `services` - A list of available services, as reported by `db.getServices()`

# Templates #

Template names matching each reports module must be present or the application
will return a 500 server error.  Reports templates should extend the 
`reports.html` template, and implement the `parameters` and `output` blocks.
The following variables are available in the template namespace for these
reports:

* note_title
* output
* args
* available_reports
* name
* query_string
* request

Further contexts are available when explicitly imported by the module's context
declaration (see "importing context" above).

See the `widgets.html` template for convenient widgets for the prompting 
for report parameters.
