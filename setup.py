#!/usr/bin/env python

from setuptools import find_packages, setup

setup(
    name         = 'sibilla',
    version      = '2.1.0',
    description  = 'A companion to the cx_Oracle python libraries',
    author       = 'Gabriele N. Tornetta',
    author_email = 'gabriele.tornetta@avaloq.com',
    url          = 'https://github.com/P403n1x87/sibilla',


    classifiers=[  # Optional
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 5 - Stable',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Topic :: Software Development',

        # Pick your license as you wish
        'License :: GPL3',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 3.6',
    ],

    packages=find_packages(),

    install_requires=[
        'cx_Oracle',
    ],

    project_urls={
        'Bug Reports': 'https://github.com/P403n1x87/sibilla/issues'
    },
)
