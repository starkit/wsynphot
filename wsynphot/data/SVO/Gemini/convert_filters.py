#Reading Gemini GMOS filters

from astropy import units as u, constants as const
from numpy import genfromtxt
import pandas as pd
import os
from glob import glob

def read_gemini_filter(fname):
    """
    Reading the gemini filter file into a dataframe

    Parameters
    ----------

    fname: ~str
        path to file to be read

    """

    for i, line in enumerate(open(fname)):
        if line.strip()[1:].strip().startswith('lambda'):
            skiprows = i
            break
    else:
        raise ValueError('File {0} not formatted in Gemini style'.format(fname))

    data = pd.DataFrame(genfromtxt(fname, skip_header=skiprows),
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

        filter_dict[filter_path] = read_gemini_filter(fname)

    return filter_dict



def read_all_gemini():
    gmos_s_nameparser = (lambda fname: os.path.basename(fname).replace(
        'gmos_s_', '').replace('.txt', ''))
    gmos_filters = read_dataset(glob('gmoss/*.txt'), 'gemini/gmoss',
                          gmos_s_nameparser)


    gmos_n_nameparser = (lambda fname: os.path.basename(fname).replace(
        'gmos_n_', '').replace('.txt', ''))
    gmos_n = read_dataset(glob('gmosn/*.txt'), 'gemini/gmosn',
                          gmos_n_nameparser)

    gmos_filters.update(gmos_n)

    return gmos_filters

def save_to_hdf(filter_dict, hdf_file, mode='a'):

    fh = pd.HDFStore(hdf_file, mode=mode)

    for key in filter_dict:
        filter_dict[key].to_hdf(fh, key)

    fh.close()
