from server import app
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import sqltypes
from sqlalchemy import event, Table
from flask import abort
from datetime import datetime
import os


if 'NAMESPACE' in os.environ and os.environ['NAMESPACE'] == '':
    db_uri = ""
    debug_flag = False
else: # when running locally with sqlite
    db_path = os.path.join(os.path.dirname(__file__), 'dextool_mutate.sqlite3')
    db_uri = 'sqlite:///{}'.format(db_path)
    debug_flag = True

app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

@event.listens_for(Table, "column_reflect")
def remove_datetime(inspector, table, column_info):
    """When a column is reflected and has type datetime the type is
    changed to text. This is due to sqlite saving the datetime string and
    sqlalchemy trying to parse it as a datetime object"""
    if isinstance(column_info['type'], db.DateTime):
        column_info['type'] = db.TEXT

db.Model.metadata.reflect(db.engine)

class AllTestCase(db.Model):
    """Allows the handler to acces the all_test_case table in the db"""
    __table__ = db.Model.metadata.tables['all_test_case']

    def to_list(self):
        return [self.name]

class Files(db.Model):
    """Allows the handler to acces the files table in the db"""
    __table__ = db.Model.metadata.tables['files']

    def to_list(self):
        return [self.path, self.checksum0, self.checksum1, self.lang]

    def to_dict(self):
        return {'checksum0': self.checksum0, 'checksum1': self.checksum1,
                'lang': self.lang}

class KilledTestCase(db.Model):
    """Allows the handler to acces the killed_test_case table in the db"""
    __table__ = db.Model.metadata.tables['killed_test_case']

    def to_list(self):
        return [self.st_id, self.tc_id, self.location]

    def to_dict(self):
        return {'st_id': self.st_id, 'tc_id': self.tc_id}

class Mutation(db.Model):
    """Allows the handler to acces the mutation table in the db"""
    __table__ = db.Model.metadata.tables['mutation']

    def to_list(self):
        return [self.mp_id, self.st_id, self.kind]

    def to_dict(self):
        return {'mp_id': self.mp_id, 'st_id': self.st_id, 'kind': self.kind}

class MutationPoint(db.Model):
    """Allows the handler to acces the mutation_point table in the db"""
    __table__ = db.Model.metadata.tables['mutation_point']

    def to_list(self):
        return [self.file_id, self.offset_begin, self.offset_end,
                self.line, self.column, self.line_end, self.column_end]

    def to_dict(self):
        return {'file_id': self.file_id, 'offset_begin': self.offset_begin,
                'offset_end': self.offset_end, 'line': self.line,
                'column': self.column, 'line_end': self.line_end,
                'column_end': self.column_end}

class MutationStatus(db.Model):
    """Allows the handler to acces the mutation_status table in the db"""
    __table__ = db.Model.metadata.tables['mutation_status']

    def to_list(self):
        return [self.status, self.time, self.test_cnt,
                datetime.strptime(self.update_ts, '%Y-%m-%dT%H:%M:%S.%f'),
                datetime.strptime(self.added_ts, '%Y-%m-%dT%H:%M:%S.%f'),
                self.checksum0, self.checksum1]

    def to_dict(self):
        return {'status': self.status, 'time': self.time,
                'test_cnt': self.test_cnt,
                'update_ts': datetime. \
                    strptime(self.update_ts, '%Y-%m-%dT%H:%M:%S.%f').timestamp()*1000,
                'added_ts': datetime. \
                    strptime(self.added_ts, '%Y-%m-%dT%H:%M:%S.%f').timestamp()*1000,
                'checksum0': self.checksum0, 'checksum1': self.checksum1}


#Empty in the googletest database, unsure if relevant
class RawSrcMetadata(db.Model):
    """Allows the handler to acces the raw_src_metadata table in the db"""
    __table__ = db.Model.metadata.tables['raw_src_metadata']

    def to_list(self):
        return [self.file_id, self.line, self.nomut, self.tag,
                self.comment]

    def to_dict(self):
        return {'file_id': self.file_id, 'line': self.line, 'nomut': self.nomut,
                'tag': self.tag, 'comment': self.comment}


def get_data(maxDataPoints, targets):
    """Takes an int denoting max number of data points (maxDataPoints) and
    a json containing target data (targets), and
    returns the corresponding data from the database"""

    data = []
    for target in targets:
        if target['type'] == 'table':
            data.append(get_table_data(maxDataPoints, target))
        elif target['type'] == 'timeseries':
            data.append(get_time_series_data(maxDataPoints, target))
    return data

def get_table_data(maxDataPoints, target):
    """Returns requested data in table-format
    Called by get_data"""

    model = determineModel(target['target'])

    column_dicts = []
    for field in model.columns:
        if field.name != "id":
            column_dicts.append({'text': field.name,
                                 'type': type_interpreter(field.type)})

    query_result = query_DB(target, maxDataPoints)

    value_lists = []
    for temp in query_result:
        value_lists.append(temp.to_list())

    return {
            "columns": column_dicts,
            "rows": value_lists,
            "type":"table"
           }


def get_time_series_data(maxDataPoints, target):
    """Returns requested data in timeseries-format
    Called by get_data"""

    query_result = query_DB(target, maxDataPoints)

    value_lists = []
    for temp in query_result:
        dict = temp.to_dict()
        value_lists.append([dict[target['data']['y']], dict[target['data']['x']]])

    return {
            'target': target['target'],
            'datapoints': value_lists
           }

def determineModel(target):
    """Identifies the table-model requested and returns a list of its fields."""

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


def query_DB(target, maxDataPoints):
    """Takes a string (target) denoting which model to query and an int denoting
    the max number of data points. Returns the result of the query"""

    if target['data'] != None and 'maxDataPoints' in target['data'] and \
            target['data']['maxDataPoints'] <= 607:
        maxDataPoints = target['data']['maxDataPoints']

    if target['data'] != None and 'firstDataPoint' in target['data']:
        firstDataPoint = target['data']['firstDataPoint']
    else:
        firstDataPoint = 0


    if target['target'] == 'all_test_case':
        query_result = AllTestCase.query.filter(AllTestCase.id>=firstDataPoint). \
            limit(maxDataPoints).all()
    elif target['target'] == 'files':
        query_result = Files.query.filter(Files.id>=firstDataPoint). \
            limit(maxDataPoints).all()
    elif target['target'] == 'killed_test_case':
        query_result = KilledTestCase.query.filter(KilledTestCase.id>=firstDataPoint). \
            limit(maxDataPoints).all()
    elif target['target'] == 'mutation':
        query_result = Mutation.query.filter(Mutation.id>=firstDataPoint). \
            limit(maxDataPoints).all()
    elif target['target'] == 'mutation_point':
        query_result = MutationPoint.query.filter(MutationPoint.id>=firstDataPoint). \
            limit(maxDataPoints).all()
    elif target['target'] == 'mutation_status':
        query_result = MutationStatus.query.filter(MutationStatus.id>=firstDataPoint). \
            limit(maxDataPoints).all()
    elif target['target'] == 'raw_src_metadata':
        query_result = RawSrcMetadata.query.filter(RawSrcMetadata.id>=firstDataPoint). \
            limit(maxDataPoints).all()
    #Add additional tables here
    else:
        query_result = []

    return query_result


def get_metrics():
    """Returns the name of all table models in the database"""
    tables = db.Model.metadata.tables
    tablelist = []
    for key in tables:
        if key != 'schema_version':
            tablelist.append(key)
    return tablelist
