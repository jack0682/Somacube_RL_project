#!/usr/bin/env python3
"""
DoosanRobotics M0609 + Intel RealSense D435i를 위한 소마큐브 포즈 추정 런치 파일
실제 로봇 환경과 작업 영역에 최적화된 설정
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
    
    robot_ip_arg = DeclareLaunchArgument(
        'robot_ip',
        default_value='192.168.137.100',
        description='DoosanRobotics M0609 IP address'
    )
    
    realsense_serial_arg = DeclareLaunchArgument(
        'realsense_serial',
        default_value='',
        description='RealSense D435i serial number'
    )
    
    enable_capture_arg = DeclareLaunchArgument(
        'enable_capture',
        default_value='true',
        description='Enable synchronized capture'
    )
    
    data_directory_arg = DeclareLaunchArgument(
        'data_directory',
        default_value='/tmp/doosan_soma_cube_data',
        description='Directory for captured data'
    )
    
    # Package path
    pkg_somacube = FindPackageShare('somacube_pose_estimation')
    
    # Configuration files
    config_dir = PathJoinSubstitution([pkg_somacube, 'config'])
    camera_poses_config = PathJoinSubstitution([config_dir, 'camera_poses.yaml'])
    params_config = PathJoinSubstitution([config_dir, 'somacube_params.yaml'])
    
    # Intel RealSense D435i with DoosanRobotics M0609 optimized settings
    realsense_node = Node(
        package='realsense2_camera',
        executable='realsense2_camera_node',
        name='realsense2_camera',
        parameters=[{
            # DoosanRobotics M0609 작업 영역 최적화 설정
            'align_depth.enable': True,
            'enable_sync': True,
            'publish_metadata': True,
            
            # D435i 해상도 (작업 영역: 75mm x 75mm 고해상도 필요)
            'color.width': 640,
            'color.height': 480,
            'color.fps': 30,
            'depth.width': 640,
            'depth.height': 480,
            'depth.fps': 30,
            
            # 정밀 작업을 위한 깊이 필터링
            'temporal_filter.enable': True,
            'spatial_filter.enable': True,
            'hole_filling_filter.enable': True,
            'decimation_filter.enable': False,  # 해상도 유지
            
            # 안정적인 RGB 설정
            'color.enable_auto_exposure': True,  # 조명 변화 대응
            'color.enable_auto_white_balance': True,
            
            # IMU 비활성화 (정적 환경)
            'enable_gyro': False,
            'enable_accel': False,
            'enable_infra1': False,
            'enable_infra2': False,
            
            # 시리얼 번호 설정 (필요시)
            'serial_no': LaunchConfiguration('realsense_serial'),
            
            'use_sim_time': LaunchConfiguration('use_sim_time')
        }],
        output='screen'
    )
    
    # DoosanRobotics M0609 카메라 포즈 매니저
    camera_pose_manager_node = Node(
        package='somacube_pose_estimation',
        executable='camera_pose_manager_node.py',
        name='camera_pose_manager',
        parameters=[
            camera_poses_config,
            {
                'camera_pose_manager.auto_tf_broadcast': True,
                'camera_pose_manager.global_map_frame': 'base_link',  # M0609 베이스
                'camera_pose_manager.robot_model': 'DoosanRobotics_M0609',
                'camera_pose_manager.calibration_file': '/home/jack/ros2_ws/src/DoosanBootcamp3rd/dsr_rokey/pick_and_place_text/resource/T_gripper2camera.npy',
                'use_sim_time': LaunchConfiguration('use_sim_time')
            }
        ],
        output='screen'
    )
    
    # 동기화된 캡처 노드 (M0609 작업 영역 특화)
    synchronized_capture_node = Node(
        package='somacube_pose_estimation',
        executable='synchronized_capture_node.py',
        name='synchronized_capture',
        parameters=[
            {
                'synchronized_capture.data_dir': LaunchConfiguration('data_directory'),
                
                # M0609 작업 영역 최적화 동기화 파라미터
                'synchronized_capture.sync.target_delta_ms': 2.0,    # 높은 정밀도
                'synchronized_capture.sync.max_delta_ms': 8.0,      # 엄격한 기준
                'synchronized_capture.sync.settle_time_ms': 100.0,  # 빠른 응답
                'synchronized_capture.sync.frame_composite_count': 3, # 빠른 처리
                
                # 품질 설정
                'synchronized_capture.quality.enable_ae_lock': False,  # 자동 조절 허용
                'synchronized_capture.quality.enable_wb_lock': False,
                'synchronized_capture.quality.depth_temporal_filter': True,
                
                # 작은 작업 영역을 위한 TSDF 설정
                'synchronized_capture.tsdf.enable': True,
                'synchronized_capture.tsdf.voxel_size_mm': 2.0,     # 높은 해상도
                'synchronized_capture.tsdf.trunc_distance_factor': 2.0,
                
                # 토픽 설정
                'common.topics.rgb': '/camera/color/image_raw',
                'common.topics.depth': '/camera/aligned_depth_to_color/image_raw',
                'common.topics.camera_info': '/camera/color/camera_info',
                
                'use_sim_time': LaunchConfiguration('use_sim_time')
            }
        ],
        condition=LaunchConfiguration('enable_capture'),
        output='screen'
    )
    
    # YOLO 검출기 (소마큐브 조각 검출)
    yolo_detector_node = Node(
        package='somacube_pose_estimation',
        executable='yolo_detector_node.py',
        name='yolo_detector',
        parameters=[
            {
                'common.topics.rgb': '/synchronized_capture/rgb',
                'common.topics.camera_info': '/camera/color/camera_info',
                'yolo_detector.processing_rate_hz': 15.0,  # M0609 작업 속도에 맞춤
                'yolo_detector.confidence_threshold': 0.7,  # 높은 신뢰도
                'yolo_detector.model_path': 'models/somacube_best.pt',
                'use_sim_time': LaunchConfiguration('use_sim_time')
            }
        ],
        output='screen'
    )
    
    # 포인트클라우드 처리기 (M0609 작업 영역 특화)
    pointcloud_processor_node = Node(
        package='somacube_pose_estimation',
        executable='pointcloud_processor_node.py',
        name='pointcloud_processor',
        parameters=[
            {
                'common.topics.rgb': '/synchronized_capture/rgb',
                'common.topics.depth': '/synchronized_capture/depth',
                'common.topics.camera_info': '/camera/color/camera_info',
                
                # 작은 작업 영역 최적화 설정
                'pointcloud_processor.segmentation.min_cluster_size': 50,
                'pointcloud_processor.segmentation.max_cluster_size': 2000,
                'pointcloud_processor.preprocessing.voxel_size_m': 0.002,  # 2mm
                
                # 글로벌 맵핑 설정
                'pointcloud_processor.global_map.enable': True,
                'pointcloud_processor.global_map.voxel_size_m': 0.001,  # 1mm 정밀도
                'pointcloud_processor.global_map.max_points': 5000000,
                
                'use_sim_time': LaunchConfiguration('use_sim_time')
            }
        ],
        output='screen'
    )
    
    # PCA 축 추정기
    pca_axis_estimator_node = Node(
        package='somacube_pose_estimation',
        executable='pca_axis_estimator_node.py',
        name='pca_axis_estimator',
        parameters=[
            {
                # 소마큐브 조각 크기에 맞춘 PCA 설정
                'pca_axis_estimator.pca.primary_dominance_threshold': 0.7,
                'pca_axis_estimator.pca.linearity_ratio_threshold': 2.0,
                'use_sim_time': LaunchConfiguration('use_sim_time')
            }
        ],
        output='screen'
    )
    
    # 맨해튼 정렬기
    manhattan_aligner_node = Node(
        package='somacube_pose_estimation',
        executable='manhattan_aligner_node.py',
        name='manhattan_aligner',
        parameters=[
            {
                'manhattan_aligner.alignment.score_threshold': 0.6,
                'use_sim_time': LaunchConfiguration('use_sim_time')
            }
        ],
        output='screen'
    )
    
    # 멀티뷰 융합
    multiview_fusion_node = Node(
        package='somacube_pose_estimation',
        executable='multiview_fusion_node.py',
        name='multiview_fusion',
        parameters=[
            {
                'multiview_fusion.convergence.min_views': 3,
                'multiview_fusion.convergence.max_position_change_m': 0.005,  # 5mm
                'multiview_fusion.convergence.max_rotation_change_deg': 2.0,
                'use_sim_time': LaunchConfiguration('use_sim_time')
            }
        ],
        output='screen'
    )
    
    # 시각화
    visualization_node = Node(
        package='somacube_pose_estimation',
        executable='visualization_node.py',
        name='visualization',
        parameters=[
            {
                'visualization.update_rate_hz': 10.0,
                'use_sim_time': LaunchConfiguration('use_sim_time')
            }
        ],
        output='screen'
    )
    
    # DoosanRobotics M0609 제어 인터페이스
    capture_control_node = Node(
        package='somacube_pose_estimation',
        executable='capture_control_interface.py',
        name='capture_control',
        parameters=[
            {
                'capture_control.interface_mode': 'cli',
                'capture_control.poses_per_session': 8,  # M0609 8개 포즈
                'use_sim_time': LaunchConfiguration('use_sim_time')
            }
        ],
        output='screen'
    )
    
    # TF 정적 변환들 (DoosanRobotics M0609 특화)
    # base_link가 로봇의 베이스이므로 world와 동일하게 설정
    tf_base_to_world = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='base_to_world_tf',
        arguments=['0', '0', '0', '0', '0', '0', 'base_link', 'world']
    )
    
    # 작업 영역 중앙을 표시하는 TF (참조용)
    tf_workspace_center = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='workspace_center_tf',
        arguments=['0.462', '0.041', '0.012', '0', '0', '0', 'base_link', 'workspace_center']
    )
    
    # RViz 시각화 (DoosanRobotics M0609 전용 설정)
    rviz_config = PathJoinSubstitution([
        pkg_somacube, 'rviz', 'doosan_m0609_debug.rviz'
    ])
    
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2_doosan_m0609',
        arguments=['-d', rviz_config] if os.path.exists(rviz_config) else ['-d', PathJoinSubstitution([pkg_somacube, 'rviz', 'global_mapping_debug.rviz'])],
        parameters=[{'use_sim_time': LaunchConfiguration('use_sim_time')}],
        output='screen'
    )
    
    return LaunchDescription([
        # Arguments
        use_sim_time_arg,
        robot_ip_arg,
        realsense_serial_arg,
        enable_capture_arg,
        data_directory_arg,
        
        # Static TF
        tf_base_to_world,
        tf_workspace_center,
        
        # Core system nodes with proper sequencing
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
        
        # Processing pipeline
        TimerAction(
            period=7.0,
            actions=[
                yolo_detector_node,
                pointcloud_processor_node,
                pca_axis_estimator_node,
            ]
        ),
        
        TimerAction(
            period=9.0,
            actions=[
                manhattan_aligner_node,
                multiview_fusion_node,
            ]
        ),
        
        # Interface and visualization
        TimerAction(
            period=11.0,
            actions=[
                visualization_node,
                capture_control_node,
                rviz_node,
            ]
        ),
    ])