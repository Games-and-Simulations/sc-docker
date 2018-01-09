from os.path import exists


def check_map_exists(map_file: str):
    if not exists(map_file):
        raise Exception(f"Map {map} could not be found")
