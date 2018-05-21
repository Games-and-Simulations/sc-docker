import os
import shutil


def check_vnc_exists():
    try:
        out = shutil.which('vnc-viewer')
    except Exception as e:
        raise Exception(
            'An error occurred while trying to find path to vnc-viewer')
    if (out is None):
        raise Exception(('vnc-viewer not found!' % ()))


def launch_vnc_viewer(host, port):
    os.spawnl(os.P_NOWAIT,
              shutil.which('vnc-viewer'), 'vnc-viewer', ('%s:%s' % (host,
                                                                    port)))
