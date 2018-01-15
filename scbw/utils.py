import os
import urllib.request as request
import zipfile
from random import choice
from tempfile import mkstemp


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
    _, filename = mkstemp()
    try:
        download_file(url, filename)
        with zipfile.ZipFile(filename, 'r') as zip_ref:
            zip_ref.extractall(extract_to)

    finally:
        os.remove(filename)


def download_file(url: str, as_file: str):
    opener = request.FancyURLopener()
    # python is sending some python User-Agent that Cloudflare doesn't like
    opener.version = 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:55.0) Gecko/20100101 Firefox/55.0'
    opener.retrieve(url, as_file)
