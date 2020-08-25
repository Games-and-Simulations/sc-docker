import os
import platform


def get_data_dir() -> str:
    system = platform.system()
    if system == "Windows":
        return os.getenv('APPDATA') + "/scbw"
    else:
        return os.path.expanduser("~") + "/.scbw"


VERSION = "1.0.4-BK"

SCBW_BASE_DIR = get_data_dir()
SC_GAME_DIR = f"{SCBW_BASE_DIR}/games"
SC_BWAPI_DATA_BWTA_DIR = f"{SCBW_BASE_DIR}/bwapi-data/BWTA"
SC_BWAPI_DATA_BWTA2_DIR = f"{SCBW_BASE_DIR}/bwapi-data/BWTA2"
SC_BOT_DIR = f"{SCBW_BASE_DIR}/bots"
SC_MAP_DIR = f"{SCBW_BASE_DIR}/maps"

SC_IMAGE = "starcraft:game"
SC_JAVA_IMAGE = "starcraft:java"
