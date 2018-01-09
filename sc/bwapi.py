from enum import Enum


class BWAPIVersion(Enum):
    BWAPI_420 = "420"
    BWAPI_412 = "412"

    # More versions can be added, but we need these in /docker/bwapi/[version_name]/
    # - BWAPI.dll
    # - BWAPId.dll
    # - bwapi.ini

    # BWAPI_401B = "401B"
    # BWAPI_374 = "374"


bwapi_md5s = {
    BWAPIVersion.BWAPI_420: "2f6fb401c0dcf65925ee7ad34dc6414a",
    BWAPIVersion.BWAPI_412: "1364390d0aa085fba6ac11b7177797b0"
}
