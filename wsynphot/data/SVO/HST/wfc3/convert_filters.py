#Reading Gemini GMOS filters

from astropy import units as u, constants as const
from numpy import genfromtxt, asscalar
import pandas as pd
import os
from glob import glob

def read_hst_filter(fname):
    """
    Reading the gemini filter file into a dataframe

    Parameters
    ----------

    fname: ~str
        path to file to be read

    """

    for i, line in enumerate(open(fname)):
        if line.strip().startswith('1'):
            skiprows = i - 1
            break
    else:
        raise ValueError('File {0} not formatted in Gemini style'.format(fname))

    data = pd.DataFrame(genfromtxt(fname, skip_header=skiprows, usecols=(1, 2)),
                        columns=['wavelength', 'transmission_lambda'])

    start_filter_idx = asscalar(
        (data.transmission_lambda > 0).searchsorted(1) - 1)
    end_filter_idx = (data.transmission_lambda > 0)[::-1].searchsorted(1)
    end_filter_idx = asscalar((len(data) - end_filter_idx) + 1)

    return data.iloc[start_filter_idx:end_filter_idx]


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

        filter_dict[filter_path] = read_hst_filter(fname)

    return filter_dict



def read_all_hst():
    hst_nameparser = (lambda fname:
                      '_'.join(os.path.basename(fname).lower().split('.')[:2]))
    hst_filters = read_dataset(glob('filter_data/*.tab'), 'hst/wfc3',
                          hst_nameparser)

    #rewriting hst_filters dict keys:

    for key, value in hst_filters.items():
        del hst_filters[key]
        long_fname = key.split('/')[-1]
        filter_name, band = long_fname.split('_')
        new_key = '/'.join(key.split('/')[:-1] + [band, filter_name])
        hst_filters[new_key] = value


    return hst_filters

def save_to_hdf(filter_dict, hdf_file, mode='a'):

    fh = pd.HDFStore(hdf_file, mode=mode)

    for key in filter_dict:
        filter_dict[key].to_hdf(fh, key)

    fh.close()
