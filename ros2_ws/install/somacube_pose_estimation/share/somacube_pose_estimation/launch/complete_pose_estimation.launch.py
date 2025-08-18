#!/usr/bin/env python3
"""
완전한 소마큐브 6DoF 포즈 추정 시스템 런치 파일
수학적 정밀 체계의 모든 단계를 통합 실행
"""

from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument, ExecuteProcess, TimerAction
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare
import os


def generate_launch_description():
    
    # Launch arguments
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Use simulation time'
    )
    
    camera_topics_prefix_arg = DeclareLaunchArgument(
        'camera_topics_prefix',
        default_value='/camera',
        description='Camera topics prefix'
    )
    
    debug_visualization_arg = DeclareLaunchArgument(
        'debug_visualization',
        default_value='true',
        description='Enable debug visualization'
    )
    
    # Package path
    pkg_somacube_pose_estimation = FindPackageShare('somacube_pose_estimation')
    
    # Configuration files
    config_dir = PathJoinSubstitution([pkg_somacube_pose_estimation, 'config'])
    camera_poses_config = PathJoinSubstitution([config_dir, 'camera_poses.yaml'])
    
    # 1. Camera Pose Manager - 카메라 위치 관리 및 글로벌 맵 구성
    camera_pose_manager_node = Node(
        package='somacube_pose_estimation',
        executable='camera_pose_manager_node.py',
        name='camera_pose_manager',
        parameters=[
            camera_poses_config,
            {'use_sim_time': LaunchConfiguration('use_sim_time')}
        ],
        output='screen'
    )
    
    # 2. YOLO Detector - 객체 검출
    yolo_detector_node = Node(
        package='somacube_pose_estimation',
        executable='yolo_detector_node.py',
        name='yolo_detector',
        parameters=[
            {
                'common.topics.rgb': [LaunchConfiguration('camera_topics_prefix'), '/color/image_raw'],
                'common.topics.camera_info': [LaunchConfiguration('camera_topics_prefix'), '/color/camera_info'],
                'use_sim_time': LaunchConfiguration('use_sim_time')
            }
        ],
        output='screen'
    )
    
    # 3. PointCloud Processor - 점군 전처리 및 세그멘테이션
    pointcloud_processor_node = Node(
        package='somacube_pose_estimation',
        executable='pointcloud_processor_node.py',
        name='pointcloud_processor',
        parameters=[
            {
                'common.topics.rgb': [LaunchConfiguration('camera_topics_prefix'), '/color/image_raw'],
                'common.topics.depth': [LaunchConfiguration('camera_topics_prefix'), '/aligned_depth_to_color/image_raw'],
                'common.topics.camera_info': [LaunchConfiguration('camera_topics_prefix'), '/color/camera_info'],
                'use_sim_time': LaunchConfiguration('use_sim_time')
            }
        ],
        output='screen'
    )
    
    # 4. PCA Axis Estimator - 주성분 분석 기반 축 추정
    pca_axis_estimator_node = Node(
        package='somacube_pose_estimation',
        executable='pca_axis_estimator_node.py',
        name='pca_axis_estimator',
        parameters=[
            {'use_sim_time': LaunchConfiguration('use_sim_time')}
        ],
        output='screen'
    )
    
    # 5. Manhattan Aligner - 맨해튼 정렬 및 자세 복원
    manhattan_aligner_node = Node(
        package='somacube_pose_estimation',
        executable='manhattan_aligner_node.py',
        name='manhattan_aligner',
        parameters=[
            {'use_sim_time': LaunchConfiguration('use_sim_time')}
        ],
        output='screen'
    )
    
    # 6. MultiView Fusion - 멀티뷰 융합
    multiview_fusion_node = Node(
        package='somacube_pose_estimation',
        executable='multiview_fusion_node.py',
        name='multiview_fusion',
        parameters=[
            {'use_sim_time': LaunchConfiguration('use_sim_time')}
        ],
        output='screen'
    )
    
    # 7. Visualization Node - 결과 시각화 (선택적)
    visualization_node = Node(
        package='somacube_pose_estimation',
        executable='visualization_node.py',
        name='pose_visualization',
        parameters=[
            {
                'debug_visualization': LaunchConfiguration('debug_visualization'),
                'use_sim_time': LaunchConfiguration('use_sim_time')
            }
        ],
        condition=LaunchConfiguration('debug_visualization'),
        output='screen'
    )
    
    # RViz for visualization
    rviz_config = PathJoinSubstitution([
        pkg_somacube_pose_estimation, 'rviz', 'pose_estimation_debug.rviz'
    ])
    
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config],
        parameters=[{'use_sim_time': LaunchConfiguration('use_sim_time')}],
        condition=LaunchConfiguration('debug_visualization'),
        output='screen'
    )
    
    # TF2 static transforms (if needed)
    # 카메라와 베이스 간 정적 변환 (실제 시스템에 맞게 수정 필요)
    tf_camera_to_base = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='camera_to_base_tf',
        arguments=['0', '0', '0', '0', '0', '0', 'base_link', 'camera_link']
    )
    
    return LaunchDescription([
        # Arguments
        use_sim_time_arg,
        camera_topics_prefix_arg,
        debug_visualization_arg,
        
        # Static TF
        tf_camera_to_base,
        
        # Core pipeline nodes (시작 순서 중요)
        camera_pose_manager_node,
        
        # 약간의 지연 후 센서 처리 노드들 시작
        TimerAction(
            period=2.0,
            actions=[
                yolo_detector_node,
                pointcloud_processor_node,
            ]
        ),
        
        # 추가 지연 후 분석 노드들 시작
        TimerAction(
            period=4.0,
            actions=[
                pca_axis_estimator_node,
                manhattan_aligner_node,
            ]
        ),
        
        # 마지막에 융합 노드 시작
        TimerAction(
            period=6.0,
            actions=[
                multiview_fusion_node,
            ]
        ),
        
        # 시각화 노드들 (조건부)
        TimerAction(
            period=8.0,
            actions=[
                visualization_node,
                rviz_node,
            ]
        ),
    ])