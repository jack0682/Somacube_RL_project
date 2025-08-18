import os

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, FindExecutable, PathJoinSubstitution, LaunchConfiguration

from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    # Declare arguments
    declared_arguments = [
        DeclareLaunchArgument(
            "model",
            default_value="m0609",
            description="Robot model (e.g., m0609, a0509)",
        ),
        DeclareLaunchArgument(
            "use_sim_time",
            default_value="true",
            description="Use simulation (Gazebo) clock if true",
        ),
        DeclareLaunchArgument(
            "world",
            default_value="soma_cube_assembly.world",
            description="Gazebo world file to load",
        ),
    ]

    # Get robot description (URDF/XACRO)
    robot_description_content = Command(
        [
            PathJoinSubstitution([FindExecutable(name="xacro")]),
            " ",
            PathJoinSubstitution(
                [
                    FindPackageShare("dsr_description2"),
                    "urdf",
                    LaunchConfiguration("model"),
                ]
            ),
            ".xacro",
            " ",
            "use_gazebo:=true",
            " ",
            "color:=white", # Default color for simulation
        ]
    )
    robot_description = {"robot_description": robot_description_content}

    # Launch Gazebo
    gazebo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [FindPackageShare("ros_gz_sim"), "/launch/gz_sim.launch.py"]
        ),
        launch_arguments={
            "gz_args": [" -r -v 3 ", PathJoinSubstitution([FindPackageShare("somacube"), "worlds", LaunchConfiguration("world")])]
        }.items(),
    )

    # Spawn robot in Gazebo
    gz_spawn_entity = Node(
        package="ros_gz_sim",
        executable="create",
        output="screen",
        arguments=[
            "-topic", "robot_description",
            "-name", LaunchConfiguration("model"),
            "-allow_renaming", "true",
            "-x", "0", "-y", "0", "-z", "0",
            "-R", "0", "-P", "0", "-Y", "0",
        ],
    )

    # Robot State Publisher
    node_robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="screen",
        parameters=[robot_description, {"use_sim_time": LaunchConfiguration("use_sim_time")}],
    )

    # Controller Spawners
    joint_state_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster", "--controller-manager", "controller_manager"],
    )

    dsr_position_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["dsr_position_controller", "--controller-manager", "controller_manager"],
    )

    # Launch the main assembly node
    rl_with_robot_node = Node(
        package="somacube",
        executable="RL_with_robot2",
        name="soma_cube_assembly_node",
        output="screen",
        parameters=[{"use_sim_time": LaunchConfiguration("use_sim_time")}],
    )

    return LaunchDescription(declared_arguments + [
        gazebo_launch,
        node_robot_state_publisher,
        gz_spawn_entity,
        joint_state_broadcaster_spawner,
        dsr_position_controller_spawner,
        rl_with_robot_node,
    ])