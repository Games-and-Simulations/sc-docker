import logging
import os
from os.path import exists, abspath

from .utils import download_extract_zip

SC_MAP_DIR = abspath("maps")
logger = logging.getLogger(__name__)


def check_map_exists(map_file: str):
    if not exists(map_file):
        raise Exception(f"Map {map_file} could not be found")


def download_sscait_maps(map_dir: str):
    logger.info("downloading maps from SSCAI")
    download_extract_zip("http://sscaitournament.com/files/sscai_map_pack.zip", map_dir)
    os.makedirs(f"{map_dir}/replays", exist_ok=True)
