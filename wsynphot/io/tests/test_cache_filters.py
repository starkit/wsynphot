import pytest
import os, re

import wsynphot
from wsynphot.io.get_filter_data import data_from_svo
from wsynphot.io import cache_filters as cf

DATA_PATH = os.path.join(wsynphot.__path__[0], 'io', 'tests', 'data')
CACHE_READING_DIR = os.path.join(DATA_PATH, 'filters', 'SVO')  # read test data
TEST_LAMBDA = 12000

# Temporary dir for storing the cache data written by functions while testing
@pytest.fixture(scope='module')
def cache_writing_dir(tmpdir_factory):
    return str(tmpdir_factory.mktemp('cache_data'))


# ---------------- Tests for cache writing functions -------------------------

def test_download_filter_data(monkeypatch, cache_writing_dir):
    '''download_filter_data() calls get_filter_index() which fetches complete 
    filter index (~5K filters), instead of it use a mock function to fetch 
    only a short filter list (<10 filters)'''
    def mock_get_filter_index():
        query = {'WavelengthEff_min': TEST_LAMBDA,
                'WavelengthEff_max': TEST_LAMBDA+100}
        return data_from_svo(query, 'No filters in specified wavelength range')

    # Inject mock_get_filter_index in place of get_filter_index
    monkeypatch.setattr(cf, 'get_filter_index', mock_get_filter_index)
    cf.download_filter_data(cache_writing_dir)

    # Test whether cached index votable is converible to dataframe
    index_path = os.path.join(cache_writing_dir, 'index.vot')
    assert os.path.exists(index_path)
    index = cf.df_from_votable(index_path)
    assert not index.empty

    # Test whether filter votables got cached in appropriate directories
    for filter_id in index['filterID']:
        facility, instrument, filter_name = re.split('/|\.', filter_id)
        assert os.path.exists(os.path.join(cache_writing_dir, facility, 
            instrument, '{0}.vot'.format(filter_name)))



def test_update_filter_data(monkeypatch, cache_writing_dir):
    # Read old index (i.e. cached by download function) before updating it
    index = cf.df_from_votable(os.path.join(cache_writing_dir, 'index.vot'))

    '''update_filter_data() calls get_filter_index() to fetch new filter index, 
    mock it to fetch only a short filter list instead of complete index'''
    def mock_get_filter_index():

        '''Choose wavelength range for the new index to be overlapping with 
        the index present on disk, so that we can get filters to remove as
        well as to add. Ranges used are:
        old index:      x ---------- x+100
        new index:        x+50 ---------- x+150          (x = TEST_LAMBDA)
        '''
        query = {'WavelengthEff_min': TEST_LAMBDA+50,
                'WavelengthEff_max': TEST_LAMBDA+150}
        return data_from_svo(query, 'No filters in specified wavelength range')


    # Inject mock_get_filter_index in place of get_filter_index
    monkeypatch.setattr(cf, 'get_filter_index', mock_get_filter_index)
    cf.update_filter_data(cache_writing_dir)

    # Find the outdated filters & test whether their votables got removed
    removed_filters = index[index['WavelengthEff'] < TEST_LAMBDA+50]['filterID']
    for filter_id in removed_filters:
        facility, instrument, filter_name = re.split('/|\.', filter_id)
        assert not os.path.exists(os.path.join(cache_writing_dir, facility, 
            instrument, '{0}.vot'.format(filter_name))) 

    # Read the updated index (i.e. cached by update function)
    index = cf.df_from_votable(os.path.join(cache_writing_dir, 'index.vot'))
    
    # Find the new filters & test whether their votables got cached
    added_filters = index[index['WavelengthEff'] > TEST_LAMBDA+100]['filterID']
    for filter_id in added_filters:
        facility, instrument, filter_name = re.split('/|\.', filter_id)
        assert os.path.exists(os.path.join(cache_writing_dir, facility, 
            instrument, '{0}.vot'.format(filter_name)))


# ------------------ Tests for cache reading functions -----------------------

def test_load_filter_index():
    data = cf.load_filter_index(CACHE_READING_DIR)
    assert data.empty == False
    assert 'filterID' in data.columns


def test_IOError_in_load_filter_index():
    # When no filter index found in passed cache directory
    pytest.raises(IOError, cf.load_filter_index, DATA_PATH)


@pytest.mark.parametrize(('test_filter_id'), 
                        ['HST/NICMOS1.F113N', 'HST/ACS_HRC.F250W'])
def test_load_transmission_data(test_filter_id):
    data = cf.load_transmission_data(test_filter_id, CACHE_READING_DIR)
    assert data.empty == False
    assert (data['Wavelength'] > 0).all() == True
    assert ((data['Transmission'] >= 0) &
        (data['Transmission'] <= 1)).all() == True


def test_IOError_in_load_transmission_data():
    # 'Spitzer/IRAC.I2' exists in filter index but not in cache
    pytest.raises(IOError, cf.load_transmission_data, 'Spitzer/IRAC.I2', 
        CACHE_READING_DIR)


def test_ValueError_in_load_transmission_data():
    # 'no/such.filter' is a dummy filter id which doesn't exist
    pytest.raises(ValueError, cf.load_transmission_data, 'no/such.filter', 
CACHE_READING_DIR)