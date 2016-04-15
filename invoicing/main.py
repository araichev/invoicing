"""
Main module.

A *timesheet* is a Pandas data frame with at least the columns...
"""
import pandas as pd 
import numpy as np 
from jinja2 import Environment, PackageLoader


# Load Jinja templates
ENV = Environment(loader=PackageLoader('main', 'templates'))

# I/O
def read_timesheet(path):
    """
    Read a timesheet located at the given path and return the corresponding
    data frame.
    """
    parser = lambda date: pd.datetime.strptime(date, '%Y%m%d')
    f = pd.read_csv(path, parse_dates=['date'], date_parser=parser)
    f = f.sort_values('date')
    return f

def validate_timesheet(timesheet):
    pass

# Billing
def bill_at_constant_rate(timesheet, project_rates_df):
    """
    Append a ``cost`` column to the given timesheet data frame and return 
    the resulting data frame.

    Billing business logic goes here.
    """
    f = timesheet.copy()
    g = f.merge(project_rates_df)
    g['cost'] = (g['time_spent']/60)*g['hourly_rate']
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
      'sender': 'Alex',
      'invoice_code': 'bingo',
      'issue_date': '2016-04-16',
      'due_date': '2016-04-17',
      }
    html = template.render(context)
    return html