#!/usr/bin/env python3

# Launch file to run both speech-to-text and test nodes together
# This makes it easy to test the complete functionality

# Import launch system components
from launch import LaunchDescription
# Import launch node action for starting ROS2 nodes
from launch_ros.actions import Node


def generate_launch_description():
    """
    Generate launch description for running speech-to-text with test subscriber.
    
    Returns:
        LaunchDescription: Launch configuration for both nodes
    """
    return LaunchDescription([
        # Launch the main speech-to-text node
        Node(
            package='rokey',                    # Package name
            executable='speech_to_text',        # Executable name from setup.py
            name='speech_to_text_node',        # Node name
            output='screen',                   # Output to terminal
            emulate_tty=True,                  # Enable colored output
            parameters=[],                     # No additional parameters
        ),
        
        # Launch the start signal test node
        Node(
            package='rokey',                    # Package name
            executable='start_signal_test',     # Executable name from setup.py
            name='start_signal_test_node',     # Node name
            output='screen',                   # Output to terminal
            emulate_tty=True,                  # Enable colored output
            parameters=[],                     # No additional parameters
        ),
    ])