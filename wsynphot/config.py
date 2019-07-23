from wsynphot import __path__ as WSYNPHOT_PATH
import os, logging, shutil
import yaml
from datetime import datetime

from astropy.config import get_config_dir


WSYNPHOT_PATH = WSYNPHOT_PATH[0]
DEFAULT_CONFIG_PATH = os.path.join(WSYNPHOT_PATH, 'data', 'default_wsynphot_config.yml')
DEFAULT_DATA_DIR = os.path.join(os.path.expanduser('~'), 'Downloads', 'wsynphot')
CONFIG_FPATH  = os.path.join(get_config_dir(), 'wsynphot_config.yml')
logger = logging.getLogger(__name__)


def get_configuration():

    if not os.path.exists(CONFIG_FPATH):
        logger.warning("Configuration File {0} does not exist - creating new one from default".format(CONFIG_FPATH))
        shutil.copy(DEFAULT_CONFIG_PATH, CONFIG_FPATH)
    return yaml.load(open(CONFIG_FPATH),Loader=yaml.SafeLoader)


def get_data_dir():

    config = get_configuration()
    data_dir = config.get('data_dir', None)
    if data_dir is None:
        logger.critical('\n{line_stars}\n\nWYSNPHOT will download filters to its data directory {default_data_dir}\n\n'
                         'WSYNPHOT DATA DIRECTORY not specified in {config_file}:\n\n'
                         'ASSUMING DEFAULT DATA DIRECTORY {default_data_dir}\n '
                         'YOU CAN CHANGE THIS AT ANY TIME IN {config_file} \n\n'
                         '{line_stars} \n\n'.format(line_stars='*'*80, config_file=CONFIG_FPATH,
                                                     default_data_dir=DEFAULT_DATA_DIR))
        if not os.path.exists(DEFAULT_DATA_DIR):
            os.makedirs(DEFAULT_DATA_DIR)
        config['data_dir'] = DEFAULT_DATA_DIR
        yaml.dump(config, open(CONFIG_FPATH, 'w'), default_flow_style=False)
        data_dir = DEFAULT_DATA_DIR

    if not os.path.exists(data_dir):
        raise IOError('Data directory specified in {0} does not exist'.format(data_dir))

    return data_dir


def get_cache_dir():
    cache_dir = os.path.join(get_data_dir(), 'filters', 'SVO')
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    return cache_dir


def get_calibration_dir():
    calibration_dir = os.path.join(get_data_dir(), 'calibration')
    if not os.path.exists(calibration_dir):
        os.makedirs(calibration_dir)
    return calibration_dir


def get_cache_updation_date():
    """Gets value of cache_updation_date from the configuration file and handles
     the exceptions when unexpected value is encountered"""

    config = get_configuration()
    cache_updation_date_text = config.get('cache_updation_date', None)
    cache_dir = get_cache_dir()

    # Check whether date is present
    if cache_updation_date_text is None:
        if os.listdir(cache_dir):
            cache_updation_date = rectify_cache_updation_date(config,
                'No date present, even when cache exists')
        else:  # When cache is not downloaded/updated atleast once
            cache_updation_date = None

    else:
        try:
            cache_updation_date = datetime.strptime(cache_updation_date_text, 
                '%Y-%m-%d').date()
        except ValueError:  # Can't be parsed as per expected format
            cache_updation_date = rectify_cache_updation_date(config, 
                'Invalid date value')
        else:
            if cache_updation_date > datetime.now().date():
                cache_updation_date = rectify_cache_updation_date(config, 
                    'Date belongs to future')

    return cache_updation_date


def set_cache_updation_date():
    """Sets the cache_updation_date to current date. This function is meant 
    to be used by cache download/update functions for saving when they were 
    called last time"""

    config = get_configuration()
    current_date = datetime.now().date()
    config['cache_updation_date'] = str(current_date)
    yaml.dump(config, open(CONFIG_FPATH, 'w'), default_flow_style=False)


def rectify_cache_updation_date(config, error_log):
    """Sets the correct cache_updation_date so that wsynphot can automatically 
    recover from wrong configuration, when user has changed the date value 
    mistakenly"""

    logger.critical('\n{line_stars}\n\nUNEXPECTED CHANGES DETECTED IN '
        '`cache_updation_date`: {error_text}\n\nAssuming it as the latest '
        'modification date of cached filter index\n\n{line_stars}\n'
        '\n'.format(line_stars='*'*80, error_text=error_log))

    index_modification_timestamp = os.path.getmtime(os.path.join(get_cache_dir(),
        'index.vot'))
    cache_updation_date = datetime.fromtimestamp(index_modification_timestamp).date()
    config['cache_updation_date'] = str(cache_updation_date)
    yaml.dump(config, open(CONFIG_FPATH, 'w'), default_flow_style=False)

    return cache_updation_date