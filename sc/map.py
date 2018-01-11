from os.path import exists, abspath

SC_MAP_DIR = abspath("maps")


def check_map_exists(map_file: str):
    if not exists(map_file):
        raise Exception(f"Map {map_file} could not be found")
