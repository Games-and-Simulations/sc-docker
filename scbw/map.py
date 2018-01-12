import logging
import os
import urllib.request
import zipfile
from os.path import exists, abspath

SC_MAP_DIR = abspath("maps")
logger = logging.getLogger(__name__)


def check_map_exists(map_file: str):
    if not exists(map_file):
        raise Exception(f"Map {map_file} could not be found")


def download_sscait_maps(map_dir: str):
    logger.info("downloading maps from SSCAI")
    urllib.request.urlretrieve("http://sscaitournament.com/files/sscai_map_pack.zip", 'maps.zip')
    with zipfile.ZipFile(f'maps.zip', 'r') as zip_ref:
        zip_ref.extractall(map_dir)

    os.remove(f'maps.zip')
    os.makedirs(f"{map_dir}/replays", exist_ok=True)
