import subprocess
from os import environ, sys
from .utils import which

def check_vnc_exists():
    if(sys.platform == "win32"):
        if "RealVNC" in environ.get('Path'):
            out = "vncviewer"
        else:
            out = None
    else:
        try:
            out = which("vnc-viewer")
        except Exception as e:
            raise Exception("An error occurred while trying to find path to vnc-viewer")
    
    if out is None:
        raise Exception(f"vnc-viewer not found!")

def launch_vnc_viewer(port: int):
    if(sys.platform == "win32"):
        subprocess.call(f"vncviewer localhost:{port} &", shell=True)
    else:
        subprocess.call(f"vnc-viewer localhost:{port} &", shell=True)

