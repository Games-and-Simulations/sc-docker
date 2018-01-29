import logging
import os
import zipfile
from random import choice
from tempfile import mkstemp

import requests
from tqdm import tqdm

logger = logging.getLogger(__name__)


def levenshtein_dist(s1, s2):
    if len(s1) < len(s2):
        return levenshtein_dist(s2, s1)

    # len(s1) >= len(s2)
    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[
                             j + 1] + 1  # j+1 instead of j since previous_row and current_row are one character longer
            deletions = current_row[j] + 1  # than s2
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


def random_string(len: int = 8) -> str:
    return "".join(choice("0123456789ABCDEF") for _ in range(len))


def download_extract_zip(url: str, extract_to: str):
    fd, filename = mkstemp()
    try:
        download_file(url, filename)
        with zipfile.ZipFile(filename, 'r') as zip_ref:
            zip_ref.extractall(extract_to)

    finally:
        os.close(fd)
        os.remove(filename)


def download_file(url: str, as_file: str):
    headers = {
        # python is sending some python User-Agent that Cloudflare doesn't like
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:55.0) Gecko/20100101 Firefox/55.0'
    }
    response = requests.get(url, allow_redirects=True, stream=True, headers=headers)
    logger.debug(f"downloading from {url} save as {as_file}")

    # Total size in bytes.
    total_size = int(response.headers.get('content-length', 0))
    block_size = 1024 * 1024

    with open(as_file, 'wb') as f:
        for data in tqdm(response.iter_content(block_size),
                         total=total_size / block_size, unit='MB', unit_scale=True):
            f.write(data)


def create_data_dirs(*dir_paths):
    for dir_path in dir_paths:
        os.makedirs(dir_path, mode=0o775, exist_ok=True)
