Invoicing
**********
A simple Python 3.4+ package for creating customizable HTML invoices from CSV timesheets.
Designed for freelancing developers.
Uses Pandas and Jinja2 to do the heavy lifting.


Installation
=============
Create a Python virtual environment and ``pip install git+https://github.com/araichev/invoicing``


Usage
======
Play with the IPython notebook and invoice template in the ``examples`` directory to get the idea


Documentation
=============
In ``docs`` and on RawGit `here <https://rawgit.com/araichev/invoicing/master/docs/_build/singlehtml/index.html>`_.


Notes
======
- Development status is Alpha
- Project uses semantic versioning
- At this stage of development, only the most common use case is handled, namely one billing function per invoice. Also, only HTML invoices are generated. You can use your browser to save these to PDF, if you like. Maybe in the future i'll incorporate wkhtmltopdf to automatically convert the HTML to PDF.


Todo
=====
- Add automated tests


Authors
========
- Alex Raichev, 2016-04
