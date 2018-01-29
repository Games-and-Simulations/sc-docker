import logging
import os
import platform
import zipfile
from os.path import expanduser
from random import choice
from tempfile import mkstemp
import requests
from tqdm import tqdm
logger = logging.getLogger(__name__)


def levenshtein_dist(s1, s2):
    if (len(s1) < len(s2)):
        return levenshtein_dist(s2, s1)
    if (len(s2) == 0):
        return len(s1)
    previous_row = range((len(s2) + 1))
    for (i, c1) in enumerate(s1):
        current_row = [(i + 1)]
        for (j, c2) in enumerate(s2):
            insertions = (previous_row[(j + 1)] + 1)
            deletions = (current_row[j] + 1)
            substitutions = (previous_row[j] + (c1 != c2))
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[(-1)]


def random_string(len=8):
    return ''.join((choice('0123456789ABCDEF') for _ in range(len)))


def download_extract_zip(url, extract_to):
    (fd, filename) = mkstemp()
    try:
        download_file(url, filename)
        with zipfile.ZipFile(filename, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
    finally:
        os.close(fd)
        os.remove(filename)


def download_file(url, as_file):
    headers = {
        'User-Agent':
        'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:55.0) Gecko/20100101 Firefox/55.0'
    }
    response = requests.get(
        url, allow_redirects=True, stream=True, headers=headers)
    logger.debug(('downloading from %s save as %s' % (url, as_file)))
    total_size = int(response.headers.get('content-length', 0))
    block_size = (1024 * 1024)
    with open(as_file, 'wb') as f:
        for data in tqdm(
                response.iter_content(block_size),
                total=(total_size / block_size),
                unit='MB',
                unit_scale=True):
            f.write(data)


def get_data_dir():
    system = platform.system()
    if (system == 'Windows'):
        return (os.getenv('APPDATA') + '/scbw')
    else:
        return (expanduser('~') + '/.scbw')


def create_data_dirs(*dir_paths):
    for dir_path in dir_paths:
        os.makedirs(dir_path, mode=509, exist_ok=True)
