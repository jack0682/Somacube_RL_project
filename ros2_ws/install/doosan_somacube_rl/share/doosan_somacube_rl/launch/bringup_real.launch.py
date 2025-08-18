#!/usr/bin/env python3

import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def launch_setup(context, *args, **kwargs):
    # Parameters
    params_file = LaunchConfiguration('params').perform(context)
    if not os.path.isabs(params_file):
        params_file = PathJoinSubstitution([
            FindPackageShare('doosan_somacube_rl'),
            'config', params_file
        ]).perform(context)
    
    # Launch order: preprocess → register → tracker → safety → control → manager → sequencer → logger → policy
    nodes = []
    
    # Core processing pipeline
    nodes.extend([
        Node(
            package='doosan_somacube_rl',
            executable='pc_preprocess_node.py',
            name='pc_preprocess',
            parameters=[params_file],
            output='screen'
        ),
        Node(
            package='doosan_somacube_rl',
            executable='pc_register_node.py',
            name='pc_register',
            parameters=[params_file],
            output='screen'
        ),
        Node(
            package='doosan_somacube_rl',
            executable='pose_tracker_node.py',
            name='pose_tracker',
            parameters=[params_file],
            output='screen'
        ),
    ])
    
    # Safety and control
    nodes.extend([
        Node(
            package='doosan_somacube_rl',
            executable='safety_monitor_node.py',
            name='safety_monitor',
            parameters=[params_file],
            output='screen'
        ),
        Node(
            package='doosan_somacube_rl',
            executable='imp_ctrl_node.py',
            name='imp_ctrl',
            parameters=[params_file],
            output='screen'
        ),
    ])
    
    # High-level management
    nodes.extend([
        Node(
            package='doosan_somacube_rl',
            executable='layer1_manager_node.py',
            name='layer1_manager',
            parameters=[params_file],
            output='screen'
        ),
        Node(
            package='doosan_somacube_rl',
            executable='sequencer_node.py',
            name='sequencer',
            parameters=[params_file],
            output='screen'
        ),
        Node(
            package='doosan_somacube_rl',
            executable='logger_node.py',
            name='logger',
            parameters=[params_file],
            output='screen'
        ),
    ])
    
    # RL policy (shadow mode)
    nodes.append(
        Node(
            package='doosan_somacube_rl',
            executable='policy_sac_low_node.py',
            name='policy_sac_low',
            parameters=[params_file],
            output='screen'
        )
    )
    
    return nodes


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'params',
            default_value='rl_somacube_params.yaml',
            description='Parameters file name (relative to config/ directory)'
        ),
        OpaqueFunction(function=launch_setup)
    ])