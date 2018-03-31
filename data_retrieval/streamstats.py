"""
This module is a wrapper for the streamstats API, documentation for which is at
https://streamstats.usgs.gov/streamstatsservices/#/
"""

import json
import requests

def download_workspace(filepath, workspaceID, format=''):
    """
    
    Args:
        workspaceID (string): Service workspace received form watershed result
        format (string): Download return format. Default will return ESRI
                         geodatabase zipfile. 'SHAPE' will return a zip file containing
                         shape format.
                         
    Returns:
        A zip file containing the workspace contents, in either a geodatabase or shape
        files.
    """
    payload = {'workspaceID':workspaceID, 'format':format}
    url = 'https://streamstats.usgs.gov/streamstatsservices/download'
    
    r = requests.get(url, params=payload)
    
    r.raise_for_status()
    return r
    #data = r.raw.read()
    
    #with open(filepath, 'wb') as f:
    #    f.write(data)
    
    #return

     
def get_watershed(rcode, xlocation, ylocation, crs=4326, 
                  includeparameters=True, includeflowtypes=False, 
                  includefeatures=True, simplify=True):
    """ Get watershed object based on location
    
    Args:
        rcode: StreamStats 2-3 character code that identifies the Study Area -- either a   
               State or a Regional Study.
        xlocation: X location of the most downstream point of desired study area.
        ylocation: Y location of the most downstream point of desired study area.
        crs: ESPSG spatial reference code.
        includeparameters:
        includeflowtypes: Not yet implemented.
        includefeatures: Comma seperated list of features to include in response.
        simplify:
        
    Returns:
        Json watershed object or maybe a watershed object
    
    see: https://streamstats.usgs.gov/streamstatsservices/#/
    """
    
    payload = {'rcode':rcode, 'xlocation':xlocation, 'ylocation':ylocation, 'crs':crs, 
               'includeparameters':includeparameters, 'includeflowtypes':includeflowtypes, 
               'includefeatures':includefeatures, 'simplify':simplify}
    url = 'https://streamstats.usgs.gov/streamstatsservices/watershed.geojson'
    
    r   = requests.get(url, params=payload)

    r.raise_for_status()
    
    data = r.json() #raise error
    return data