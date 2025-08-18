from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'dsr_tests'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name), glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'm0609_block_assembly_rl'), 
         glob('dsr_tests/m0609_block_assembly_rl/*.py')),
        (os.path.join('share', package_name, 'm0609_block_assembly_rl'), 
         ['dsr_tests/m0609_block_assembly_rl/requirements.txt', 'dsr_tests/m0609_block_assembly_rl/README.md'])
    ],
    install_requires=[
        'setuptools',
        'torch>=2.0.0',
        'gymnasium>=0.29.0', 
        'numpy>=1.21.0',
        'matplotlib>=3.5.0',
        'pyyaml>=6.0',
        'tqdm>=4.64.0'
    ],
    zip_safe=True,
    maintainer='doosan-robotics',
    maintainer_email='minju3.lee@doosan.com',
    description='Doosan Robot System Tests including Block Assembly RL',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'm0609_train_rl = dsr_tests.m0609_block_assembly_rl.train:main',
            'm0609_evaluate_rl = dsr_tests.m0609_block_assembly_rl.evaluate:main',
        ],
    },
)
