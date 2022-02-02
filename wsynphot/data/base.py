import os
import shutil
import urllib.request as request
import logging

import requests
from tqdm.autonotebook import tqdm
from wsynphot.config import get_calibration_dir

logger = logging.getLogger(__name__)


ALPHA_LYR_FNAME = 'alpha_lyr_mod_002.fits'

ALPHA_LYR_PATH = os.path.join(get_calibration_dir(), ALPHA_LYR_FNAME)

ALPHA_LYR_MOD_URL = "https://archive.stsci.edu/hlsps/reference-atlases/cdbs/calspec/{0}".format(
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


def download_calibration_data():
    if os.path.exists(ALPHA_LYR_PATH):
        logger.error('Alpha Lyra calibration already exists - not downloading')
    else:
        logger.info('Downloading Alpha Lyra calibration ...')
        with request.urlopen(ALPHA_LYR_MOD_URL) as response:
            with open(ALPHA_LYR_PATH, 'wb') as file:
                shutil.copyfileobj(response, file)
