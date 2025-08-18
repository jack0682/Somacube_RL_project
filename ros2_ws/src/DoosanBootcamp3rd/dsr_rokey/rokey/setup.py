from setuptools import find_packages, setup

package_name = "rokey"

# Read requirements from requirements.txt
def read_requirements():
    with open('requirements.txt', 'r') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name=package_name,
    version="2.0.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        ("share/" + package_name, ["requirements.txt"]),
        ("share/" + package_name, ["ROKEY_STT_README.md"]),
        ("share/" + package_name, ["install_rokey_stt.sh"]),
        ("share/" + package_name, ["test_rokey_stt.sh"]),
    ],
    install_requires=read_requirements(),
    zip_safe=True,
    maintainer="juwan",
    maintainer_email="dlacksdn352@gmail.com",
    description="ROKEY Korean Speech-to-Text Package - Production Ready STT System",
    license="Apache 2.0 License",
    entry_points={
        "console_scripts": [
            # Primary STT commands
            "rokey-stt=rokey.speech_to_text:main",
            "rokey-trigger=rokey.start_signal_test:main",
            "rokey-test=rokey.speech_test_launcher:main",
            
            # Backward compatibility
            "rokey-speech=rokey.speech_to_text:main",
            "speech_to_text=rokey.speech_to_text:main",
            "start_signal_test=rokey.start_signal_test:main"
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Multimedia :: Sound/Audio :: Speech",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    keywords="ros2 speech-to-text korean whisper openai robotics stt production",
    long_description=open("ROKEY_STT_README.md").read(),
    long_description_content_type="text/markdown",
)
