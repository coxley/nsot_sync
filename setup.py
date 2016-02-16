from setuptools import setup, find_packages

setup(
    name='nsot_sync',
    version='0.1',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Click',
        'pynsot',
        'netifaces',
        'IPy',
    ],
    tests_require=['pytest'],
    setup_requires=['pytest-runner'],
    entry_points='''
        [console_scripts]
        nsot_sync=nsot_sync.cli:main
    ''',
)
