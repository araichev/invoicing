"""
Main module.

CONVENTIONS:

- A timesheet object is a Pandas DataFrame object with at least the columns

    * ``'date'``: date worked was done; datetime object
    * ``'project'``: project the work is part of
    * ``'time_spent'``: time spent on work; hours

- A biller is a univariate function that maps time spent to cost in some currency units
- All dates described below are YYYYMMDD strings unless specified otherwise

"""
from collections import OrderedDict
from pathlib import Path 

import pandas as pd 
import numpy as np
import jinja2 as j2

#: Default date format
DATE_FORMAT = '%Y%m%d'
#: Acceptable time units
VALID_TIME_UNITS = [
  'min', # minutes
  'h', # hours
  ]

#---------------------------------------
# Reading
#---------------------------------------
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
    Read a timesheet CSV located at the given path (string or Path object)
    and return its corresponding timesheet data frame.
    The timesheet must contain at least the columns

    - ``'date'``: date string in the format specified by ``date_format``, 
      e.g '%Y%m%d'
    - ``'project'``: project name; string
    - ``'time_spent'``: time spent on project in units specified by
      the string ``input_time_units`` which must lie in ``VALID_TIME_UNITS``,
      e.g. 'min' for minutes.
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

#---------------------------------------
# Manipulation
#---------------------------------------
def slice_by_dates(timesheet, date1=None, date2=None):
    """
    Return the portion of the timesheet for which the date satisfies
    date1 <= date <= date2.
    """
    d1, d2 = map(parse_date, [date1, date2])
    return timesheet.copy().set_index('date')[d1:d2].reset_index()
    
def compute_project_summary(timesheet, date1=None, date2=None, freq=None):
    """
    Slice the given timesheet by the given dates then aggregate total
    time spent by project.
    If a Pandas frequency string is given (e.g. 'W' for calendar week),
    then resample by that frequency and then aggregate time spent by project.
    Return a data frame with the columns:

    - ``'start_date'``: start date of the time period corresponding to the
      given frequency, or the first date in the sliced timesheet
    - ``'end_date'``: end date of the time period corresponding to the
      given frequency, or the last date in the sliced timesheet
    - ``'project'``
    - ``'time_spent'``: total timespent on project in period
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

#---------------------------------------
# Billing
#---------------------------------------
def decompose(x, bins):
    """
    Given a number x (the input ``x``)
    and a list of numbers x_1, x_2, ..., x_n
    (the input list ``bins``) whose sum is at least x and
    whose last element may equal the non-number ``np.inf``
    (which represents positive infinity),
    find the least k < n such that 

        x = x_1 + x_2 + ... + x_k + r

    where 0 <= r < x_{k+1}.
    Return the list [x_1, x_2, ..., x_k, r, 0, ..., 0]
    of length n.
    
    EXAMPLES::

        >>> decompose(17, [10, 15, np.inf])
        [10, 7, 0]
        >>> decompose(27, [10, 15, np.inf])
        [10, 15, 2]
        >>> decompose(17, [np.inf])
        [17]
        >>> decompose(17, [10])
        [17]

    """
    # Validity check
    if x > sum(bins):
        raise ValueError('The sum of the bins must be at least as great as x')
    
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
    Return a biller with the given hourly rate, base fee, 
    and billing frequency 
    (Pandas frequency string such as 'W' for weekly billing).
    Uses :func:`build_piecewise_linear_biller`.

    EXAMPLES::

        >>> b = build_linear_biller(100, base_fee=1)
        >>> b(17)
        171
        >>> b.__dict__
        {'base_fee': 3,
        'bins': [inf],
        'freq': 'M',
        'kind': 'linear',
        'name': None,
        'rates': [30]}

    """
    biller = build_piecewise_linear_biller(base_fee=base_fee,
        bins=[np.inf], rates=[rate], freq=freq, name=name)
    biller.kind = 'linear'
    return biller 

def build_piecewise_linear_biller(bins, rates, base_fee=0, freq=None, 
  name=None):
    """
    Return a biller that charges at the given billing frequency
    (Pandas frequency string such as 'W' for weekly billing)
    the given base fee plus the given hourly rates for the given 
    chunks of times listed in ``bins``.

    EXAMPLES::

        >>> bins = [10, 15, np.inf]
        >>> decompose(27, bins)
        [10, 15, 2]
        >>> rates = [1, 2, 3]
        >>> b = build_piecewise_linear_biller(bins, rates, base_fee=1)
        >>> b(27)
        47 # = 1 + 1*10 + 2*15 + 3*2  
        >>> b.__dict__
        {'base_fee': 1,
        'bins': [10, 15, inf],
        'freq': None,
        'kind': 'piecewise_linear',
        'name': None,
        'rates': [1, 2, 3]}

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

def compute_cost_summary(timesheet, biller, date1=None, date2=None):  
    """
    Slice the given timesheet to the given dates and compute
    the cost of the time spent according to the given biller.
    Return a new data frame with the columns

    - ``'start_date'``: start date of the time period corresponding to the
      biller's frequency, or the first date in the sliced timesheet
    - ``'end_date'``: end date of the time period corresponding to the
      biller's frequency, or the last date in the sliced timesheet
    - ``'time_spent'``: time spent resampled at the biller's frequency
      via summing
    - ``'rate'``: cost per hour
    - ``'cost'``: time spent multiplied by rate

    If the biller has bins, then the time spent is decomposed
    by the biller's bins.
    """  
    # Slice
    f = slice_by_dates(timesheet, date1, date2)

    # Resample and add start/end dates
    if biller.freq is not None:
        freq = biller.freq
        f = timesheet.set_index('date')[['time_spent']].resample(freq).sum()
        f = f.reset_index()
        f['period'] = f['date'].map(lambda x: pd.Period(x, freq))
        f['start_date'] = f['period'].map(lambda x: x.start_time)
        f['end_date'] = f['period'].map(lambda x: x.end_time)
    else:
        start_date, end_date = f['date'].min(), f['date'].max()
        f['start_date'] = start_date
        f['end_date'] = end_date

    # Get bins for aggregating
    if biller.base_fee:
        bins = [0] + biller.bins
    else:
        bins = biller.bins

    def my_agg(group):
        d = OrderedDict()
        d['start_date'] = group['start_date'].iat[0]
        d['end_date'] = group['end_date'].iat[0]
        t = group['time_spent'].iat[0]
        d['time_spent'] = pd.Series(decompose(t, bins))
        c1 = d['time_spent'].cumsum().map(biller)
        c2 = c1.shift(1).fillna(0)
        cost = c1 - c2
        d['rate'] = cost/d['time_spent']
        d['cost'] = cost
        return pd.DataFrame(d)
    
    f = f.groupby('date').apply(my_agg
      ).reset_index().drop(['level_1', 'date'], axis=1)

    # Drop NaN rate items
    f = f.dropna(subset=['rate'])

    return f

#---------------------------------------
# Writing
#---------------------------------------
def make_invoice(cost_summary, template_path, context):
    """
    Given a cost summary (output of :func:`compute_cost_summary`),
    the path to an HTML invoice template (string on pathlib.Path object), 
    and a context dictionary to feed to the template,
    inject into the context the keys and values 

    - ``'cost_table'``: a list of each non-header row (list)
      in the cost summary
    - ``'total_cost'``: the sum of the ``'cost'`` column of the 
      cost summary.

    Then render the template with the context, and 
    return the resulting HTML (string) invoice.
    """
    f = cost_summary.copy()

    # Inject extra items into context
    context['cost_table'] = [row.tolist() for __, row in f.iterrows()]
    context['total_cost'] = f['cost'].sum()

    # Render as HTML
    path = Path(template_path).resolve()
    loader = j2.FileSystemLoader(path.parent.as_posix())
    env = j2.Environment(loader=loader)
    template = env.get_template(path.name)
    html = template.render(context)
    return html
