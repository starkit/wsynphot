import pytest

from ..get_filter_data import svofps

def test_get_filter_index():
    table = svofps.get_filter_index()
    # Check if column for Filter ID (named 'filterID') exists in table
    assert 'filterID' in table.to_table().colnames

@pytest.mark.parametrize(('test_filter_id'), 
                        ['HST/NICMOS1.F113N', 'HST/WFPC2.f218w'])
def test_get_transmission_data(test_filter_id):
    table = svofps.get_transmission_data(test_filter_id)
    # Check if data is downloaded properly, with > 0 rows
    assert len(table.to_table()) > 0