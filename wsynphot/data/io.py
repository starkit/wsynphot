import logging
import yaml

CONFIGURATION_PATH = 'xxx'

DEFAULT_DATA_DIR
logger = logging.getLogger(__name__)

def get_configuration():
    return yaml.load(open(CONFIGURATION_PATH))

def get_data_dir():

    config = get_configuration()
    data_dir = config.get('data_dir', None)
    if data_dir is None:
        logging.warning('data_dir not specified - '.format())
