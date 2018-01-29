import logging
import os
from os.path import exists

import sys

from .defaults import *
from .docker import check_docker_version, check_docker_can_run, check_docker_has_local_net, \
    create_local_net, create_local_image, remove_game_image
from .map import download_sscait_maps, download_bwta_caches
from .utils import create_data_dirs

logger = logging.getLogger(__name__)


def install():
    if exists(SCBW_BASE_DIR):
        logger.warning(f"Path {SCBW_BASE_DIR} found, re-installing scbw package.")
        logger.info("This will re-create the base game image, continue? [Y/n]")
        do_continue = input()
        if not do_continue == "y" and not do_continue == "Y" and not do_continue == "":
            logger.warning("Reinstall aborted by user.")
            sys.exit(1)

    check_docker_version()
    check_docker_can_run()
    check_docker_has_local_net() or create_local_net()

    # remove old image in case of update
    remove_game_image(SC_IMAGE)
    create_local_image(SC_IMAGE)

    create_data_dirs(
        SC_LOG_DIR,
        SC_BWAPI_DATA_BWTA_DIR,
        SC_BWAPI_DATA_BWTA2_DIR,
        SC_BOT_DIR,
        SC_MAP_DIR,
    )

    download_sscait_maps(SC_MAP_DIR)
    download_bwta_caches(SC_BWAPI_DATA_BWTA_DIR, SC_BWAPI_DATA_BWTA2_DIR)
    os.makedirs(f"{SC_MAP_DIR}/replays", exist_ok=True)
    os.makedirs(f"{SC_MAP_DIR}/BroodWar", exist_ok=True)

    logger.info("Install finished. Data files are located in")
    logger.info(SCBW_BASE_DIR)


if __name__ == '__main__':
    install()
