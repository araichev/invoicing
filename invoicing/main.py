"""
Main module.

A *timesheet* is a Pandas data frame with at least the columns...
"""
import pandas as pd 
import numpy as np 

# I/O
def read_timesheet(path):
    """
    Read a timesheet located at the given path and return the corresponding
    data frame.
    """
    parser = lambda date: pd.datetime.strptime(date, '%Y%m%d')
    f = pd.read_csv(path, parse_dates=['date'], date_parser=parser)
    f = f.sort_values('date')
    f['is_billable'] = f['is_billable'].fillna(1).astype(int)
    return f

# Billing
def append_cost(timesheet):
    """
    Append a ``cost`` column to the given timesheet data frame and return 
    the resulting data frame.

    Billing business logic goes here.
    """
    f = timesheet.copy()
    hourly_rate = 100
    cost_fn = lambda t: (t/60)*hourly_rate
    f['cost'] = f['is_billable']*f['time_spent'].map(cost_fn)
    return f

# Aggregating
def agg_by_project(timesheet):
    f = timesheet.copy()
    return f.groupby('project').agg(np.sum).drop(['is_billable'], axis=1)
