from setuptools import find_packages, setup

setup(
    name         = 'sibilla',
    version      = '0.1.0',
    description  = 'Python ORM for the Oracle Database',
    author       = 'Gabriele N. Tornetta',
    author_email = 'phoenix1987@gmail.com',
    url          = 'https://github.com/P403n1x87/sibilla',

    classifiers=[
        'Development Status :: 5 - Stable',

        'Intended Audience :: Developers',
        'Topic :: Software Development',

        'License :: GPL3',

        'Programming Language :: Python :: 3.6',
    ],

    packages=find_packages(),

    install_requires=[
        'cx_Oracle',
        'cachetools',
    ],

    project_urls={
        'Bug Reports': 'https://github.com/P403n1x87/sibilla/issues'
    },
)
