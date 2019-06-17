from server import app
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import sqltypes
from flask import abort
import datetime, os

#fixa till saabs nätverk istället
if 'NAMESPACE' in os.environ and os.environ['NAMESPACE'] == 'heroku':
    db_uri = os.environ['DATABASE_URL']
    debug_flag = False
else: # when running locally with sqlite
    db_path = os.path.join(os.path.dirname(__file__), 'dextool_mutate.sqlite3')
    db_uri = 'sqlite:///{}'.format(db_path)
    debug_flag = True

app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
db.Model.metadata.reflect(db.engine)

class AllTestCase(db.Model):
    __table__ = db.Model.metadata.tables['all_test_case']

    def to_list(self):
        list = [self.id, self.name]
        return list


def get_data(maxDataPoints, targets, adhocFilters):
    """Takes an int denoting max number of data points (maxDataPoints),
    a json containing target data (targets), and
    a json containg filters (adhocfilters) and
    returns the corresponding data from the database"""

    data = []
    for target in targets:
        if target['type'] == 'table':
            data.append(get_table_data(maxDataPoints, target, adhocFilters))
        elif target['type'] == 'timeseries':
            data.append(get_time_series_data(maxDataPoints, target, adhocFilters))
    print(data)
    return data

def get_table_data(maxDataPoints, target, adhocFilters):
    """Help-function for get_data. Returns data in table-format"""
    model = determineModel(target['target'])
    column_dicts = []
    for field in model.columns:
        column_dicts.append({'text': field.name,
                             'type': type_interpreter(field.type)})

    value_lists = query_DB(target, adhocFilters, maxDataPoints)
    return {
            "columns": column_dicts,
            "rows": value_lists,
            "type":"table"
           }


def get_time_series_data(maxDataPoints, targets, adhocFilters):
    """Help-function for get_data. Returns data in timeseries-format"""
    pass

def determineModel(target):
    """Identifies the table-model requested and returns a list of its fields and
    which data-types they contain."""

    model = db.Model.metadata.tables[target]
    return model

def type_interpreter(type):
    """Takes a SQL datatype and returns the appropriate type to use in Grafana"""

    if isinstance(type, sqltypes.INTEGER):
        return 'number'
    elif isinstance(type, sqltypes.TEXT):
        return 'string'
    elif isinstance(type, sqltypes.DATETIME):
        return 'time'
    else:
        return ""

#Bad solution, should bw rewritten to increase modularity
def query_DB(target, adhocFilters, maxDataPoints):
    """Takes a string (target) denoting which model to query, a json with
    filters to filter the query by (adhocFilters) and a int denoting
    the max number of data points. Returns the result of the query"""

    if target == all_test_case:
        AllTestCase.query.filter_by()

def get_metrics():
    tables = db.Model.metadata.tables
    tablelist = []
    for key in tables:
        tablelist.append(key)
    return tablelist
