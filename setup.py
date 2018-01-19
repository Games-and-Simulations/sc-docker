"""
Starcraft BW docker launcher.
"""

from os.path import exists

from scbw import VERSION
# Always prefer setuptools over distutils
from setuptools import setup
from setuptools.command.develop import develop
from setuptools.command.install import install
from scbw.utils import get_data_dir

base_dir = get_data_dir() + "/docker"


def install_or_update():
    from scbw.cli import SC_LOG_DIR, SC_BWAPI_DATA_BWTA_DIR, SC_BWAPI_DATA_BWTA2_DIR, SC_BOT_DIR, \
        SC_MAP_DIR
    from scbw.docker import check_docker_version, check_docker_can_run, check_docker_has_local_net, \
        create_local_net, create_local_image, remove_game_image
    from scbw.map import download_sscait_maps
    from scbw.utils import create_data_dirs

    check_docker_version()
    check_docker_can_run()
    check_docker_has_local_net() or create_local_net()

    # remove old image in case of update
    remove_game_image()
    create_local_image()

    create_data_dirs(
        SC_LOG_DIR,
        SC_BWAPI_DATA_BWTA_DIR,
        SC_BWAPI_DATA_BWTA2_DIR,
        SC_BOT_DIR,
        SC_MAP_DIR,
    )
    if not exists(f"{SC_MAP_DIR}/sscai"):
        download_sscait_maps(SC_MAP_DIR)


class PostDevelopCommand(develop):
    """Post-installation for development mode."""

    def run(self):
        develop.run(self)
        install_or_update()


class PostInstallCommand(install):
    """Post-installation for installation mode."""

    def run(self):
        install.run(self)
        install_or_update()


setup(
    name='scbw',
    version=VERSION,
    description='Multi-platform Version of StarCraft: Brood War in a Docker Container',
    long_description="This repository contains fully working StarCraft game running in Wine "
                     "inside of docker image. It can launch bots that use BWAPI client "
                     "to communicate with the game. Please visit "
                     "https://github.com/Games-and-Simulations/sc-docker for more information.",
    url='https://github.com/Games-and-Simulations/sc-docker',
    author='Michal Sustr',
    author_email='michal.sustr@aic.fel.cvut.cz',
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 4 - Beta',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',

        # Pick your license as you wish
        'License :: OSI Approved :: MIT License',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 3.6',
    ],
    keywords='starcraft docker broodwar ai bot',
    install_requires=['requests',
                      'coloredlogs',
                      'numpy',
                      'tqdm',
                      'requests',
                      'python-dateutil'],
    packages=['scbw'],
    entry_points={  # Optional
        'console_scripts': [
            'scbw.play=scbw.cli:main',
        ],
    },
    python_requires='>=3.6',
    include_package_data=True,
    # cmdclass={
    #     'develop': PostDevelopCommand,
    #     'install': PostInstallCommand,
    # },
)
