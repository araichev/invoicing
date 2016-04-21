"""
Main module.

Coventions
------------
A **timesheet** is a Pandas data frame with at least the columns

- ``'date'``: date worked was done; Pandas Date object
- ``'project'``: project the work is part of
- ``'time_spent'``: time spent on work; hours

A **biller** is...

All dates are YYYYMMDD strings unless specified otherwise.

Start simple with most common use case: one invoice, one billing function.
"""
from collections import OrderedDict

import pandas as pd 
import numpy as np 
from jinja2 import Environment, PackageLoader


DATE_FORMAT = '%Y%m%d'
VALID_TIME_UNITS = ['min', 'h']

# I/O
def parse_date(date_str, date_format=DATE_FORMAT):
    if date_str is None:
        return None
    return pd.datetime.strptime(date_str, '%Y%m%d')

def build_convert_to_hours(time_units):
    if time_units == 'min':
        return lambda x: x/60
    elif time_units == 'h':
        return lambda x: x

def read_timesheet(path, date_format=DATE_FORMAT, input_time_units='h'):
    """
    Read a timesheet CSV located at the given path and return the corresponding
    timesheet data frame.
    ``date_format`` is the date string format contained in the CSV.
    ``input_time_units`` is a string representing the units of time recorded
    in the CSV, e.g. ``'min'`` for minutes.
    Acceptable input time units are listed in ``VALID_TIME_UNITS``. 
    """
    if input_time_units not in VALID_TIME_UNITS:
        raise ValueError('input_time_units must be one of', VALID_TIME_UNITS)
    
    f = pd.read_csv(path, parse_dates=['date'], 
      date_parser=lambda x: parse_date(x, DATE_FORMAT))
    f = f.sort_values('date')
    # Convert to hours
    convert_to_hours = build_convert_to_hours(input_time_units)
    f['time_spent'] = f['time_spent'].map(convert_to_hours)
    return f

def validate_timesheet(timesheet):
    pass

# Basic timesheet manipulation
def slice_by_dates(timesheet, date1=None, date2=None):
    """
    Return the portion of the timesheet for which the date satisfies
    date1 <= date <= date2.
    """
    d1, d2 = map(parse_date, [date1, date2])
    return timesheet.copy().set_index('date')[d1:d2].reset_index()
    
def compute_project_times(timesheet, date1=None, date2=None, freq=None):
    """
    Slice the given timesheet by the given dates then aggregate total
    time spent by project.
    If a Pandas frequency string is given (e.g. 'W' for calendar week),
    then resample by that frequency and then aggregate time spent by project.
    Return a data frame with the columns:

    - ``'start_date'``
    - ``'end_date'``
    - ``'project'``
    - ``'time_speent'``
    """
    f = slice_by_dates(timesheet, date1, date2)

    if freq is not None:
        f = f.groupby('project').apply(
          lambda x: x.set_index('date')[['time_spent']].resample(freq
          ).sum().fillna(0)).reset_index()
        f = f[['date', 'project', 'time_spent']].sort_values(
          'date')
        f['period'] = f['date'].map(lambda x: pd.Period(x, freq))
        f['start_date'] = f['period'].map(lambda x: x.start_time)
        f['end_date'] = f['period'].map(lambda x: x.end_time)
    else:
        start_date, end_date = f['date'].min(), f['date'].max()
        f = f.groupby('project').agg({'time_spent': np.sum}
          ).reset_index()
        f['start_date'] = start_date
        f['end_date'] = end_date

    return f[['start_date', 'end_date', 'project', 'time_spent']].copy()


# Billing
def decompose(x, bins):
    """
    EXAMPLES::

        >>> decompose(17, [10, 15, np.inf])
        [10, 7, 0]
        >>> decompose(27, [10, 15, np.inf])
        [10, 15, 2]

    """
    parts = []
    prev_bin = 0
    for bin in bins:
        if x >= bin:
            parts.append(bin)
            x -= bin
        elif x > 0:
            parts.append(x)
            x = 0
        else:
            parts.append(0)
    return parts 

def build_linear_biller(rate, base_fee=0, freq=None, name=None):
    """
    """
    return build_piecewise_linear_biller(base_fee=base_fee,
        bins=[np.inf], rates=[rate], freq=freq, name=name)

def build_piecewise_linear_biller(bins, rates, base_fee=0, freq=None, 
  name=None):
    """
    """
    def biller(x):
        return base_fee + np.dot(decompose(x, bins), rates)
    
    biller.name = name
    biller.kind = 'piecewise_linear'
    biller.base_fee = base_fee
    biller.bins = bins
    biller.rates = rates
    biller.freq = freq
    return biller

# TODO: Replace date column with start date and end date columns
def compute_cost(timesheet, biller, date1=None, date2=None):  
    """
    Slice the given timesheet to the given dates,
    and return a new data frame with the columns

    - ``'project'``
    - ``'time_spent'``
    - ``'rate'``: currency per hour
    - ``'cost'``: time spent multiplied by rate
    """  
    # Slice
    f = slice_by_dates(timesheet, date1, date2)

    # Resample to frequency by summing
    # if bill_by_project:
    #     f = timesheet.groupby('project').apply(
    #       lambda x: x.set_index('date')[['time_spent']].resample('W').sum())
    # else:
    #     f = timesheet.set_index('date')[['time_spent']].resample('W').sum()

    if biller.freq is not None:
        freq = biller.freq
        f = timesheet.set_index('date')[['time_spent']].resample(freq).sum()
        f = f.reset_index()


    if biller.base_fee:
        new_bins = [0] + biller.bins
    else:
        new_bins = biller.bins

    def my_agg(group):
        d = OrderedDict()
        t = group['time_spent'].iat[0]
        d['time_spent'] = pd.Series(decompose(t, new_bins))
        c1 = d['time_spent'].cumsum().map(biller)
        c2 = c1.shift(1).fillna(0)
        cost = c1 - c2
        d['rate'] = cost/d['time_spent']
        d['cost'] = cost
        return pd.DataFrame(d)
    
    g = f.groupby('date').apply(my_agg
      ).reset_index().drop(['level_1'], axis=1)
    return g

# Reporting

# Load Jinja templates
ENV = Environment(loader=PackageLoader('main', 'templates'))

def make_invoice(timesheet, template='invoice_alex.html'):
    template = ENV.get_template(template)
    context = {
      'invoice_code': 'bingo',
      'issue_date': '2016-04-16',
      'due_date': '2016-04-17',
      'sender': 'Alex',
      'sender_address': '1 Queen St, Auckland 1001',
      'sender_email': 'a@b.com',
      'receiver': 'Wingnut',
      'receiver_address': '2 Victoria St, Auckland 1001',
      }
    html = template.render(context)
    return html