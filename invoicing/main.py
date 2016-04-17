"""
Main module.

A *timesheet* is a Pandas data frame with at least the columns...
"""
from collections import OrderedDict

import pandas as pd 
import numpy as np 
from jinja2 import Environment, PackageLoader


# Load Jinja templates
ENV = Environment(loader=PackageLoader('main', 'templates'))

# I/O
def parse_date(date_str):
    if date_str is None:
        return None
    return pd.datetime.strptime(date_str, '%Y%m%d')

def read_timesheet(path):
    """
    Read a timesheet located at the given path and return the corresponding
    data frame.
    """
    f = pd.read_csv(path, parse_dates=['date'], date_parser=parse_date)
    f = f.sort_values('date')
    # Convert from minutes to hours
    f['time_spent'] /= 60
    return f

def validate_timesheet(timesheet):
    pass

def slice_by_dates(timesheet, date1=None, date2=None):
    d1, d2 = map(parse_date, [date1, date2])
    return timesheet.copy().set_index('date')[d1:d2].reset_index()
    
# Billing
def bill_at_project_rates(timesheet, project_rates_df,
  date1=None, date2=None):
    """
    Slice the given timesheet to the given dates,
    and return a new data frame with the columns

    - ``'project'``
    - ``'time_spent'``
    - ``'rate'``: currency per hour
    - ``'cost'``: time spent multiplied by rate

    Get the rates per project from the data frame
    ``project_rates_df``, which has the columns:

    - ``'project'``
    - ``'rate'``.
    """
    f = slice_by_dates(timesheet, date1, date2)
    cols = ['project', 'time_spent']
    g = f[cols].groupby('project').agg(np.sum).reset_index()
    g = g.merge(project_rates_df)
    g['cost'] = g['time_spent']*g['rate']
    return g

def bill_at_tiered_rates(timesheet, tiers_df,
  date1=None, date2=None):
    """
    Slice the given timesheet to the given dates,
    group the time spent into periods of (Pandas) frequency
    ``freq``, and return a data frame with the columns

    ...
    """
    pass

# Aggregating
def agg_by_project(timesheet):
    f = timesheet.copy()
    cols = ['date', 'project', 'time_spent', 'cost']
    return f[cols].groupby('project').agg(np.sum)

# Reporting
def make_invoice(timesheet, template='invoice_alex.html'):
    template = ENV.get_template(template)
    context = {
      'sender': 'Alex',
      'invoice_code': 'bingo',
      'issue_date': '2016-04-16',
      'due_date': '2016-04-17',
      }
    html = template.render(context)
    return html