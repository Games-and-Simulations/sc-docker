import logging
import os
import shutil
import tempfile
from os.path import exists, abspath
from .error import GameException
from .utils import download_extract_zip
SC_MAP_DIR = abspath('maps')
logger = logging.getLogger(__name__)


def check_map_exists(map_file):
    if (not exists(map_file)):
        raise GameException(('Map %s could not be found' % (map_file, )))


def download_sscait_maps(map_dir):
    logger.info('downloading maps from SSCAI')
    download_extract_zip('http://sscaitournament.com/files/sscai_map_pack.zip',
                         map_dir)


def download_bwta_caches(bwta_dir, bwta2_dir):
    logger.info('downloading BWTA caches')
    tmp_dir = tempfile.mkdtemp()
    download_extract_zip(
        'https://github.com/adakitesystems/DropLauncher/releases/download/0.4.18a/BWTA_cache.zip',
        tmp_dir)
    for file in os.listdir((tmp_dir + '/bwapi-data/BWTA')):
        shutil.move(((tmp_dir + '/bwapi-data/BWTA/') + file), bwta_dir)
    for file in os.listdir((tmp_dir + '/bwapi-data/BWTA2')):
        shutil.move(((tmp_dir + '/bwapi-data/BWTA2/') + file), bwta2_dir)
