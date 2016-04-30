Invoicing
**********
A Python 3.4+ package that turns CSV timesheets into customizable HTML invoices.
Uses Pandas and Jinja2 to do the heavy lifting.


Installation
=============
- Create a Python virtual environment and ``pip install invoicing``


Usage
======
- Play with the IPython notebook and invoice template in the ``examples`` directory to get the idea
- Read the short ``main.py`` module for more details
- Better docs coming soon 


Notes
======
- Development status is Alpha
- Project uses semantic versioning
- At this stage of development, only the most common use case is handled, namely one billing function per invoice. Also, only HTML invoices are generated. You can use your browser to save these to PDF, if you like. Maybe in the future i'll incorporate `wkhtmltopdf <http://wkhtmltopdf.org/>`_ to automatically convert the HTML to PDF.


Todo
=====
- Document billers more
- Make Sphinx docs
- Add automated tests


Authors
========
- Alex Raichev, 2016-04