from setuptools import setup, find_packages

setup(
    name='crypto-dataflow',
    version='0.0.1',
    install_requires=[
        'apache-beam[gcp]==2.53.0',
        'requests',
        'pandas',
        'numpy'
    ],
    packages=[''],
    include_package_data=True,
)
