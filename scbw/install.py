import logging
import os
import os.path
from scbw.defaults import SCBW_BASE_DIR, SC_IMAGE, SC_GAME_DIR, SC_BOT_DIR, SC_MAP_DIR, SC_BWAPI_DATA_BWTA_DIR, SC_BWAPI_DATA_BWTA2_DIR
from scbw.docker_utils import ensure_docker_can_run, ensure_local_net, remove_game_image, ensure_local_image
from scbw.map import download_bwta_caches, download_sscait_maps
from scbw.utils import create_data_dirs
logger = logging.getLogger(__name__)


def install():
    if os.path.exists(SCBW_BASE_DIR):
        logger.warning(
            ('Path %s found, re-installing scbw package.' % (SCBW_BASE_DIR, )))
        logger.warning('Re-creating the base game image...')
    ensure_docker_can_run()
    ensure_local_net()
    remove_game_image(SC_IMAGE)
    ensure_local_image(SC_IMAGE)
    create_data_dirs(SC_GAME_DIR, SC_BWAPI_DATA_BWTA_DIR,
                     SC_BWAPI_DATA_BWTA2_DIR, SC_BOT_DIR, SC_MAP_DIR)
    download_sscait_maps(SC_MAP_DIR)
    download_bwta_caches(SC_BWAPI_DATA_BWTA_DIR, SC_BWAPI_DATA_BWTA2_DIR)
    os.makedirs(('%s/replays' % (SC_MAP_DIR, )), exist_ok=True)
    os.makedirs(('%s/BroodWar' % (SC_MAP_DIR, )), exist_ok=True)
    logger.info('Install finished. Data files are located in')
    logger.info(SCBW_BASE_DIR)


if (__name__ == '__main__'):
    install()
