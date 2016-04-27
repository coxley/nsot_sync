#!/usr/bin/env python

from setuptools import setup, find_packages

VERSION = '0.5'

setup(
    name='nsot_sync',
    version=VERSION,
    description="CLI/Driver-based framework to sync resources to NSoT (IPAM)",
    author='Codey Oxley',
    author_email='codey.a.oxley+os@gmail.com',
    url='https://github.com/coxley/nsot_sync',
    keywords=['networking', 'ipam', 'nsot', 'cmdb', 'sync', 'orion',
              'solarwinds', 'infoblox', 'ip', 'address'],
    classifiers=[],
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'pynsot==0.22.2',
        'netifaces==0.10.4',
        'coloredlogs==5.0',
    ],
    extras_require={
        'docs': ['sphinx', 'sphinx-autobuild', 'sphinx-rtd-theme'],
        'tests': ['pytest'],
    },
    tests_require=['pytest'],
    setup_requires=['pytest-runner'],
    entry_points='''
        [console_scripts]
        nsot_sync=nsot_sync.cli:main
    ''',
)
