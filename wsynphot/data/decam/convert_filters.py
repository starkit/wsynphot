#Reading Gemini GMOS filters

from astropy import units as u, constants as const
from numpy import genfromtxt
import pandas as pd
import os
from glob import glob

def read_decam_filter(fname):
    """
    Reading the bessell filter file into a dataframe

    Parameters
    ----------

    fname: ~str
        path to file to be read

    """

    data = pd.DataFrame(genfromtxt(fname, usecols=(0, 1)),
                        columns=['wavelength', 'transmission_lambda'])

    return data


def read_dataset(fname_list, prefix, name_parser=None):
    """
    Reading a whole list of filters

    Parameters
    ----------

    fname_list: list
        list of filenames

    prefix: str
        prefix for the dictionary keys

    Returns
    -------

    dict
    """

    filter_dict = {}

    for fname in fname_list:
        if name_parser is not None:
            filter_name = name_parser(fname)
        else:
            filter_name = fname

        filter_path = os.path.join(prefix, filter_name)

        filter_dict[filter_path] = read_decam_filter(fname)

    return filter_dict



def read_all_decam():
    nameparser = (lambda fname: os.path.basename(fname).replace('DECam.', ''))
    return read_dataset(glob('DECam.?'), 'decam',
                          nameparser)

def save_to_hdf(filter_dict, hdf_file, mode='a'):

    fh = pd.HDFStore(hdf_file, mode=mode)

    for key in filter_dict:
        filter_dict[key].to_hdf(fh, key)

    fh.close()
