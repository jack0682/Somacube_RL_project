from setuptools import find_packages
from setuptools import setup

setup(
    name='doosan_somacube_rl',
    version='1.0.0',
    packages=find_packages(
        include=('doosan_somacube_rl', 'doosan_somacube_rl.*')),
)
