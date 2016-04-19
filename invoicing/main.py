"""
Main module.

A *timesheet* is a Pandas data frame with at least the columns...

TODO:

- Expand :func:`compute_cost` to allow for different billers for different projects
"""
from collections import OrderedDict

import pandas as pd 
import numpy as np 
from jinja2 import Environment, PackageLoader

TIME_UNITS = ['min', 'h']

# Load Jinja templates
ENV = Environment(loader=PackageLoader('main', 'templates'))

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

def read_timesheet(path, time_units='h'):
    """
    Read a timesheet located at the given path and return the corresponding
    data frame.
    """
    if time_units not in TIME_UNITS:
        raise ValueError('time_units must be one of', TIME_UNITS)
    
    f = pd.read_csv(path, parse_dates=['date'], date_parser=parse_date)
    f = f.sort_values('date')
    # Convert to hours
    convert_to_hours = get_convert_to_hours(time_units)
    f['time_spent'] = f['time_spent'].map(convert_to_hours)
    return f

def validate_timesheet(timesheet):
    pass

def slice_by_dates(timesheet, date1=None, date2=None):
    d1, d2 = map(parse_date, [date1, date2])
    return timesheet.copy().set_index('date')[d1:d2].reset_index()
    
# Billing
# TODO: Subsume this function under compute_cost()
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

def partition(x, cuts):
    """
    EXAMPLES::

        >>> partition(17, [10, 15, np.inf])
        [10, 7, 0]
        >>> partition(27, [10, 15, np.inf])
        [10, 15, 2]

    """
    parts = []
    prev_cut = 0
    for cut in cuts:
        if x >= cut:
            parts.append(cut)
            x -= cut
        elif x > 0:
            parts.append(x)
            x = 0
        else:
            parts.append(0)
    return parts 

def build_piecewise_linear_biller(base_fee, cuts, rates):
    """
    Use ``cuts = [np.inf]`` for a single-rate biller.
    """
    def biller(x):
        return base_fee + np.dot(partition(x, cuts), rates)
    
    biller.kind = 'piecewise_linear'
    biller.base_fee = base_fee
    biller.cuts = cuts
    return biller

def compute_cost(timesheet, biller, freq='W', cuts=(), groupby_project=False, 
  date1=None, date2=None):  
    """
    Slice the given timesheet to the given dates,
    and return a new data frame with the columns

    - ``'project'``
    - ``'time_spent'``
    - ``'rate'``: currency per hour
    - ``'cost'``: time spent multiplied by rate

    To be continued...
    """  
    # Slice
    timesheet = slice_by_dates(timesheet, date1, date2)

    # Resample to frequency by summing
    if groupby_project:
        f = timesheet.groupby('project').apply(
          lambda x: x.set_index('date')[['time_spent']].resample('W').sum())
    else:
        f = timesheet.set_index('date')[['time_spent']].resample('W').sum()

    f = f.reset_index().rename(columns={'date': 'period_end'})

    if groupby_project:
        cols = ['period_end', 'project']
        drop_cols = ['level_2']
    else:
        cols = ['period_end']
        drop_cols = ['level_1']
        
    # Partition time spent
    if not cuts:
        cuts = [np.inf]
        
    def my_agg(group):
        d = OrderedDict()
        t = group['time_spent'].iat[0]
        d['time_spent'] = pd.Series(partition(t, cuts))
        c1 = d['time_spent'].cumsum().map(biller)
        c2 = c1.shift(1).fillna(0)
        cost = c1 - c2
        d['rate'] = cost/d['time_spent']
        d['cost'] = cost
        return pd.DataFrame(d)
    
    g = f.groupby(cols).apply(my_agg).reset_index().drop(
      drop_cols, axis=1)
    return g

# Aggregating
def agg_by_project(timesheet):
    f = timesheet.copy()
    cols = ['date', 'project', 'time_spent', 'cost']
    return f[cols].groupby('project').agg(np.sum)

# Reporting
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