from setuptools import find_packages, setup

setup(
    name='sibilla',
    version='0.1.0',
    description='Python ORM for the Oracle Database',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='Gabriele N. Tornetta',
    author_email='phoenix1987@gmail.com',
    url='https://github.com/P403n1x87/sibilla',

    classifiers=[
        'Development Status :: 4 - Beta',

        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Intended Audience :: Financial and Insurance Industry',

        'Topic :: Database',
        'Topic :: Software Development',

        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',

        'Programming Language :: Python :: 3.6',
    ],

    packages=find_packages(),

    install_requires=[
        'cx_Oracle',
        'cachetools',
    ],

    tests_require=[
        'pandas',
    ],

    project_urls={
        'Bug Reports': 'https://github.com/P403n1x87/sibilla/issues',
        'Source': 'https://github.com/P403n1x87/sibilla',
    },
)
