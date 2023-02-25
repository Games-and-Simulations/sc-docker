import logging
import os
import os.path
import shutil
import tempfile

from scbw.error import GameException
from scbw.utils import download_extract_zip



SC_MAP_DIR = os.path.abspath("maps")
logger = logging.getLogger(__name__)



def check_map_exists(map_file: str) -> None:
    if not os.path.exists(map_file):
        raise GameException(f"Map {map_file} could not be found")


def download_sscait_maps(map_dir: str) -> None:
    logger.info("downloading maps from SSCAI")
    download_extract_zip(
        "http://sscaitournament.com/files/sscai_map_pack.zip", map_dir
    )

def download_season_maps(map_dir: str) -> None:
    logger.info("downloading maps for 2019 season 1")
    download_extract_zip(
        "https://github.com/Bytekeeper/sc-docker/releases/download/Maps_2019Season1/2019Season1.zip", map_dir
    )
    logger.info("downloading maps for 2019 season 2")
    download_extract_zip(
        "https://github.com/Bytekeeper/sc-docker/releases/download/Maps_2019Season2/2019Season2.zip", map_dir
    )


def download_bwta_caches(bwta_dir: str, bwta2_dir: str) -> None:
    logger.info("downloading BWTA caches")
    tmp_dir = tempfile.mkdtemp()
    download_extract_zip(
        "https://github.com/adakitesystems/DropLauncher/releases/download/0.4.18a/BWTA_cache.zip",
        tmp_dir
    )

    download_extract_zip(
        "https://github.com/Bytekeeper/sc-docker/releases/download/Maps_2019Season1/BWTA_cache_2019Season1.zip",
        tmp_dir
    )

    for file in os.listdir(tmp_dir + "/bwapi-data/BWTA"):
        if not os.path.exists(f"{bwta_dir}/{file}"):
            shutil.move(tmp_dir + "/bwapi-data/BWTA/" + file, bwta_dir)
    for file in os.listdir(tmp_dir + "/bwapi-data/BWTA2"):
        if not os.path.exists(f"{bwta2_dir}/{file}"):
            shutil.move(tmp_dir + "/bwapi-data/BWTA2/" + file, bwta2_dir)
