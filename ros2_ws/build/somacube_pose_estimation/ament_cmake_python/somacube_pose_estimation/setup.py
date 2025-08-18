from setuptools import find_packages
from setuptools import setup

setup(
    name='somacube_pose_estimation',
    version='1.0.0',
    packages=find_packages(
        include=('somacube_pose_estimation', 'somacube_pose_estimation.*')),
)
