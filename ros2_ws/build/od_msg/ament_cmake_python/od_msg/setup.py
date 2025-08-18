from setuptools import find_packages
from setuptools import setup

setup(
    name='od_msg',
    version='0.0.0',
    packages=find_packages(
        include=('od_msg', 'od_msg.*')),
)
