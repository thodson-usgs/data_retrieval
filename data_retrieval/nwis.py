# -*- coding: utf-8 -*-
"""Functions for downloading data from NWIS

Todo:
    * Create a test to check whether functions pull multipe sites
    * Work on multi-index capabilities.
    * Check that all timezones are handled properly for each service.
"""

import pandas as pd
import requests
from io import StringIO
import numpy as np
import re

from data_retrieval.codes import tz
from data_retrieval.utils import to_str

WATERDATA_URL = 'https://nwis.waterdata.usgs.gov/nwis/'
WATERSERVICE_URL = 'https://waterservices.usgs.gov/nwis/'

WATERSERVICES_SERVICES = ['dv','iv','site','stat','gwlevels']
WATERDATA_SERVICES = ['qwdata','measurements','peak', 'pmcodes'] # add more services


def format_response(df, service=None):
    """Setup index for response from query.
    """
    if df is None:
        return

    if service=='qwdata':
        df = preformat_qwdata_response(df)

    #check for multiple sites:
    if 'datetime' not in df.columns:
        #XXX: consider making site_no index
        return df

    elif len(df['site_no'].unique()) > 1:
        #setup multi-index
        df.set_index(['site_no','datetime'], inplace=True)

    else:
        df.set_index(['datetime'], inplace=True)

    return df.sort_index()


def preformat_qwdata_response(df):
    #create a datetime index from the columns in qwdata response
    df['sample_start_time_datum_cd'] = df['sample_start_time_datum_cd'].map(tz)

    df['datetime'] = pd.to_datetime(df.pop('sample_dt') + ' ' +
                                    df.pop('sample_tm') + ' ' +
                                    df.pop('sample_start_time_datum_cd'),
                                    format = '%Y-%m-%d %H:%M')

    return format_response(df)


def get_qwdata(**kwargs):
    """Get water sample data from qwdata service.
    """
    #check number of sites, may need to create multiindex

    payload = {'agency_cd':'USGS', 'format':'rdb',
               'pm_cd_compare':'Greater than', 'inventory_output':'0',
               'rdb_inventory_output':'file', 'TZoutput':'0',
               'radio_parm_cds':'all_parm_cds', 'rdb_qw_attributes':'expanded',
               'date_format':'YYYY-MM-DD', 'rdb_compression':'value',
               'submmitted_form':'brief_list', 'qw_sample_wide':'separated_wide'}

    kwargs = {**payload, **kwargs}

    query = query_waterdata('qwdata',**kwargs)

    df = read_rdb(query)

    return format_response(df, service='qwdata')


def get_discharge_measurements(**kwargs):
    """ **DEPCRECATED**
    Args:
        sites (listlike):
    """
    query = query_waterdata('measurements', format='rdb', **kwargs)
    df = read_rdb(query)

    return format_response(df)


def get_peaks(**kwargs):
    """ **DEPRECATED** Implement through waterservices

    Args:
        site_no (listlike):
        state_cd (listline):

    """
    query = query_waterdata('measurements', format='rdb', **kwargs)

    df = read_rdb(query)

    return format_response(df)


def get_stats(**kwargs):
    """Querys waterservices statistics information

    Must specify
    Args:
        sites (string or list): USGS site number
        statReportType (string): daily (default), monthly, or annual
        statTypeCd (string): all, mean, max, min, median

    Returns:
        Dataframe

    TODO: fix date parsing
    """
    if sites not in kwargs:
        raise TypeError('Query must specify a site or list of sites')

    query = waterservices_query('stat', **kwargs)

    return read_rdb(query)


def query(url, **kwargs):
    """Send a query.

    Wrapper for requests.get that handles errors, converts listed
    query paramaters to comma separated strings, and returns response.

    Args:
        url:
        kwargs: query parameters passed to requests.get

    Returns:
        string : query response
    """

    payload = {}

    for key, value in kwargs.items():
        value = to_str(value)
        payload[key] = value

    try:

        req = requests.get(url, params=payload)

    except ConnectionError:

        print('could not connect to {}'.format(req.url))

    response_format = kwargs.get('format')

    if response_format == 'json':
        return req.json()

    else:
        return req.text


def query_waterdata(service, **kwargs):
    """Querys waterdata.
    """
    major_params = ['site_no','state_cd']
    bbox_params = ['nw_longitude_va', 'nw_latitude_va',
                   'se_longitude_va','se_latitude_va']


    if not any(key in kwargs for key in major_params + bbox_params):
        raise TypeError('Query must specify a major filter: site_no, stateCd, bBox')

    elif any(key in kwargs for key in bbox_params) \
    and not all(keys in kwargs for key in bbox_params):
        raise TypeError('One or more lat/long coordinates missing or invalid.')

    if service not in WATERDATA_SERVICES:
        raise TypeError('Service not recognized')


    url = WATERDATA_URL + service

    return query(url, **kwargs)


def query_waterservices(service, **kwargs):
    """Querys waterservices.usgs.gov

    For more documentation see

    Args:
        service (string): 'site','stats',etc
        bBox:
        huc (string): 7-digit Hydrologic Unit Code

        startDT (string): start date (2017-12-31)
        endDT (string): end date
        modifiedSince (string): for example

    Returns:
        request

    Usage: must specify one major filter: sites, stateCd, bBox,
    """
    if not any(key in kwargs for key in ['sites','stateCd','bBox']):
        raise TypeError('Query must specify a major filter: site_no, stateCd, bBox')

    if service not in WATERSERVICES_SERVICES:
        raise TypeError('Service not recognized')

    url = WATERSERVICE_URL + service

    return query(url, **kwargs)


def get_dv(**kwargs):

    query = query_waterservices('dv', format='json', **kwargs)
    df = read_json(query)

    return format_response(df)


def get_info(**kwargs):
    """
    Get site description information from NWIS

    Parameters:
        See waterservices_query

    Note: Must specify one major filter: site_no, stateCd, bBox
    """

    query = query_waterservices('site', **kwargs)

    return read_rdb(query)


def get_iv(**kwargs):

    query = query_waterservices('iv', format='json', **kwargs)
    df = read_json(query)

    return format_response(df)


def get_pmcodes(**kwargs):
    """Return a DataFrame containing all NWIS parameter codes.

    Returns:
        DataFrame containgin the USGS parameter codes
    """
    payload = {'radio_pm_search':'param_group',
               'pm_group':'All+--+include+all+parameter+groups',
               'pm_sarch':None,
               'casrn_search':None,
               'srsname_search':None,
               'show':'parameter_group_nm',
               'show':'casrn',
               'show':'srsname',
               'show':'parameter_units',
               'format':'rdb',
              }

    kwargs = {**payload, **kwargs}

    #FIXME check that the url is correct
    url = WATERSERVICE_URL + 'pmcodes'
    df = read_rdb( query(url, **kwargs) )

    return format_response(df)


def get_record(sites, start=None, end=None, state=None, service='iv', *args, **kwargs):
    """
    Get data from NWIS and return it as a DataFrame.

    Args:
        sites (listlike): List or comma delimited string of site.
        start (string): Starting date of record (YYYY-MM-DD)
        end (string): Ending date of record.
        service (string):
            - 'iv' : instantaneous data
            - 'dv' : daily mean data
            - 'qwdata' : discrete samples
            - 'site' : site description
            - 'measurements' : discharge measurements
    Return:
        DataFrame containing requested data.
    """
    if service not in WATERSERVICES_SERVICES + WATERDATA_SERVICES:
        raise TypeError('Unrecognized service: {}'.format(service))

    if service == 'iv':
        record_df = get_iv(sites=sites, startDT=start, endDT=end, **kwargs)

    elif service == 'dv':
        record_df = get_dv(sites=sites, startDT=start, endDT=end, **kwargs)

    elif service == 'qwdata':
        record_df = get_qwdata(site_no=sites, begin_date=start, start_date=end)

    elif service == 'site':
        record_df = get_info(site_no=sites)
        #record_df = get_site_desc(sites)

    elif service == 'measurements':
        record_df = get_discharge_measurements(site_no=sites, begin_date=start,
                                               end_date=end, **kwargs)

    elif service == 'peaks':
        record_df = get_discharge_peaks(site_no=sites, begin_date=start,
                                        end_date=end, **kwargs)

    return record_df


def read_json(json, multi_index=False):
    """Reads a NWIS Water Services formated JSON into a dataframe

    Args:
        json (dict)

    Returns:
        DataFrame containing times series data from the NWIS json.
    """
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
            #should be able to avoid this by dumping
            record_json = str(record_json).replace("'",'"')

            # read json, converting all values to float64 and all qaulifiers
            # to str. Lists can't be hashed, thus we cannot df.merge on a list column
            record_df   = pd.read_json(record_json, orient='records',
                                       dtype={'value':'float64',
                                              'qualifiers':'unicode'})

            record_df['qualifiers'] = record_df['qualifiers'].str.strip("[]").str.replace("'","")
            record_df['site_no'] = site_no

            record_df.rename(columns={'value':col_name,
                                      'dateTime':'datetime',
                                      'qualifiers':col_name + '_cd'}, inplace=True)

            try:
                merged_df = merged_df.merge(record_df, on=['site_no','datetime'],how='outer')

            except MemoryError:
                #merged_df wasn't created
                merged_df = record_df

            except NameError:
                merged_df = record_df

    return format_response(merged_df)


def read_rdb(rdb):
    """Convert NWIS rdb table into a dataframe.

    Args:
        rdb (string):
    """
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

    return format_response(df)
