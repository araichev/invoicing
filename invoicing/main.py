"""
Main module.

A *timesheet* is a Pandas data frame with at least the columns...

Start simple with most common use case: one invoice, one billing function.
"""
from collections import OrderedDict

import pandas as pd 
import numpy as np 
from jinja2 import Environment, PackageLoader

INPUT_TIME_UNITS = ['min', 'h']

# I/O
def parse_date(date_str):
    if date_str is None:
        return None
    return pd.datetime.strptime(date_str, '%Y%m%d')

def get_convert_to_hours(time_units):
    if time_units == 'min':
        return lambda x: x/60
    elif time_units == 'h':
        return lambda x: x

def read_timesheet(path, input_time_units='h'):
    """
    Read a timesheet located at the given path and return the corresponding
    data frame.
    """
    if input_time_units not in INPUT_TIME_UNITS:
        raise ValueError('input_time_units must be one of', INPUT_TIME_UNITS)
    
    f = pd.read_csv(path, parse_dates=['date'], date_parser=parse_date)
    f = f.sort_values('date')
    # Convert to hours
    convert_to_hours = get_convert_to_hours(input_time_units)
    f['time_spent'] = f['time_spent'].map(convert_to_hours)
    return f

def validate_timesheet(timesheet):
    pass

# Basic timesheet manipulation
def slice_by_dates(timesheet, date1=None, date2=None):
    d1, d2 = map(parse_date, [date1, date2])
    return timesheet.copy().set_index('date')[d1:d2].reset_index()
    
def compute_project_times(timesheet, freq=None, date1=None, date2=None):
    f = slice_by_dates(timesheet, date1, date2)

    if freq is not None:
        f = f.groupby('project').apply(
          lambda x: x.set_index('date')[['time_spent']].resample(freq
          ).sum().fillna(0)).reset_index()
        f = f.rename(columns={'date': 'period_end'})
        f = f[['period_end', 'project', 'time_spent']].sort_values(
          'period_end')
    else:
        f = f.groupby('project').agg({'time_spent': np.sum}
          ).reset_index()

    return f

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

    f = f.rename(columns={'date': 'period_end'})

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
    
    g = f.groupby('period_end').apply(my_agg
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