#Reading Gemini GMOS filters

from astropy import units as u, constants as const
from numpy import genfromtxt
import pandas as pd

def read_gemini_filter(fname):
    """
    Reading the gemini filter file into a dataframe

    Parameters
    ----------

    fname: ~str
        path to file to be read

    """

    for i, line in enumerate(open(fname)):
        if line[1:].strip().startswith('lambda'):
            skiprows = i
            break

    data = pd.DataFrame(genfromtxt(fname, skip_header=skiprows),
                        columns=['wavelength', 'transmission'])

    return data
