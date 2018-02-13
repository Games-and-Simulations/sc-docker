import os
import platform
__all__ = ('SCBW_BASE_DIR', 'SC_LOG_DIR', 'SC_BWAPI_DATA_BWTA_DIR',
           'SC_BWAPI_DATA_BWTA2_DIR', 'SC_BOT_DIR', 'SC_MAP_DIR', 'SC_IMAGE',
           'SC_PARENT_IMAGE', 'SC_JAVA_IMAGE')


def get_data_dir():
    system = platform.system()
    if (system == 'Windows'):
        return (os.getenv('APPDATA') + '/scbw')
    else:
        return (os.path.expanduser('~') + '/.scbw')


SCBW_BASE_DIR = get_data_dir()
SC_LOG_DIR = ('%s/logs' % (SCBW_BASE_DIR, ))
SC_BWAPI_DATA_BWTA_DIR = ('%s/bwapi-data/BWTA' % (SCBW_BASE_DIR, ))
SC_BWAPI_DATA_BWTA2_DIR = ('%s/bwapi-data/BWTA2' % (SCBW_BASE_DIR, ))
SC_BOT_DIR = ('%s/bots' % (SCBW_BASE_DIR, ))
SC_MAP_DIR = ('%s/maps' % (SCBW_BASE_DIR, ))
SC_IMAGE = 'starcraft:game'
SC_PARENT_IMAGE = 'ggaic/starcraft:java'
SC_JAVA_IMAGE = 'starcraft:java'
