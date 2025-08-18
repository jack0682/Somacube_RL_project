#!/usr/bin/env python3
"""
Standalone virtual training launch - no external dependencies
"""

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    
    # Simple M0609 robot description embedded directly
    robot_description = """
<?xml version="1.0"?>
<robot name="m0609">
  <link name="base_link">
    <visual>
      <geometry>
        <box size="0.2 0.2 0.1"/>
      </geometry>
      <material name="blue">
        <color rgba="0 0 1 0.8"/>
      </material>
    </visual>
  </link>
  
  <link name="link1">
    <visual>
      <geometry>
        <cylinder radius="0.05" length="0.1"/>
      </geometry>
      <material name="gray">
        <color rgba="0.5 0.5 0.5 1"/>
      </material>
    </visual>
  </link>
  
  <joint name="joint1" type="revolute">
    <parent link="base_link"/>
    <child link="link1"/>
    <origin xyz="0 0 0.05"/>
    <axis xyz="0 0 1"/>
    <limit lower="-3.14" upper="3.14" effort="100" velocity="1.57"/>
  </joint>
  
  <link name="link2">
    <visual>
      <geometry>
        <box size="0.08 0.06 0.2"/>
      </geometry>
      <material name="gray">
        <color rgba="0.5 0.5 0.5 1"/>
      </material>
    </visual>
  </link>
  
  <joint name="joint2" type="revolute">
    <parent link="link1"/>
    <child link="link2"/>
    <origin xyz="0 0 0.1"/>
    <axis xyz="0 1 0"/>
    <limit lower="-1.57" upper="1.57" effort="100" velocity="1.57"/>
  </joint>
  
  <link name="link3">
    <visual>
      <geometry>
        <box size="0.06 0.06 0.15"/>
      </geometry>
      <material name="gray">
        <color rgba="0.5 0.5 0.5 1"/>
      </material>
    </visual>
  </link>
  
  <joint name="joint3" type="revolute">
    <parent link="link2"/>
    <child link="link3"/>
    <origin xyz="0 0 0.15"/>
    <axis xyz="0 1 0"/>
    <limit lower="-1.57" upper="1.57" effort="100" velocity="1.57"/>
  </joint>
  
  <link name="link4">
    <visual>
      <geometry>
        <cylinder radius="0.03" length="0.1"/>
      </geometry>
      <material name="gray">
        <color rgba="0.5 0.5 0.5 1"/>
      </material>
    </visual>
  </link>
  
  <joint name="joint4" type="revolute">
    <parent link="link3"/>
    <child link="link4"/>
    <origin xyz="0 0 0.1"/>
    <axis xyz="1 0 0"/>
    <limit lower="-3.14" upper="3.14" effort="50" velocity="1.57"/>
  </joint>
  
  <link name="link5">
    <visual>
      <geometry>
        <box size="0.05 0.05 0.08"/>
      </geometry>
      <material name="gray">
        <color rgba="0.5 0.5 0.5 1"/>
      </material>
    </visual>
  </link>
  
  <joint name="joint5" type="revolute">
    <parent link="link4"/>
    <child link="link5"/>
    <origin xyz="0 0 0.08"/>
    <axis xyz="0 1 0"/>
    <limit lower="-1.57" upper="1.57" effort="50" velocity="1.57"/>
  </joint>
  
  <link name="link6">
    <visual>
      <geometry>
        <cylinder radius="0.02" length="0.05"/>
      </geometry>
      <material name="red">
        <color rgba="1 0 0 1"/>
      </material>
    </visual>
  </link>
  
  <joint name="joint6" type="revolute">
    <parent link="link5"/>
    <child link="link6"/>
    <origin xyz="0 0 0.05"/>
    <axis xyz="0 0 1"/>
    <limit lower="-3.14" upper="3.14" effort="25" velocity="1.57"/>
  </joint>
  
  <link name="tcp">
    <visual>
      <geometry>
        <sphere radius="0.01"/>
      </geometry>
      <material name="green">
        <color rgba="0 1 0 1"/>
      </material>
    </visual>
  </link>
  
  <joint name="tcp_joint" type="fixed">
    <parent link="link6"/>
    <child link="tcp"/>
    <origin xyz="0 0 0.03"/>
  </joint>
</robot>
"""
    
    return LaunchDescription([
        
        # Robot State Publisher
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            output='screen',
            parameters=[
                {
                    'robot_description': robot_description,
                    'publish_frequency': 50.0,
                }
            ],
            arguments=['--ros-args', '--log-level', 'warn']
        ),
        
        # Virtual Soma Cube Simulation
        Node(
            package='doosan_somacube_rl',
            executable='virtual_soma_cube_training.py',
            name='virtual_somacube_sim',
            output='screen',
            arguments=['--ros-args', '--log-level', 'info']
        ),
        
        # RViz2 for visualization
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=['-d', '/home/jack/ros2_ws/soma_cube_rviz_config.rviz'],
            output='screen'
        ),
    ])