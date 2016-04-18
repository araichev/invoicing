"""
Main module.

A *timesheet* is a Pandas data frame with at least the columns...

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

def partition_by_tiered_rates(t, tiered_rates_df):
    f = tiered_rates_df.copy()
    prev_c = 0
    time_spent = []
    for c in f['time_cutoff'].values:
        delta = c - prev_c
        if t >= delta:
            time_spent.append(delta)
            t -= delta
        elif t > 0:
            time_spent.append(t)
            t = 0
        else:
            time_spent.append(0)
        prev_c = c
    f['time_spent'] = time_spent
    return f

def bill_at_tiered_rates(timesheet, tiered_rates_df, freq='W', 
  groupby_project=False, date1=None, date2=None):
    # Slice
    timesheet = slice_by_dates(timesheet, date1, date2)

    # Resample to frequency by summing
    if groupby_project:
        f = timesheet.groupby('project').apply(
          lambda x: x.set_index('date')[['time_spent']].resample('W').sum())
    else:
        f = timesheet.set_index('date')[['time_spent']].resample('W').sum()
    
    # Partition each group by tiered rates
    def my_agg(group):
        t = group['time_spent'].iat[0]
        return partition_by_tiered_rates(t, tiered_rates_df)

    f = f.reset_index().rename(columns={'date': 'period_end'})
    
    if groupby_project:
        cols = ['period_end', 'project']
        drop_cols = ['level_2']
    else:
        cols = ['period_end']
        drop_cols = ['level_1']
        
    g = f.groupby(cols).apply(my_agg).reset_index().drop(drop_cols, axis=1)

    # Compute cost
    g['cost'] = g['time_spent']*g['rate']

    return g

# TODO: combine previous billing functions into this one
def bill_piecewise_linearly(timesheet, rates_df, base_fees_df=None,
  freq=None, groupby_project=False, date1=None, date2=None):
    """
    ``rates_df`` has the columns:

    - ``'project'``
    - ``'time_cutoff'``: use ``np.inf`` for infinite/no cutoff
    - ``'rate'``

    ``base_fees_df`` has the columns:

    - ``'project'``
    - ``'base_fee'``
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