from setuptools import find_packages, setup

package_name = "rokey"

# Read requirements from requirements.txt
def read_requirements():
    with open('requirements.txt', 'r') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name=package_name,
    version="1.0.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        ("share/" + package_name, [".env"]),
        ("share/" + package_name, ["requirements.txt"]),
        ("share/" + package_name, ["SPEECH_TO_TEXT_README.md"]),
        ("share/" + package_name, ["test_speech_to_text.sh"]),
    ],
    install_requires=read_requirements(),
    zip_safe=True,
    maintainer="juwan",
    maintainer_email="dlacksdn352@gmail.com",
    description="ROKEY BOOT CAMP Package with Korean Speech-to-Text",
    license="Apache 2.0 License",
    entry_points={
        "console_scripts": [
            # Original ROKEY commands
            "simple_amove=rokey.basic.amove_test:main",
            "force_control = rokey.basic.force_control:main",
            "get_current_pos=rokey.basic.get_current_pos:main",
            "getting_position = rokey.basic.getting_position:main",
            "grip=rokey.basic.grip:main",
            "jog = rokey.basic.jog_complete:main",
            "move_periodic = rokey.basic.move_periodic:main",
            "simple_move=rokey.basic.move:main",
            "simple_movesx=rokey.basic.movesx_test:main",
            "data_recording=rokey.basic.data_recording:main",
            
            # Speech-to-Text commands
            "rokey-speech=rokey.speech_to_text:main",
            "rokey-test=rokey.start_signal_test:main",
            "rokey-speech-test=rokey.speech_test_launcher:main",
            
            # Backward compatibility
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
    ],
    python_requires=">=3.8",
    keywords="ros2 speech-to-text korean whisper openai robotics",
    long_description=open("SPEECH_TO_TEXT_README.md").read(),
    long_description_content_type="text/markdown",
)
