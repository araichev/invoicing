Invoicing
**********
A Python 3.4+ project to create invoices from CSV timesheets.


Installation
=============
- Create a Python virtual environment and ``pip install invoicing``


Usage
======

- Timesheet CSVs must contain at least the columns

    * ``date``: date in a consistent format
    * ``project``: project name
    * ``time_spent``: minutes or hours (but not both) 
      spent on the project on the date 
 
- For example usage, play with the IPython notebook ``ipynb/examples.ipynb``


Notes
======
- Development status is Alpha
- Project uses semantic version


Authors
========
- Alex Raichev, 2016-04