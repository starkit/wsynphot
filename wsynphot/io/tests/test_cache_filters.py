import pytest
import os, re
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
    data = cf.df_from_votable(sample_votable_path)
    pdt.assert_frame_equal(sample_table.to_pandas(), data)

@pytest.mark.parametrize(('test_filter_id'), 
                        ['Keck/NIRC2.Kp', 'Keck/LWS/SiC'])
def test_download_transmission_data(test_filter_id):
    cf.download_transmission_data(test_filter_id, CACHE_DIR)
    facility, instrument, filter_name = re.split('/|\.', test_filter_id)
    # Check whether filter votable get stored in appropriate directory
    assert os.path.exists(os.path.join(CACHE_DIR, facility, instrument,
        '{0}.vot'.format(filter_name)))

def test_load_filter_index():
    data = cf.load_filter_index(CACHE_DIR)
    assert data.empty == False
    assert 'filterID' in data.columns

def test_IOError_in_load_filter_index():
    # When no filter index found in passed cache directory
    pytest.raises(IOError, cf.load_filter_index, DATA_PATH)

@pytest.mark.parametrize(('test_filter_id'), 
                        ['HST/NICMOS1.F113N', 'HST/ACS_HRC.F250W'])
def test_load_transmission_data(test_filter_id):
    data = cf.load_transmission_data(test_filter_id, CACHE_DIR)
    assert data.empty == False
    assert (data['Wavelength'] > 0).all() == True
    assert ((data['Transmission'] >= 0) &
        (data['Transmission'] <= 1)).all() == True

def test_IOError_in_load_transmission_data():
    # 'Spitzer/IRAC.I2' exists in filter index but not in cache
    pytest.raises(IOError, cf.load_transmission_data, 'Spitzer/IRAC.I2', 
        CACHE_DIR)

def test_ValueError_in_load_transmission_data():
    # 'no/such.filter' is a dummy filter id which doesn't exist
    pytest.raises(ValueError, cf.load_transmission_data, 'no/such.filter', 
        CACHE_DIR)
