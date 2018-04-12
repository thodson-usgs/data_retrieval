"""
Library for request water quality sample data from NWIS


url with all paramater codes:
https://nwis.waterdata.usgs.gov/nwis/pmcodes?radio_pm_search=param_group&pm_group=Physical&pm_search=&casrn_search=&srsname_search=&format=rdb_file&show=parameter_group_nm&show=parameter_nm&show=casrn&show=srsname&show=parameter_units

"""

import pandas as pd
import requests
from io import StringIO


def get_samples(site, usgs=True):
    """Get samples from waterqualitydata.us

    """
    if usgs:
        site = 'USGS-' + site

    url = 'https://waterqualitydata.us/Result/search'
    payload = {'siteid':site, 'mimeType':'csv', 
            'sorted':'no'}

    req = requests.get(url, params=payload)

    #if not req:
        #sleep
        #request again
    #return req.url
    df = pd.read_csv(StringIO(req.text),delimiter=',')

    df['datetime'] = pd.to_datetime(df.pop('ActivityStartDate') + ' ' +
                                    df.pop('ActivityStartTime/Time'),
                                    format = '%Y-%m-%d %H:%M:%S')
    temp = df.pop('MonitoringLocationIdentifier')

    df['site_no'] = temp.str.replace('USGS-','')

    df.set_index(['site_no','datetime'], inplace=True)
    #df.set_index(['site_no','datetime'], inplace=True)
    return df
