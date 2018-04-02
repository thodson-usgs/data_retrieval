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
    df = test_measurements_service()
    assert df.iloc[0]['measurement_nu'] == 801
