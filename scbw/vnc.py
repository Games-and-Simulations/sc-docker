import shutil

import os


def check_vnc_exists():
    try:
        out = shutil.which("vnc-viewer")
    except Exception as e:
        raise Exception("An error occurred while trying to find path to vnc-viewer")

    if out is None:
        raise Exception(f"vnc-viewer not found!")


def launch_vnc_viewer(port: int):
    # launch in bg
    os.spawnl(os.P_NOWAIT, shutil.which("vnc-viewer"), "vnc-viewer", f"localhost:{port}")
