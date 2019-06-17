from server import app
from flask_sqlalchemy import SQLAlchemy
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

class All(db.Model):
    __table__ = db.Model.metadata.tables['all_test_case']

    def to_list(self):
        list = [self.id, self.name]
        return list


def get_data(range, interval, maxDataPoints, targets, adhocFilters):
    """Takes a json with 'to' and 'from' keys containging unixtimestamps (range),
    an int denoting the time between data points in milliseconds (interval),
    an int denoting max number of data points (maxDataPoints),
    a json containing target data (targets), and
    a json containg filters (adhocfilters) and
    returns the corresponding data from the database"""
    test = All.query.first()
    testList = test.to_list()
    return [{'columns': [{"text": 'Id', 'type': 'number'},
                        {'text': 'Name', 'type': 'string'}],
            'rows': [testList],
            'type': 'table'}]

def get_metrics():
    tables = db.Model.metadata.tables
    tablelist = []
    for key in tables:
        tablelist.append(key)
    return tablelist

def init_db():
    """Initializes the database"""
    db.drop_all()
    db.create_all()
    meta = db.metadata
    for table in reversed(meta.sorted_tables):
        db.session.execute(table.delete())
