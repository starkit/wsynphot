import pytest
import os
import pandas.testing as pdt

import wsynphot
from wsynphot.io import cache_filters as cf

DATA_PATH = os.path.join(wsynphot.__path__[0], 'io', 'tests', 'data')
CACHE_DIR = os.path.join(DATA_PATH, 'cached_SVO_FPS')

@pytest.fixture
def sample_table():
    from astropy.table import Table
    table = Table()
    table['a'] = [1.56, 2.34, 3.78, 4.71]
    table['b'] = [0.1, 0.2, 0.4, 0.5]
    return table

def test_cache_as_votable(sample_table):
    sample_votable_path = os.path.join(DATA_PATH, 'sample_table.vot')
    cf.cache_as_votable(sample_table, sample_votable_path)
    # Convert back cached votable to a dataframe "data" and compare it 
    data = cf.df_from_votable(sample_votable_path, 
        "Caching of sample_table failed!")
    pdt.assert_frame_equal(sample_table.to_pandas(), data)

def test_load_filter_index():
    data = cf.load_filter_index(CACHE_DIR)
    assert data.empty == False
    assert 'filterID' in data.columns

@pytest.mark.parametrize(('test_filter_id'), 
                        ['HST/NICMOS1.F113N', 'HST/WFPC2.f218w'])
def test_load_transmission_data(test_filter_id):
    data = cf.load_transmission_data(test_filter_id, CACHE_DIR)
    assert data.empty == False
    assert (data['Wavelength'] > 0).all() == True
    assert ((data['Transmission'] >= 0) &
        (data['Transmission'] <= 1)).all() == True
