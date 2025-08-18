#!/usr/bin/env python3
"""
동기화된 캡처 노드
SLAM 없는 글로벌 맵 구성을 위한 정밀한 RGB-Depth 동기 캡처 및 타임스탬프 제어
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy
from sensor_msgs.msg import Image, CameraInfo, PointCloud2
from geometry_msgs.msg import PoseStamped, TransformStamped
from std_msgs.msg import String, Bool, Header
from builtin_interfaces.msg import Time
import tf2_ros
import tf2_geometry_msgs
from cv_bridge import CvBridge
import cv2
import numpy as np
import json
import os
import time
from pathlib import Path
from collections import deque
import threading
from scipy.spatial.transform import Rotation as R


class SynchronizedCaptureNode(Node):
    """동기화된 캡처 및 글로벌 맵 구성"""
    
    def __init__(self):
        super().__init__('synchronized_capture')
        
        # Parameters
        self.declare_parameters_from_yaml()
        
        # TF buffer with long history for precise interpolation
        self.tf_buffer = tf2_ros.Buffer(cache_time=rclpy.duration.Duration(seconds=10.0))
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)
        
        # CV bridge
        self.bridge = CvBridge()
        
        # Synchronization state
        self.capture_enabled = False
        self.capture_requested = False
        self.current_pose_index = 0
        
        # Frame buffers for temporal filtering (3-5 frame median)
        self.rgb_buffer = deque(maxlen=5)
        self.depth_buffer = deque(maxlen=5)
        self.timestamp_buffer = deque(maxlen=5)
        
        # Capture statistics
        self.capture_count = 0
        self.timestamp_deltas = []
        self.tf_query_failures = 0
        
        # QoS profiles for reliable synchronization
        sensor_qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,  # 동기화를 위해 RELIABLE 사용
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
            durability=DurabilityPolicy.VOLATILE
        )
        
        # Subscribers with synchronized timestamps
        self.rgb_sub = self.create_subscription(
            Image,
            '/camera/color/image_raw',
            self.rgb_callback,
            sensor_qos
        )
        
        self.depth_sub = self.create_subscription(
            Image,
            '/camera/aligned_depth_to_color/image_raw',
            self.depth_callback,
            sensor_qos
        )
        
        self.camera_info_sub = self.create_subscription(
            CameraInfo,
            '/camera/color/camera_info',
            self.camera_info_callback,
            sensor_qos
        )
        
        # 포즈 매니저로부터 현재 포즈 인덱스 수신
        self.pose_index_sub = self.create_subscription(
            String,
            '/camera_pose_manager/global_map_status',
            self.pose_status_callback,
            10
        )
        
        # 캡처 트리거 구독
        self.capture_trigger_sub = self.create_subscription(
            Bool,
            '/synchronized_capture/trigger',
            self.capture_trigger_callback,
            10
        )
        
        # Publishers
        self.synchronized_rgb_pub = self.create_publisher(
            Image,
            '/synchronized_capture/rgb',
            10
        )
        
        self.synchronized_depth_pub = self.create_publisher(
            Image,
            '/synchronized_capture/depth',
            10
        )
        
        self.synchronized_pointcloud_pub = self.create_publisher(
            PointCloud2,
            '/synchronized_capture/pointcloud',
            10
        )
        
        self.global_map_pub = self.create_publisher(
            PointCloud2,
            '/synchronized_capture/global_map',
            10
        )
        
        self.capture_status_pub = self.create_publisher(
            String,
            '/synchronized_capture/status',
            10
        )
        
        # State
        self.latest_rgb = None
        self.latest_depth = None
        self.camera_info = None
        self.latest_rgb_timestamp = None
        self.latest_depth_timestamp = None
        
        # Global map accumulation
        self.global_points = []
        self.global_colors = []
        self.tsdf_volume = None  # Will be initialized if needed
        
        # Data storage
        self.data_dir = self.get_parameter('synchronized_capture.data_dir').value
        self.session_dir = None
        self.create_session_directory()
        
        # Capture timing control
        self.last_capture_time = time.time()
        self.min_capture_interval = 0.5  # 최소 캡처 간격 (초)
        
        # Timer for status monitoring
        self.status_timer = self.create_timer(1.0, self.publish_status)
        
        self.get_logger().info('Synchronized Capture node initialized')
        self.get_logger().info(f'Data directory: {self.session_dir}')

    def declare_parameters_from_yaml(self):
        """YAML 설정에서 파라미터 선언"""
        defaults = {
            'common.frames.base': 'base_link',
            'common.frames.camera': 'camera_link',
            'common.frames.world': 'world',
            
            'synchronized_capture.data_dir': '/tmp/somacube_captures',
            'synchronized_capture.session_prefix': 'scene_',
            
            # 동기화 파라미터 (계획에서 제시한 값들)
            'synchronized_capture.sync.target_delta_ms': 3.0,
            'synchronized_capture.sync.max_delta_ms': 10.0,
            'synchronized_capture.sync.settle_time_ms': 150.0,
            'synchronized_capture.sync.frame_composite_count': 5,
            
            # 캡처 품질
            'synchronized_capture.quality.enable_ae_lock': True,
            'synchronized_capture.quality.enable_wb_lock': True,
            'synchronized_capture.quality.depth_temporal_filter': True,
            'synchronized_capture.quality.depth_spatial_filter': True,
            'synchronized_capture.quality.depth_hole_filling': True,
            
            # 전처리 파라미터
            'synchronized_capture.preprocessing.voxel_size_mm': 6.0,
            'synchronized_capture.preprocessing.ransac_epsilon_mm': 3.0,
            'synchronized_capture.preprocessing.ransac_max_iter': 1000,
            
            # TSDF 파라미터  
            'synchronized_capture.tsdf.enable': True,
            'synchronized_capture.tsdf.voxel_size_mm': 6.0,
            'synchronized_capture.tsdf.trunc_distance_factor': 3.0,
            
            # 글로벌 맵
            'synchronized_capture.global_map.max_points': 5000000,
            'synchronized_capture.global_map.enable_voxel_filter': True,
            'synchronized_capture.global_map.publish_rate_hz': 1.0,
        }
        
        for name, default_value in defaults.items():
            self.declare_parameter(name, default_value)

    def create_session_directory(self):
        """세션 디렉토리 생성"""
        base_dir = Path(self.get_parameter('synchronized_capture.data_dir').value)
        session_prefix = self.get_parameter('synchronized_capture.session_prefix').value
        
        # 타임스탬프 기반 세션 이름
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        self.session_dir = base_dir / f"{session_prefix}{timestamp}"
        
        # 디렉토리 구조 생성
        self.session_dir.mkdir(parents=True, exist_ok=True)
        (self.session_dir / 'rgb').mkdir(exist_ok=True)
        (self.session_dir / 'depth').mkdir(exist_ok=True)
        (self.session_dir / 'metadata').mkdir(exist_ok=True)
        (self.session_dir / 'pointclouds').mkdir(exist_ok=True)

    def pose_status_callback(self, msg):
        """포즈 상태 콜백"""
        try:
            status_data = json.loads(msg.data)
            self.current_pose_index = status_data.get('current_pose_index', 0)
        except json.JSONDecodeError:
            pass

    def capture_trigger_callback(self, msg):
        """캡처 트리거 콜백 - 이벤트 잠금 방식"""
        if msg.data and not self.capture_requested:
            current_time = time.time()
            
            # 최소 간격 확인
            if current_time - self.last_capture_time < self.min_capture_interval:
                self.get_logger().warn(f'Capture request too frequent, ignoring')
                return
                
            self.capture_requested = True
            self.last_capture_time = current_time
            
            # 정착 대기 시간
            settle_time = self.get_parameter('synchronized_capture.sync.settle_time_ms').value / 1000.0
            
            # 정착 대기 후 캡처 시작
            def delayed_capture():
                time.sleep(settle_time)
                self.capture_enabled = True
                self.get_logger().info(f'Capture enabled for pose {self.current_pose_index}')
                
            threading.Thread(target=delayed_capture, daemon=True).start()

    def rgb_callback(self, msg):
        """RGB 이미지 콜백"""
        self.latest_rgb = msg
        self.latest_rgb_timestamp = msg.header.stamp
        
        # 버퍼에 추가 (시간 순서 중요)
        self.rgb_buffer.append((msg, msg.header.stamp))
        
        # 동기화된 캡처 시도
        if self.capture_enabled:
            self.attempt_synchronized_capture()

    def depth_callback(self, msg):
        """Depth 이미지 콜백"""
        self.latest_depth = msg
        self.latest_depth_timestamp = msg.header.stamp
        
        # 버퍼에 추가
        self.depth_buffer.append((msg, msg.header.stamp))
        
        # 동기화된 캡처 시도
        if self.capture_enabled:
            self.attempt_synchronized_capture()

    def camera_info_callback(self, msg):
        """카메라 정보 콜백"""
        self.camera_info = msg

    def attempt_synchronized_capture(self):
        """동기화된 캡처 시도"""
        if not self.capture_enabled:
            return
            
        if (not self.latest_rgb or not self.latest_depth or 
            not self.camera_info):
            return
            
        # 타임스탬프 동기 검사
        rgb_stamp = self.latest_rgb_timestamp
        depth_stamp = self.latest_depth_timestamp
        
        # ROS Time을 초 단위로 변환
        rgb_time = rgb_stamp.sec + rgb_stamp.nanosec * 1e-9
        depth_time = depth_stamp.sec + depth_stamp.nanosec * 1e-9
        
        timestamp_delta = abs(rgb_time - depth_time) * 1000.0  # ms
        
        target_delta = self.get_parameter('synchronized_capture.sync.target_delta_ms').value
        max_delta = self.get_parameter('synchronized_capture.sync.max_delta_ms').value
        
        if timestamp_delta > max_delta:
            self.get_logger().debug(f'Timestamp delta too large: {timestamp_delta:.2f} ms')
            return
            
        # 성공적인 동기화 - 캡처 수행
        self.perform_capture(rgb_stamp, depth_stamp, timestamp_delta)
        
        # 캡처 완료 후 비활성화
        self.capture_enabled = False
        self.capture_requested = False

    def perform_capture(self, rgb_stamp: Time, depth_stamp: Time, delta_ms: float):
        """실제 캡처 수행"""
        try:
            # 통계 기록
            self.timestamp_deltas.append(delta_ms)
            
            # 중앙값 합성을 위한 프레임 수집
            composite_count = self.get_parameter('synchronized_capture.sync.frame_composite_count').value
            
            if len(self.rgb_buffer) >= composite_count and len(self.depth_buffer) >= composite_count:
                # 최근 프레임들의 중앙값 계산
                composite_rgb = self.compute_median_frame([frame[0] for frame in list(self.rgb_buffer)[-composite_count:]], 'bgr8')
                composite_depth = self.compute_median_frame([frame[0] for frame in list(self.depth_buffer)[-composite_count:]], 'passthrough')
            else:
                composite_rgb = self.latest_rgb
                composite_depth = self.latest_depth
            
            # TF 조회 - 이벤트 시점의 정확한 변환
            capture_time = rgb_stamp  # RGB 타임스탬프를 기준으로 사용
            
            try:
                # 카메라 좌표계에서 베이스(월드) 좌표계로의 변환
                transform = self.tf_buffer.lookup_transform(
                    self.get_parameter('common.frames.world').value,
                    self.get_parameter('common.frames.camera').value,
                    capture_time,
                    timeout=rclpy.duration.Duration(seconds=0.1)
                )
                
                # 변환 행렬 추출
                T_world_camera = self.transform_to_matrix(transform)
                
            except Exception as e:
                self.get_logger().error(f'TF lookup failed: {e}')
                self.tf_query_failures += 1
                return
                
            # 데이터 저장
            self.save_capture_data(composite_rgb, composite_depth, capture_time, T_world_camera, delta_ms)
            
            # 포인트클라우드 생성 및 글로벌 맵 업데이트
            self.update_global_map(composite_rgb, composite_depth, T_world_camera)
            
            # 동기화된 데이터 발행
            self.publish_synchronized_data(composite_rgb, composite_depth, capture_time)
            
            self.capture_count += 1
            self.get_logger().info(
                f'Captured frame {self.capture_count} for pose {self.current_pose_index}, '
                f'sync delta: {delta_ms:.2f} ms'
            )
            
        except Exception as e:
            self.get_logger().error(f'Capture failed: {e}')

    def compute_median_frame(self, frames: list, encoding: str) -> Image:
        """프레임들의 중앙값 합성"""
        if not frames:
            return None
            
        try:
            cv_images = []
            for frame in frames:
                cv_img = self.bridge.imgmsg_to_cv2(frame, encoding)
                cv_images.append(cv_img)
                
            # 중앙값 계산
            median_image = np.median(cv_images, axis=0).astype(cv_images[0].dtype)
            
            # ROS 메시지로 변환
            median_msg = self.bridge.cv2_to_imgmsg(median_image, encoding)
            median_msg.header = frames[-1].header  # 최신 헤더 사용
            
            return median_msg
            
        except Exception as e:
            self.get_logger().error(f'Median computation failed: {e}')
            return frames[-1]  # 실패시 최신 프레임 반환

    def transform_to_matrix(self, transform: TransformStamped) -> np.ndarray:
        """TransformStamped를 4x4 변환 행렬로 변환"""
        trans = transform.transform
        
        # 회전 (쿼터니언 → 회전 행렬)
        quat = [trans.rotation.x, trans.rotation.y, 
                trans.rotation.z, trans.rotation.w]
        rotation_matrix = R.from_quat(quat).as_matrix()
        
        # 변환 행렬 구성
        T = np.eye(4)
        T[:3, :3] = rotation_matrix
        T[:3, 3] = [trans.translation.x, trans.translation.y, trans.translation.z]
        
        return T

    def save_capture_data(self, rgb: Image, depth: Image, timestamp: Time, 
                         transform: np.ndarray, delta_ms: float):
        """캡처 데이터를 파일로 저장"""
        try:
            pose_dir = self.session_dir / f'pose_{self.current_pose_index:03d}'
            pose_dir.mkdir(exist_ok=True)
            
            # 파일 이름
            frame_id = f'{self.capture_count:06d}'
            
            # RGB 저장
            rgb_cv = self.bridge.imgmsg_to_cv2(rgb, 'bgr8')
            cv2.imwrite(str(pose_dir / f'rgb_{frame_id}.png'), rgb_cv)
            
            # Depth 저장
            depth_cv = self.bridge.imgmsg_to_cv2(depth, 'passthrough')
            cv2.imwrite(str(pose_dir / f'depth_{frame_id}.png'), depth_cv)
            
            # 메타데이터 저장
            metadata = {
                'timestamp': {
                    'sec': timestamp.sec,
                    'nanosec': timestamp.nanosec
                },
                'pose_index': self.current_pose_index,
                'frame_id': frame_id,
                'sync_delta_ms': delta_ms,
                'T_world_camera': transform.tolist(),
                'camera_info': {
                    'height': self.camera_info.height,
                    'width': self.camera_info.width,
                    'K': list(self.camera_info.k),
                    'D': list(self.camera_info.d),
                    'distortion_model': self.camera_info.distortion_model
                }
            }
            
            with open(pose_dir / f'metadata_{frame_id}.json', 'w') as f:
                json.dump(metadata, f, indent=2)
                
            self.get_logger().debug(f'Saved data to {pose_dir}')
            
        except Exception as e:
            self.get_logger().error(f'Data saving failed: {e}')

    def update_global_map(self, rgb: Image, depth: Image, T_world_camera: np.ndarray):
        """글로벌 맵 업데이트"""
        try:
            # Depth를 포인트클라우드로 변환
            points_3d, colors = self.depth_to_pointcloud(rgb, depth)
            
            if len(points_3d) == 0:
                return
                
            # 글로벌 좌표계로 변환
            points_homo = np.column_stack([points_3d, np.ones(len(points_3d))])
            global_points = (T_world_camera @ points_homo.T).T[:, :3]
            
            # 테이블 제거 (RANSAC 평면 제거)
            filtered_points, filtered_colors = self.remove_table_plane(global_points, colors)
            
            # Voxel 다운샘플링
            if self.get_parameter('synchronized_capture.global_map.enable_voxel_filter').value:
                voxel_size = self.get_parameter('synchronized_capture.preprocessing.voxel_size_mm').value / 1000.0
                filtered_points, filtered_colors = self.voxel_downsample(filtered_points, filtered_colors, voxel_size)
            
            # 글로벌 맵에 추가
            self.global_points.extend(filtered_points.tolist())
            if len(filtered_colors) == len(filtered_points):
                self.global_colors.extend(filtered_colors.tolist())
                
            # 메모리 관리
            max_points = self.get_parameter('synchronized_capture.global_map.max_points').value
            if len(self.global_points) > max_points:
                excess = len(self.global_points) - max_points
                self.global_points = self.global_points[excess:]
                if self.global_colors:
                    self.global_colors = self.global_colors[excess:]
                    
            self.get_logger().debug(f'Global map updated: {len(self.global_points)} total points')
            
        except Exception as e:
            self.get_logger().error(f'Global map update failed: {e}')

    def depth_to_pointcloud(self, rgb: Image, depth: Image) -> tuple:
        """Depth 이미지를 포인트클라우드로 변환"""
        try:
            rgb_cv = self.bridge.imgmsg_to_cv2(rgb, 'bgr8')
            depth_cv = self.bridge.imgmsg_to_cv2(depth, 'passthrough')
            
            h, w = depth_cv.shape
            
            # 카메라 내부 파라미터
            K = np.array(self.camera_info.k).reshape(3, 3)
            fx, fy = K[0, 0], K[1, 1]
            cx, cy = K[0, 2], K[1, 2]
            
            # 좌표 그리드 생성
            u, v = np.meshgrid(np.arange(w), np.arange(h))
            
            # 유효한 깊이 마스크
            valid_mask = (depth_cv > 0) & (depth_cv < 5000)  # 5m 최대
            
            # 유효한 픽셀 추출
            u_valid = u[valid_mask]
            v_valid = v[valid_mask]
            z_valid = depth_cv[valid_mask] / 1000.0  # mm to m
            
            # 3D 좌표 계산
            x_valid = (u_valid - cx) * z_valid / fx
            y_valid = (v_valid - cy) * z_valid / fy
            
            points_3d = np.column_stack([x_valid, y_valid, z_valid])
            
            # 색상 추출
            colors = rgb_cv[valid_mask][:, [2, 1, 0]]  # BGR to RGB
            
            return points_3d, colors
            
        except Exception as e:
            self.get_logger().error(f'Pointcloud conversion failed: {e}')
            return np.array([]), np.array([])

    def remove_table_plane(self, points: np.ndarray, colors: np.ndarray) -> tuple:
        """RANSAC을 사용한 테이블 평면 제거"""
        if len(points) < 100:
            return points, colors
            
        try:
            epsilon = self.get_parameter('synchronized_capture.preprocessing.ransac_epsilon_mm').value / 1000.0
            max_iter = self.get_parameter('synchronized_capture.preprocessing.ransac_max_iter').value
            
            best_inliers = []
            best_count = 0
            
            for _ in range(max_iter):
                # 3개 점 샘플링
                if len(points) < 3:
                    break
                    
                sample_indices = np.random.choice(len(points), 3, replace=False)
                p1, p2, p3 = points[sample_indices]
                
                # 평면 방정식 계산
                v1, v2 = p2 - p1, p3 - p1
                normal = np.cross(v1, v2)
                
                if np.linalg.norm(normal) < 1e-8:
                    continue
                    
                normal = normal / np.linalg.norm(normal)
                d = -np.dot(normal, p1)
                
                # 인라이어 계산
                distances = np.abs(points @ normal + d)
                inliers = distances < epsilon
                inlier_count = np.sum(inliers)
                
                if inlier_count > best_count:
                    best_count = inlier_count
                    best_inliers = inliers
                    
            if best_count > 100:  # 충분한 테이블 점들이 있다면
                outliers = ~best_inliers
                return points[outliers], colors[outliers] if len(colors) > 0 else colors
            else:
                return points, colors
                
        except Exception as e:
            self.get_logger().error(f'Plane removal failed: {e}')
            return points, colors

    def voxel_downsample(self, points: np.ndarray, colors: np.ndarray, voxel_size: float) -> tuple:
        """Voxel 다운샘플링"""
        if len(points) == 0:
            return points, colors
            
        try:
            # Voxel 인덱스 계산
            voxel_indices = np.floor(points / voxel_size).astype(int)
            
            # 고유한 voxel 찾기
            unique_voxels, inverse_indices = np.unique(
                voxel_indices, axis=0, return_inverse=True
            )
            
            # 각 voxel의 대표점 계산 (중심점)
            downsampled_points = []
            downsampled_colors = []
            
            for i in range(len(unique_voxels)):
                voxel_mask = inverse_indices == i
                voxel_points = points[voxel_mask]
                
                # 중심점
                centroid = np.mean(voxel_points, axis=0)
                downsampled_points.append(centroid)
                
                # 색상 평균
                if len(colors) > 0:
                    voxel_colors = colors[voxel_mask]
                    avg_color = np.mean(voxel_colors, axis=0)
                    downsampled_colors.append(avg_color)
                    
            return np.array(downsampled_points), np.array(downsampled_colors)
            
        except Exception as e:
            self.get_logger().error(f'Voxel downsampling failed: {e}')
            return points, colors

    def publish_synchronized_data(self, rgb: Image, depth: Image, timestamp: Time):
        """동기화된 데이터 발행"""
        try:
            # 헤더 통일
            header = Header()
            header.stamp = timestamp
            header.frame_id = self.get_parameter('common.frames.camera').value
            
            # RGB 발행
            sync_rgb = rgb
            sync_rgb.header = header
            self.synchronized_rgb_pub.publish(sync_rgb)
            
            # Depth 발행
            sync_depth = depth
            sync_depth.header = header
            self.synchronized_depth_pub.publish(sync_depth)
            
            # 포인트클라우드 생성 및 발행
            points_3d, colors = self.depth_to_pointcloud(rgb, depth)
            if len(points_3d) > 0:
                pc_msg = self.create_pointcloud2_msg(points_3d, colors, header)
                self.synchronized_pointcloud_pub.publish(pc_msg)
                
        except Exception as e:
            self.get_logger().error(f'Data publication failed: {e}')

    def create_pointcloud2_msg(self, points: np.ndarray, colors: np.ndarray, header: Header) -> PointCloud2:
        """PointCloud2 메시지 생성"""
        from sensor_msgs.msg import PointField
        import struct
        
        msg = PointCloud2()
        msg.header = header
        msg.height = 1
        msg.width = len(points)
        msg.is_dense = False
        msg.is_bigendian = False
        
        # 필드 정의
        if len(colors) == len(points):
            msg.fields = [
                PointField(name='x', offset=0, datatype=PointField.FLOAT32, count=1),
                PointField(name='y', offset=4, datatype=PointField.FLOAT32, count=1),
                PointField(name='z', offset=8, datatype=PointField.FLOAT32, count=1),
                PointField(name='rgb', offset=12, datatype=PointField.UINT32, count=1),
            ]
            msg.point_step = 16
        else:
            msg.fields = [
                PointField(name='x', offset=0, datatype=PointField.FLOAT32, count=1),
                PointField(name='y', offset=4, datatype=PointField.FLOAT32, count=1),
                PointField(name='z', offset=8, datatype=PointField.FLOAT32, count=1),
            ]
            msg.point_step = 12
            
        msg.row_step = msg.point_step * len(points)
        
        # 데이터 패킹
        buffer = []
        for i, point in enumerate(points):
            if len(colors) == len(points):
                r, g, b = colors[i][:3]
                rgb = (int(r) << 16) | (int(g) << 8) | int(b)
                buffer.append(struct.pack('fffI', point[0], point[1], point[2], rgb))
            else:
                buffer.append(struct.pack('fff', point[0], point[1], point[2]))
                
        msg.data = b''.join(buffer)
        return msg

    def publish_status(self):
        """상태 정보 발행"""
        try:
            status = {
                'capture_count': self.capture_count,
                'current_pose_index': self.current_pose_index,
                'capture_enabled': self.capture_enabled,
                'capture_requested': self.capture_requested,
                'global_map_points': len(self.global_points),
                'tf_query_failures': self.tf_query_failures,
                'session_directory': str(self.session_dir),
                'timestamp_statistics': {
                    'count': len(self.timestamp_deltas),
                    'mean_ms': np.mean(self.timestamp_deltas) if self.timestamp_deltas else 0.0,
                    'std_ms': np.std(self.timestamp_deltas) if self.timestamp_deltas else 0.0,
                    'max_ms': np.max(self.timestamp_deltas) if self.timestamp_deltas else 0.0,
                }
            }
            
            status_msg = String()
            status_msg.data = json.dumps(status, indent=2)
            self.capture_status_pub.publish(status_msg)
            
            # 글로벌 맵 주기적 발행
            if (len(self.global_points) > 0 and 
                self.capture_count % 10 == 0):  # 10프레임마다
                self.publish_global_map()
                
        except Exception as e:
            self.get_logger().error(f'Status publication failed: {e}')

    def publish_global_map(self):
        """글로벌 맵 발행"""
        if len(self.global_points) == 0:
            return
            
        try:
            header = Header()
            header.stamp = self.get_clock().now().to_msg()
            header.frame_id = self.get_parameter('common.frames.world').value
            
            points_array = np.array(self.global_points)
            colors_array = np.array(self.global_colors) if self.global_colors else None
            
            global_map_msg = self.create_pointcloud2_msg(points_array, colors_array, header)
            self.global_map_pub.publish(global_map_msg)
            
            self.get_logger().debug(f'Published global map with {len(points_array)} points')
            
        except Exception as e:
            self.get_logger().error(f'Global map publication failed: {e}')


def main(args=None):
    rclpy.init(args=args)
    node = SynchronizedCaptureNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()