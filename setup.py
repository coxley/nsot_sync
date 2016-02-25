from setuptools import setup, find_packages

setup(
    name='nsot_sync',
    version='0.3',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Click==6.2',
        'pynsot==0.18.2',
        'netifaces==0.10.4',
        'IPy==0.83',
        'coloredlogs==5.0',
    ],
    tests_require=['pytest'],
    setup_requires=['pytest-runner'],
    entry_points='''
        [console_scripts]
        nsot_sync=nsot_sync.cli:main
    ''',
)
