import mut_googletest.json

def get_data(maxDataPoints, targets):
    """Takes an int denoting max number of data points (maxDataPoints) and
    a json containing target data (targets), and
    returns the corresponding data from the json file"""

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

    pass

def get_time_series_data(maxDataPoints, target):
    """Returns requested data in timeseries-format
    Called by get_data"""

    pass

def get_metrics():
    pass
