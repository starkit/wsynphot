import pytest

from wsynphot.io import get_filter_data as gfd

def test_get_filter_index():
    table = gfd.get_filter_index()
    # Check if column for Filter ID (named 'filterID') exists in table
    assert 'filterID' in table.to_table().colnames

@pytest.mark.parametrize(('test_filter_id'), 
                        ['HST/NICMOS1.F113N', 'HST/ACS_HRC.F250W'])
def test_get_transmission_data(test_filter_id):
    table = gfd.get_transmission_data(test_filter_id)
    # Check if data is downloaded properly, with > 0 rows
    assert len(table.to_table()) > 0

@pytest.mark.parametrize('test_facility, test_instrument', 
                            [('HST', 'WFPC2'), ('Keck', None)])
def test_get_filter_list(test_facility, test_instrument):
    table = gfd.get_filter_list(test_facility, test_instrument)
    # Check if column for Filter ID (named 'filterID') exists in table
    assert 'filterID' in table.to_table().colnames
