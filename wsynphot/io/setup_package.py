# Licensed under a 3-clause BSD style license - see LICENSE.rst

def get_package_data():
    index_file = 'data/cached_SVO_FPS/index.vot'
    transmission_data_files = 'data/cached_SVO_FPS/*/*/*.vot'
    return {'wsynphot.io.tests': [index_file, transmission_data_files]}
