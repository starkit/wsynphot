import numpy as np
import pandas as pd
import requests, tempfile

from astropy.io.votable import parse_single_table
# The VOTables fetched from SVO contain only single table element, thus parse_single_table

svo_main_url = 'http://svo2.cab.inta-csic.es/theory/fps/fps.php'

# A utility fuction to convert byte strings to normal literal strings
def byte_to_literal_strings(dataframe):
    # Select the str columns:
    str_df = dataframe.select_dtypes([np.object])
    
    # Convert all of them into unicode strings
    str_df = str_df.stack().str.decode('utf-8').unstack()
    
    # Swap out converted cols with the original df cols
    for col in str_df:
        dataframe[col] = str_df[col]
    return dataframe


def get_filter_index():
    # To get master list, fetch all filters from SVO of wavelength between 0 & very large no.
    query = {'WavelengthEff_min': 0,
             'WavelengthEff_max': 10000000}
    response = requests.get(svo_main_url, params=query)
    response.raise_for_status()
    
    # Save the fetched VOTable (XML file) as a temporary file and parse it into an Astropy table
    with tempfile.NamedTemporaryFile() as votable:
        votable.write(response.content)
        table = parse_single_table(votable.name).to_table()

    # TODO: Remove unnecessary columns from table (since there're 31 columns)
    
    # Return table after converting it to pandas dataframe
    index = table.to_pandas()
    return byte_to_literal_strings(index)  # Since byte strings appear


def get_transmission_data(filter_id):
    # Fetch transmission data from SVO for the requested filter_id
    # filter_id should be in SVO Filter ID format (facility/instrument.filter)
    query = {'ID': filter_id}
    response = requests.get(svo_main_url, params=query)
    response.raise_for_status()
    
    # Save the fetched VOTable in a temporary file & try parsing it into an Astropy table
    with tempfile.NamedTemporaryFile() as votable:
        votable.write(response.content)
        try:
            table = parse_single_table(votable.name).to_table()
        except ValueError:
            # If no table element found in VOTable
            raise ValueError('Requested filter ({0}) does not exist'.format(filter_id))

    # Return table after converting it to pandas dataframe
    return table.to_pandas()


def get_filter_list(facility, instrument=None):
    # Fetch all filters for requested facilty and instrument (optional)
    query = {'Facility': facility, 
             'Instrument': instrument}
    response = requests.get(svo_main_url, params=query)
    response.raise_for_status()
    
    # Save the fetched VOTable in a temporary file & try parsing it into an Astropy table
    with tempfile.NamedTemporaryFile() as votable:
        votable.write(response.content)
        try:
            table = parse_single_table(votable.name).to_table()
        except ValueError:
            # If no table element found in VOTable
            raise ValueError('No filter found for requested facilty & instrument')

    # Return table after converting it to pandas dataframe
    filter_list = table.to_pandas()
    return byte_to_literal_strings(filter_list)  # Since byte strings appear
