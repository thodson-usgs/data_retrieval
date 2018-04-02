import pytest
from data_retrieval.nwis import get_records

def test_measurements_service():
    """Test measurement service
    """
    start = '2018-01-24'
    end   = '2018-01-25'
    service = 'measurements'
    site = '03339000'
    df = get_records(site, start, end, service=service)
    return df

def test_measurements_service_answer():
<<<<<<< HEAD
    df = test_measurements_service()
    assert df.iloc[0]['tz_cd'] == 'CST'
=======
    assert df['measurement_nu'] == 801
>>>>>>> ef69678983dc95516a3a4aa227b4b1ef12ada314
