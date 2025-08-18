#!/usr/bin/env python3
"""
글로벌 맵핑 시스템 런치 파일
SLAM 없는 정밀한 RGB-Depth 동기 캡처 및 글로벌 맵 구성
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
    
    realsense_config_arg = DeclareLaunchArgument(
        'realsense_config',
        default_value='true',
        description='Launch RealSense camera with optimal settings'
    )
    
    enable_capture_arg = DeclareLaunchArgument(
        'enable_capture',
        default_value='true',
        description='Enable synchronized capture'
    )
    
    data_directory_arg = DeclareLaunchArgument(
        'data_directory',
        default_value='/tmp/somacube_global_mapping',
        description='Directory for captured data'
    )
    
    # Package path
    pkg_somacube = FindPackageShare('somacube_pose_estimation')
    
    # Configuration files
    config_dir = PathJoinSubstitution([pkg_somacube, 'config'])
    camera_poses_config = PathJoinSubstitution([config_dir, 'camera_poses.yaml'])
    params_config = PathJoinSubstitution([config_dir, 'somacube_params.yaml'])
    
    # RealSense camera with optimal settings for global mapping
    realsense_node = Node(
        package='realsense2_camera',
        executable='realsense2_camera_node',
        name='realsense2_camera',
        parameters=[{
            # 동기화를 위한 핵심 설정들
            'align_depth.enable': True,           # Depth를 RGB에 정렬
            'enable_sync': True,                  # 센서 간 동기화
            'publish_metadata': True,             # HW 타임스탬프 포함
            
            # 이미지 해상도 및 주파수 (D435i 최적화)
            'color.width': 640,
            'color.height': 480,
            'color.fps': 30,
            'depth.width': 640,
            'depth.height': 480,
            'depth.fps': 30,
            'infra.width': 640,
            'infra.height': 480,
            
            # 깊이 필터링 (계획서의 요구사항)
            'temporal_filter.enable': True,       # 시간 필터
            'spatial_filter.enable': True,        # 공간 필터
            'hole_filling_filter.enable': True,   # 홀 채움
            'decimation_filter.enable': False,    # 동기화를 위해 비활성화
            
            # 자동 노출/화이트 밸런스 제어
            'color.enable_auto_exposure': False,  # AE 잠금
            'color.enable_auto_white_balance': False,  # WB 잠금
            'color.exposure': 8000,  # 고정 노출값 (마이크로초)
            
            # 기타 안정성 설정
            'enable_infra1': False,
            'enable_infra2': False,
            'enable_gyro': False,
            'enable_accel': False,
            
            'use_sim_time': LaunchConfiguration('use_sim_time')
        }],
        condition=LaunchConfiguration('realsense_config'),
        output='screen'
    )
    
    # 카메라 포즈 매니저 - 미리 정의된 포즈 관리
    camera_pose_manager_node = Node(
        package='somacube_pose_estimation',
        executable='camera_pose_manager_node.py',
        name='camera_pose_manager',
        parameters=[
            camera_poses_config,
            {
                'camera_pose_manager.auto_tf_broadcast': True,
                'camera_pose_manager.global_map_frame': 'world',
                'use_sim_time': LaunchConfiguration('use_sim_time')
            }
        ],
        output='screen'
    )
    
    # 동기화된 캡처 노드 - 핵심 구성요소
    synchronized_capture_node = Node(
        package='somacube_pose_estimation',
        executable='synchronized_capture_node.py',
        name='synchronized_capture',
        parameters=[
            {
                'synchronized_capture.data_dir': LaunchConfiguration('data_directory'),
                
                # 계획서의 동기화 파라미터
                'synchronized_capture.sync.target_delta_ms': 2.5,
                'synchronized_capture.sync.max_delta_ms': 10.0,
                'synchronized_capture.sync.settle_time_ms': 150.0,
                'synchronized_capture.sync.frame_composite_count': 5,
                
                # 품질 설정
                'synchronized_capture.quality.enable_ae_lock': True,
                'synchronized_capture.quality.enable_wb_lock': True,
                'synchronized_capture.quality.depth_temporal_filter': True,
                
                # TSDF 설정
                'synchronized_capture.tsdf.enable': True,
                'synchronized_capture.tsdf.voxel_size_mm': 6.0,
                'synchronized_capture.tsdf.trunc_distance_factor': 3.0,
                
                # 토픽 설정
                'common.topics.rgb': [LaunchConfiguration('camera_topics_prefix'), '/color/image_raw'],
                'common.topics.depth': [LaunchConfiguration('camera_topics_prefix'), '/aligned_depth_to_color/image_raw'],
                'common.topics.camera_info': [LaunchConfiguration('camera_topics_prefix'), '/color/camera_info'],
                
                'use_sim_time': LaunchConfiguration('use_sim_time')
            }
        ],
        condition=LaunchConfiguration('enable_capture'),
        output='screen'
    )
    
    # YOLO 검출기 (선택적)
    yolo_detector_node = Node(
        package='somacube_pose_estimation',
        executable='yolo_detector_node.py',
        name='yolo_detector',
        parameters=[
            {
                'common.topics.rgb': '/synchronized_capture/rgb',  # 동기화된 RGB 사용
                'common.topics.camera_info': [LaunchConfiguration('camera_topics_prefix'), '/color/camera_info'],
                'yolo_detector.processing_rate_hz': 10.0,  # 글로벌 맵핑용으로 빈도 낮춤
                'use_sim_time': LaunchConfiguration('use_sim_time')
            }
        ],
        output='screen'
    )
    
    # 포인트클라우드 처리기 (동기화된 데이터 사용)
    pointcloud_processor_node = Node(
        package='somacube_pose_estimation',
        executable='pointcloud_processor_node.py',
        name='pointcloud_processor',
        parameters=[
            {
                'common.topics.rgb': '/synchronized_capture/rgb',
                'common.topics.depth': '/synchronized_capture/depth',
                'common.topics.camera_info': [LaunchConfiguration('camera_topics_prefix'), '/color/camera_info'],
                
                # 글로벌 맵핑 최적화 설정
                'pointcloud_processor.global_map.enable': True,
                'pointcloud_processor.global_map.voxel_size_m': 0.005,  # 5mm 정밀도
                'pointcloud_processor.global_map.max_points': 10000000,  # 1천만 포인트
                
                'use_sim_time': LaunchConfiguration('use_sim_time')
            }
        ],
        output='screen'
    )
    
    # 캡처 제어 인터페이스 (간단한 GUI 또는 CLI)
    capture_control_node = Node(
        package='somacube_pose_estimation',
        executable='capture_control_interface.py',
        name='capture_control',
        parameters=[
            {'use_sim_time': LaunchConfiguration('use_sim_time')}
        ],
        output='screen'
    )
    
    # TF 정적 변환들
    # 베이스에서 월드로의 변환 (world ≡ base)
    tf_base_to_world = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='base_to_world_tf',
        arguments=['0', '0', '0', '0', '0', '0', 'base_link', 'world']
    )
    
    # RViz 시각화 설정
    rviz_config = PathJoinSubstitution([
        pkg_somacube, 'rviz', 'global_mapping_debug.rviz'
    ])
    
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2_global_mapping',
        arguments=['-d', rviz_config],
        parameters=[{'use_sim_time': LaunchConfiguration('use_sim_time')}],
        output='screen'
    )
    
    # rqt 플러그인들 (모니터링용)
    rqt_image_view = Node(
        package='rqt_image_view',
        executable='rqt_image_view',
        name='rqt_image_view',
        arguments=['/synchronized_capture/rgb'],
        output='screen'
    )
    
    return LaunchDescription([
        # Arguments
        use_sim_time_arg,
        camera_topics_prefix_arg,
        realsense_config_arg,
        enable_capture_arg,
        data_directory_arg,
        
        # Static TF
        tf_base_to_world,
        
        # Core system nodes
        TimerAction(
            period=1.0,
            actions=[realsense_node]
        ),
        
        TimerAction(
            period=3.0,
            actions=[camera_pose_manager_node]
        ),
        
        TimerAction(
            period=5.0,
            actions=[synchronized_capture_node]
        ),
        
        # Processing nodes
        TimerAction(
            period=7.0,
            actions=[
                yolo_detector_node,
                pointcloud_processor_node,
            ]
        ),
        
        # Interface and visualization
        TimerAction(
            period=9.0,
            actions=[
                capture_control_node,
                rviz_node,
            ]
        ),
        
        # Optional monitoring tools
        TimerAction(
            period=11.0,
            actions=[rqt_image_view]
        ),
    ])