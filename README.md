data_retrieval: Download USGS hydrologic data
=============================================

What is data_retrieval?
-----------------------

data_retrieval is a python alternative to USGS-R's dataRetrieval package for obtaining USGS or EPA water quality data, streamflow data, and metadata directly from web services.

Here's an example of how to use data_retrievel to retrieve data from the National Water Information System (NWIS).

```python
import data_retrieval.nwis as nwis

site = '03339000'

#get instantaneous values (iv)
df = nwis.get_record(site=site, service='iv', start='2017-12-31', end='2018-01-01')

#get water quality samples (qwdata)
df2 = nwis.get_record(site=site, service='qwdata', start='2017-12-31', end='2018-01-01')
```
Services available from NWIS include:
- instantaneous values (iv)
- daily values (dv)
- statistics (stat)
- site info (site)
- discharge peaks (peaks)
- discharge measurements (measurements)

More services and documentation to come!

Quick start
-----------

data_retrieval can be installed using pip:

    $ python3 -m pip install -U data_retrieval

If you want to run the latest version of the code, you can install from git:

    $ python3 -m pip install -U git+git://github.com/USGS-python/data_retrieval.git

Issue tracker
-------------

Please report any bugs and enhancement ideas using the data_retrieval issue
tracker:

  https://github.com/USGS-python/data_retrieval/issues

Feel free to also ask questions on the tracker.


Help wanted
-----------

Any help in testing, development, documentation and other tasks is
highly appreciated and useful to the project. 

For more details, see the file [CONTRIBUTING.md](CONTRIBUTING.md).



[![Coverage Status](https://coveralls.io/repos/github/thodson-usgs/data_retrieval/badge.svg?branch=master)](https://coveralls.io/github/thodson-usgs/data_retrieval?branch=master)
