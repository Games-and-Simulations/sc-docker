import os
import platform


def get_data_dir():
    system = platform.system()
    if (system == 'Windows'):
        return (os.getenv('APPDATA') + '/scbw')
    else:
        return (os.path.expanduser('~') + '/.scbw')


VERSION = '1.0.2'
SCBW_BASE_DIR = get_data_dir()
SC_GAME_DIR = ('%s/games' % (SCBW_BASE_DIR, ))
SC_BWAPI_DATA_BWTA_DIR = ('%s/bwapi-data/BWTA' % (SCBW_BASE_DIR, ))
SC_BWAPI_DATA_BWTA2_DIR = ('%s/bwapi-data/BWTA2' % (SCBW_BASE_DIR, ))
SC_BOT_DIR = ('%s/bots' % (SCBW_BASE_DIR, ))
SC_MAP_DIR = ('%s/maps' % (SCBW_BASE_DIR, ))
SC_IMAGE = ('starcraft:game-' + VERSION)
SC_PARENT_IMAGE = ('ggaic/starcraft:java-' + VERSION)
SC_JAVA_IMAGE = 'starcraft:java'
SC_BINARY_LINK = 'http://files.theabyss.ru/sc/starcraft.zip'
