from setuptools import setup, find_packages

VERSION = '0.4.6'

setup(
    name='nsot_sync',
    version=VERSION,
    description="CLI/Driver-based framework to sync resources to NSoT (IPAM)",
    author='Codey Oxley',
    author_email='codey.a.oxley+os@gmail.com',
    url='https://github.com/coxley/nsot_sync',
    download_url='https://github.com/coxley/nsot_sync/tarball/%s' % VERSION,
    keywords=['networking', 'ipam', 'nsot', 'cmdb', 'sync', 'orion',
              'solarwinds', 'infoblox', 'ip', 'address'],
    classifiers=[],
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Click==6.2',
        'pynsot==0.18.2',
        'netifaces==0.10.4',
        'IPy==0.83',
        'coloredlogs==5.0',
    ],
    extras_require={
        'docs': ['sphinx', 'sphinx-autobuild', 'sphinx-rtd-theme'],
    },
    tests_require=['pytest'],
    setup_requires=['pytest-runner'],
    entry_points='''
        [console_scripts]
        nsot_sync=nsot_sync.cli:main
    ''',
)
