from __future__ import print_function
import os

import requests
from tqdm.autonotebook import tqdm
from wsynphot.config import get_data_dir



FILTER_DATA_FPATH = os.path.join(get_data_dir(), 'filter_data.h5')

DATA_TRANSMISSION_URL = ("https://zenodo.org/record/1467309/files/"
                         "filter_data.h5?download=1")

ALPHA_LYR_FNAME = 'alpha_lyr_mod_002.fits'
ALPHA_LYR_PATH = os.path.join(os.path.dirname(__file__), 'calibration',
                              ALPHA_LYR_FNAME)

ALPHA_LYR_MOD_URL= "ftp://ftp.stsci.edu/cdbs/calspec/{0}".format(
    ALPHA_LYR_FNAME)


def download_from_url(url, dst):
    """
    kindly used from https://gist.github.com/wy193777/0e2a4932e81afc6aa4c8f7a2984f34e2
    @param: url to download file
    @param: dst place to put the file
    """

    file_size = int(requests.head(url).headers["Content-Length"])
    if os.path.exists(dst):
        first_byte = os.path.getsize(dst)
    else:
        first_byte = 0
    if first_byte >= file_size:
        return file_size
    header = {"Range": "bytes=%s-%s" % (first_byte, file_size)}
    pbar = tqdm(
        total=file_size, initial=first_byte,
        unit='B', unit_scale=True, desc=url.split('/')[-1])
    req = requests.get(url, headers=header, stream=True)
    with(open(dst, 'ab')) as f:
        for chunk in req.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)
                pbar.update(1024)
    pbar.close()
    return file_size




def download_filter_data():
    if os.path.exists(FILTER_DATA_FPATH):
        print('Filter Data already exists - you can delete by '
              'calling wsynphot.delete_filter_data()')
    download_from_url(DATA_TRANSMISSION_URL, FILTER_DATA_FPATH)

def delete_filter_data():
    if not os.path.exists(FILTER_DATA_FPATH):
        print('Filter Data does not exist - nothing to delete')
    os.remove(FILTER_DATA_FPATH)

def download_calibration_data():
    if os.path.exists(ALPHA_LYR_PATH):
        print('Alpha Lyra calibration already exists - not downloading')
    else:
        download_from_url(ALPHA_LYR_MOD_URL, ALPHA_LYR_PATH)