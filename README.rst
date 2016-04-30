Invoicing
**********
A Python 3.4+ package that consumes CSV timesheets, operates on them in combination with billing functions, and produces HTML invoices.
At this stage of development, only the most common use case is handled, namely one billing function per invoice.


Installation
=============
- Create a Python virtual environment and ``pip install invoicing``


Usage
======

- A timesheet CSV must contain at least the columns

    * ``'date'``: date in a consistent format, e.g. YYYYMMDD
    * ``'project'``: project name
    * ``'time_spent'``: time spent on project on date in a consistent format, e.g. minutes  
 
- For examples, play with the IPython notebook ``ipynb/examples.ipynb``


Notes
======
- Development status is Alpha
- Project uses semantic version


Authors
========
- Alex Raichev, 2016-04