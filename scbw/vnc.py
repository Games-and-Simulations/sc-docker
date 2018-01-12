import subprocess

from .utils import which


def check_vnc_exists():
    try:
        out = which("vnc-viewer")
    except Exception as e:
        raise Exception("An error occurred while trying to find path to vnc-viewer")

    if out is None:
        raise Exception(f"vnc-viewer not found!")


def launch_vnc_viewer(port: int):
    subprocess.call(f"vnc-viewer localhost:{port} &", shell=True)
