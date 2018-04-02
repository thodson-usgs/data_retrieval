import pandas as pd
import requests
from io import StringIO
import numpy as np
import re

from data_retrieval.timezones import tz
#from hygnd.munge import update_merge

NWIS_URL = 'https://waterservices.usgs.gov/nwis/iv/'
QWDATA_URL =  'https://nwis.waterdata.usgs.gov/nwis/qwdata?'

def rdb_to_df(url, params=None):
    """ Convert NWIS rdb table into a dataframe.

    Args:
          url (string):  Base yrk
          params: Parameters for REST request

    See https://waterdata.usgs.gov/nwis?automated_retrieval_info
    """
    try:

        req = requests.get(url, params=params)

    except ConnectionError:

        print('could not connect to {}'.format(req.url))

    rdb = req.text
    #return rdb
    if rdb.startswith('No sites/data'):
        return None
    #return None

    count = 0

    for line in rdb.splitlines():
        # ignore comment lines
        if line.startswith('#'):
            count = count + 1

        else:
            break

    fields = rdb.splitlines()[count].split('\t')
    dtypes = {'site_no': str}
    #dtypes =  {‘site_no’: str, }
    df = pd.read_csv(StringIO(rdb), delimiter='\t', skiprows=count+2, names=fields,
                     na_values='NaN', dtype=dtypes)

    return df


#TODO: move this to core module.
def to_str(listlike):
    """Translates list-like objects into strings.

    Return:
        List-like object as string
    """
    if type(listlike) == list:
        return ','.join(listlike)

    elif type(listlike) == pd.core.series.Series:
        return ','.join(listlike.tolist())

    elif type(listlike) == str:
        return listlike


#need to acount for time zones
def get_samples(sites=None, state_cd=None,
                  start=None, end=None, multi_index=False, *args):
    """Pull water quality sample data from NWIS and return as dataframe.

    Args:
      site (string): X digit USGS site ID. USGS-05586300/
      start: 2018-01-25
      end:
    """
    #payload = {'sites':siteid, 'startDateLo':start, 'startDateHi':end,
    #       'mimeType':'csv'}


    payload = {'agency_cd':'USGS', 'format':'rdb',
               'pm_cd_compare':'Greater than', 'inventory_output':'0',
               'rdb_inventory_output':'file', 'TZoutput':'0',
               'radio_parm_cds':'all_parm_cds', 'rdb_qw_attributes':'expanded',
               'date_format':'YYYY-MM-DD', 'rdb_compression':'value',
               'submmitted_form':'brief_list', 'qw_sample_wide':'separated_wide'}
    #payload = {'format':'rdb','date_format':'YYYY-MM-DD'}

    # check for sites and state_cd, and if list-like, convert them to strings/freq

    if sites:
        payload['site_no'] = to_str(sites)

    elif state_cd:
        payload['state_cd'] = to_str(state_cd)

    else:
        raise ValueError('Site or state must be defined')

    if start: payload['begin_date'] = start

    if end: payload['end_date'] = end

    df = rdb_to_df(QWDATA_URL, payload)

    if type(df) == type(None):
        return None

    df['sample_start_time_datum_cd'] = df['sample_start_time_datum_cd'].map(tz)

    df['datetime'] = pd.to_datetime(df.pop('sample_dt') + ' ' +
                                    df.pop('sample_tm') + ' ' + df.pop('sample_start_time_datum_cd'),
                                    format = '%Y-%m-%d %H:%M')
    if multi_index == True:
        df.set_index(['site_no','datetime'], inplace=True)
    else:
        df.set_index('datetime', inplace=True)
    #df.set_index(['site_no','datetime'], inplace=True)

    return df


def get_site_desc(sites):
    """
    Get site description information from NWIS
    """

    url = 'https://waterservices.usgs.gov/nwis/site/?'

    sites = to_str(sites)
    payload = {'sites':sites, 'format':'rdb'}

    df = rdb_to_df(url, payload)
    #df.set_index(['site_no'], inplace=True)
    return df


def get_all_param_cds():
    """Return a DataFrame containing all NWIS parameter codes."""

    url = 'https://nwis.waterdata.usgs.gov/nwis/pmcodes?radio_pm_search=param_group&pm_group=All+--+include+all+parameter+groups&pm_search=&casrn_search=&srsname_search=&format=rdb&show=parameter_group_nm&show=parameter_nm&show=casrn&show=srsname&show=parameter_units'

    df = rdb_to_df(url)
    #df.set_index(['parameter_cd'], inplace=True)

    return df


def get_records(sites, start=None, end=None, service='iv', *args):
    """
    Args:

    Return:
    """
    if service == 'iv' or service =='dv':
        json = get_json_record(sites, start, end, service=service, *args)
        record_df = parse_gage_json(json)

    #if service == 'dv'

    elif service == 'qwdata':
        record_df = get_samples(sites, start=start, end=end)

    elif service == 'site':
        record_df = get_site_desc(sites)

    else:
        print('A record for site {} was not found in service {}'.format(site,service))
        return

    return record_df


def get_json_record(sites, start=None, end=None, params=None, service='iv', *args, **kwargs):
    """Request

    Args:
        site (string): USGS site number, e.g., 05586300.
        start (string): 2018-01-25
        end:
        kwargs: any additional parameter codes, namely 'parameterCD'

    Returns:
        Return an object containing the gage record


    See https://waterdata.usgs.gov/nwis?automated_retrieval_info

    """

    url = 'https://waterservices.usgs.gov/nwis/iv/'

    # if daily values were requested
    if service=='dv':
        url = re.sub('iv/$','dv/$', url)

    sites = to_str(sites)

    payload = {'sites':sites, 'startDT':start, 'endDT':end,
               'format':'json'} #, 'parameterCD':''}

    if start:
        payload['startDT'] = start
    if end:
        payload['endDT'] = end

    if params:
        payload['parameterCD'] = to_str(params)

    #for arg in kwargs:
    #    payload[arg]=to_str(kwargs[arg])


    req = requests.get(url, params=payload)
    req.raise_for_status()
    #print(req.url)
    return req.json()


def parse_gage_json(json, multi_index=False):
    """Parses an NWIS formated json into a pandas DataFrame

    Args:
        json (dict)

    Returns:
        DataFrame containing times series data from the NWIS json.
    """
    #FIXME need to check number of sites. If multiple sites, set multi_index
    # loop through each timeseries in the json
    for timeseries in json['value']['timeSeries']:

        site_no = timeseries['sourceInfo']['siteCode'][0]['value']
        param_cd = timeseries['variable']['variableCode'][0]['value']

        # loop through each parameter in timeseries.
        for parameter in timeseries['values']:
            col_name = param_cd
            method =  parameter['method'][0]['methodDescription']

            #if len(timeseries['values']) > 1 and method:
            if method:
                # get method, format it, and append to column name
                method = method.strip("[]()").lower()
                col_name = '{}_{}'.format(col_name, method)

            col_cd_name = col_name + '_cd'
            record_json = parameter['value']

            if not record_json:
                #no data in record
                continue

            record_json = str(record_json).replace("'",'"')

            # read json, converting all values to float64 and all qaulifiers
            # to str. Lists can't be hashed, thus we cannot df.merge on a list column
            record_df   = pd.read_json(record_json, orient='records',
                                       dtype={'value':'float64',
                                              'qualifiers':'unicode'})

            record_df['qualifiers'] = record_df['qualifiers'].str.strip("[]'")

            record_df.rename(columns={'value':col_name,
                                      'dateTime':'datetime',
                                      'qualifiers':col_name + '_cd'}, inplace=True)

            # move to end and if multiple sites were returned, force to mutli-index
            if multi_index:
                record_df['site_no'] = site_no
                record_df.set_index(['site_no','datetime'], inplace=True)

            else:
                record_df.set_index(['datetime'], inplace=True)

            #record_df.rename(columns={'value':(col_name,'val'),'qualifiers':(col_name,'cd') }, inplace=True)

            #return record_df
            try:
                #should be able to replace with outer join
                merged_df.merge(record_df, how='outer')
                #merged_df = update_merge(merged_df, record_df)
            except MemoryError:
                #merged_df wasn't created
                merged_df = record_df

            except NameError:
                merged_df = record_df

    return merged_df


def sample_gage_record():
    """Gets a sample gage record for testing purposes."""

    return get_records('05586300','2016-10-1','2017-9-30')
