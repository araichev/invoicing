Invoicing
**********
A Python 3.4 project to create simple invoices from CSV timesheets.


Usage
======

Timesheet format
-----------------
Input timesheets must contain at least the columns

- ``date``: date in the form YYYYMMDD
- ``project``: project name
- ``is_billable``: 1 if the project is billable; 0 otherwise
- ``time_spent``: integer minutes spent on the project on that date 
- ``comment``: comment on the time spent 
 

Notes
======
- Development status is Pre-alpha


Authors
========
- Alex Raichev, 2016-04