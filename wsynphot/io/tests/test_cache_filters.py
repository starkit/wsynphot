import pytest
import os

import wsynphot
from wsynphot.io import cache_filters as cf

DATA_PATH = os.path.join(wsynphot.__path__[0], 'io', 'tests', 'data')
CACHE_DIR = os.path.join(DATA_PATH, 'cached_SVO_FPS')

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
