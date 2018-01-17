"""
Starcraft BW docker launcher.
"""

from scbw import VERSION
# Always prefer setuptools over distutils
from setuptools import setup

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
    extras_require={
    },
    packages=['scbw'],
    entry_points={  # Optional
        'console_scripts': [
            'scbw=scbw.cli:main',
        ],
    },
    python_requires='>=3.6',

    data_files=[('scbw_local_docker', ['scbw/local_docker/game.dockerfile',
                                       'scbw/local_docker/default.mpc',
                                       'scbw/local_docker/default.spc',
                                       ])
                ]
)
