import os
import platform

__all__ = (
    "SCBW_BASE_DIR",
    "SC_LOG_DIR",
    "SC_BWAPI_DATA_BWTA_DIR",
    "SC_BWAPI_DATA_BWTA2_DIR",
    "SC_BOT_DIR",
    "SC_MAP_DIR",
    "SC_IMAGE",
    "SC_PARENT_IMAGE",
    "SC_JAVA_IMAGE"
)


def get_data_dir() -> str:
    system = platform.system()
    if system == "Windows":
        return os.getenv('APPDATA') + "/scbw"
    else:
        return os.path.expanduser("~") + "/.scbw"


SCBW_BASE_DIR = get_data_dir()
SC_LOG_DIR = f"{SCBW_BASE_DIR}/logs"
SC_BWAPI_DATA_BWTA_DIR = f"{SCBW_BASE_DIR}/bwapi-data/BWTA"
SC_BWAPI_DATA_BWTA2_DIR = f"{SCBW_BASE_DIR}/bwapi-data/BWTA2"
SC_BOT_DIR = f"{SCBW_BASE_DIR}/bots"
SC_MAP_DIR = f"{SCBW_BASE_DIR}/maps"

SC_IMAGE = "starcraft:game"

SC_PARENT_IMAGE = "ggaic/starcraft:java"
SC_JAVA_IMAGE = "starcraft:java"
