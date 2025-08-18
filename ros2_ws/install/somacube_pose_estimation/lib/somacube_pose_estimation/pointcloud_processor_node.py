#!/usr/bin/env python3
"""
점군 전처리 노드
수학적 정밀 체계 III단계: 점집합 전처리와 세그멘테이션 구현
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from sensor_msgs.msg import PointCloud2, Image, CameraInfo
from std_msgs.msg import String
from geometry_msgs.msg import PoseStamped
import tf2_ros
import tf2_geometry_msgs
import numpy as np
from cv_bridge import CvBridge
import json

# Import mathematical foundations
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from somacube_pose_estimation.mathematical_foundations import MathematicalFoundations

try:
    import open3d as o3d
    HAS_OPEN3D = True
except ImportError:
    HAS_OPEN3D = False


class PointCloudProcessorNode(Node):
    """점군 전처리 및 세그멘테이션 (정리 T1-T6 구현)"""
    
    def __init__(self):
        super().__init__('pointcloud_processor')
        
        # Mathematical foundations
        self.math_foundation = MathematicalFoundations()
        
        # Parameters
        self.declare_parameters_from_yaml()
        
        # TF buffer
        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)
        
        # CV bridge
        self.bridge = CvBridge()
        
        # QoS profiles
        sensor_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=5
        )
        
        # Subscribers
        self.rgb_sub = self.create_subscription(
            Image,
            self.get_parameter('common.topics.rgb').value,
            self.rgb_callback,
            sensor_qos
        )
        
        self.depth_sub = self.create_subscription(
            Image,
            self.get_parameter('common.topics.depth').value,
            self.depth_callback,
            sensor_qos
        )
        
        self.camera_info_sub = self.create_subscription(
            CameraInfo,
            self.get_parameter('common.topics.camera_info').value,
            self.camera_info_callback,
            sensor_qos
        )
        
        # YOLO detections for ROI filtering
        self.detection_sub = self.create_subscription(
            String,
            '/yolo_detector/detections',
            self.detection_callback,
            10
        )
        
        # Camera pose for global transformation
        self.camera_pose_sub = self.create_subscription(
            PoseStamped,
            '/camera_pose_manager/current_pose',
            self.camera_pose_callback,
            10
        )
        
        # Publishers
        self.processed_pc_pub = self.create_publisher(
            PointCloud2,
            '/pointcloud_processor/processed_cloud',
            10
        )
        
        self.segmented_objects_pub = self.create_publisher(
            String,
            '/pointcloud_processor/segmented_objects',
            10
        )
        
        self.global_pc_pub = self.create_publisher(
            PointCloud2,
            '/pointcloud_processor/global_cloud',
            10
        )
        
        self.debug_image_pub = self.create_publisher(
            Image,
            '/pointcloud_processor/debug_image',
            10
        )
        
        # State
        self.latest_rgb = None
        self.latest_depth = None
        self.camera_info = None
        self.latest_detections = None
        self.current_camera_pose = None
        
        # Global point cloud accumulation
        self.global_pointcloud = []
        self.global_colors = []
        
        # Timer for processing
        processing_rate = self.get_parameter('pointcloud_processor.processing_rate_hz').value
        self.timer = self.create_timer(1.0 / processing_rate, self.process_pointcloud)
        
        self.get_logger().info('PointCloud Processor node initialized')
        self.get_logger().info(f'Open3D available: {HAS_OPEN3D}')

    def declare_parameters_from_yaml(self):
        """YAML 설정에서 파라미터 선언"""
        defaults = {
            'common.topics.rgb': '/camera/color/image_raw',
            'common.topics.depth': '/camera/aligned_depth_to_color/image_raw',
            'common.topics.camera_info': '/camera/color/camera_info',
            'common.frames.camera': 'camera_link',
            'common.frames.world': 'world',
            
            'pointcloud_processor.processing_rate_hz': 10.0,
            'pointcloud_processor.depth_scale': 0.001,  # mm to m
            'pointcloud_processor.depth_max_m': 2.0,
            'pointcloud_processor.depth_min_m': 0.1,
            
            # 정리 T4: RANSAC 평면 제거 파라미터
            'pointcloud_processor.plane_removal.enable': True,
            'pointcloud_processor.plane_removal.epsilon': 0.005,
            'pointcloud_processor.plane_removal.max_iterations': 1000,
            'pointcloud_processor.plane_removal.min_inliers': 100,
            
            # 정리 T5: Voxel 다운샘플링 파라미터  
            'pointcloud_processor.voxel_downsample.enable': True,
            'pointcloud_processor.voxel_downsample.size_m': 0.002,
            
            # 정리 T6: DBSCAN 클러스터링 파라미터
            'pointcloud_processor.clustering.enable': True,
            'pointcloud_processor.clustering.eps': 0.01,
            'pointcloud_processor.clustering.min_samples': 50,
            'pointcloud_processor.clustering.min_cluster_points': 100,
            
            # ROI 필터링 (YOLO 검출 영역 확장)
            'pointcloud_processor.roi_filtering.enable': True,
            'pointcloud_processor.roi_filtering.expansion_ratio': 0.2,
            'pointcloud_processor.roi_filtering.min_depth_m': 0.05,
            
            # 글로벌 맵 구성
            'pointcloud_processor.global_map.enable': True,
            'pointcloud_processor.global_map.voxel_size_m': 0.001,
            'pointcloud_processor.global_map.max_points': 1000000,
        }
        
        for name, default_value in defaults.items():
            self.declare_parameter(name, default_value)

    def rgb_callback(self, msg):
        """RGB 이미지 콜백"""
        self.latest_rgb = msg

    def depth_callback(self, msg):
        """Depth 이미지 콜백"""
        self.latest_depth = msg

    def camera_info_callback(self, msg):
        """카메라 정보 콜백"""
        self.camera_info = msg

    def detection_callback(self, msg):
        """YOLO 검출 결과 콜백"""
        try:
            detection_data = json.loads(msg.data)
            self.latest_detections = detection_data.get('detections', [])
        except json.JSONDecodeError as e:
            self.get_logger().error(f'Failed to parse detection data: {e}')

    def camera_pose_callback(self, msg):
        """카메라 포즈 콜백"""
        self.current_camera_pose = msg

    def process_pointcloud(self):
        """메인 점군 처리 루프"""
        if not self.all_data_available():
            return
            
        try:
            # 1. Depth to 3D point cloud (정리 T2: 역투영)
            points_3d, colors = self.depth_to_pointcloud()
            
            if len(points_3d) < 100:
                return
                
            # 2. ROI filtering using YOLO detections
            if self.get_parameter('pointcloud_processor.roi_filtering.enable').value and self.latest_detections:
                points_3d, colors = self.filter_by_detection_roi(points_3d, colors)
                
            # 3. 평면 제거 (정리 T4: RANSAC)
            if self.get_parameter('pointcloud_processor.plane_removal.enable').value:
                points_3d, colors = self.remove_table_plane(points_3d, colors)
                
            # 4. Voxel 다운샘플링 (정리 T5)
            if self.get_parameter('pointcloud_processor.voxel_downsample.enable').value:
                points_3d, colors = self.voxel_downsample(points_3d, colors)
                
            # 5. 클러스터링 (정리 T6: DBSCAN)
            if self.get_parameter('pointcloud_processor.clustering.enable').value:
                clusters = self.cluster_objects(points_3d)
                self.publish_segmented_objects(clusters, colors)
                
            # 6. 처리된 점군 발행
            if len(points_3d) > 0:
                self.publish_processed_pointcloud(points_3d, colors)
                
            # 7. 글로벌 맵에 추가
            if (self.get_parameter('pointcloud_processor.global_map.enable').value and 
                self.current_camera_pose is not None):
                self.add_to_global_map(points_3d, colors)
                
        except Exception as e:
            self.get_logger().error(f'Point cloud processing error: {e}')

    def all_data_available(self) -> bool:
        """모든 필요한 데이터가 준비되었는지 확인"""
        return all([
            self.latest_rgb is not None,
            self.latest_depth is not None,
            self.camera_info is not None
        ])

    def depth_to_pointcloud(self) -> tuple:
        """정리 T2: Depth 이미지를 3D 점군으로 변환"""
        try:
            # Convert ROS images to OpenCV
            rgb_image = self.bridge.imgmsg_to_cv2(self.latest_rgb, 'bgr8')
            depth_image = self.bridge.imgmsg_to_cv2(self.latest_depth, 'passthrough')
            
            h, w = depth_image.shape
            
            # Camera intrinsics (정리 T1)
            K = np.array(self.camera_info.k).reshape(3, 3)
            fx, fy = K[0, 0], K[1, 1]
            cx, cy = K[0, 2], K[1, 2]
            
            # Depth scaling
            depth_scale = self.get_parameter('pointcloud_processor.depth_scale').value
            depth_min = self.get_parameter('pointcloud_processor.depth_min_m').value
            depth_max = self.get_parameter('pointcloud_processor.depth_max_m').value
            
            # Create coordinate grids
            u, v = np.meshgrid(np.arange(w), np.arange(h))
            
            # Valid depth mask
            depth_m = depth_image * depth_scale
            valid_mask = (depth_m > depth_min) & (depth_m < depth_max)
            
            # Extract valid pixels
            u_valid = u[valid_mask]
            v_valid = v[valid_mask] 
            z_valid = depth_m[valid_mask]
            
            # Back-project to 3D (정리 T2 구현)
            x_valid = (u_valid - cx) * z_valid / fx
            y_valid = (v_valid - cy) * z_valid / fy
            
            points_3d = np.column_stack([x_valid, y_valid, z_valid])
            
            # Extract colors
            rgb_valid = rgb_image[valid_mask]  # Nx3 BGR
            colors = rgb_valid[:, [2, 1, 0]]  # BGR to RGB
            
            return points_3d, colors
            
        except Exception as e:
            self.get_logger().error(f'Depth to pointcloud conversion error: {e}')
            return np.array([]), np.array([])

    def filter_by_detection_roi(self, points_3d: np.ndarray, colors: np.ndarray) -> tuple:
        """YOLO 검출 ROI로 점군 필터링"""
        if len(self.latest_detections) == 0:
            return points_3d, colors
            
        try:
            # Camera intrinsics
            K = np.array(self.camera_info.k).reshape(3, 3)
            
            # Project 3D points to 2D (정리 T1)
            projected_2d, valid_mask = self.math_foundation.pinhole_projection(points_3d, K)
            
            if np.sum(valid_mask) == 0:
                return points_3d, colors
                
            # Filter points that are inside detection ROIs
            roi_mask = np.zeros(len(projected_2d), dtype=bool)
            expansion_ratio = self.get_parameter('pointcloud_processor.roi_filtering.expansion_ratio').value
            
            for detection in self.latest_detections:
                x1, y1, x2, y2 = detection['bbox']
                
                # Expand ROI
                w, h = x2 - x1, y2 - y1
                x1 -= w * expansion_ratio
                y1 -= h * expansion_ratio
                x2 += w * expansion_ratio  
                y2 += h * expansion_ratio
                
                # Check which points are inside ROI
                u_coords, v_coords = projected_2d[:, 0], projected_2d[:, 1]
                inside_roi = ((u_coords >= x1) & (u_coords <= x2) & 
                             (v_coords >= y1) & (v_coords <= y2))
                roi_mask |= inside_roi
                
            # Apply ROI mask to original valid points
            filtered_points = points_3d[valid_mask][roi_mask]
            filtered_colors = colors[valid_mask][roi_mask]
            
            return filtered_points, filtered_colors
            
        except Exception as e:
            self.get_logger().error(f'ROI filtering error: {e}')
            return points_3d, colors

    def remove_table_plane(self, points_3d: np.ndarray, colors: np.ndarray) -> tuple:
        """정리 T4: RANSAC 기반 테이블 평면 제거"""
        if len(points_3d) < 100:
            return points_3d, colors
            
        epsilon = self.get_parameter('pointcloud_processor.plane_removal.epsilon').value
        max_iterations = self.get_parameter('pointcloud_processor.plane_removal.max_iterations').value
        min_inliers = self.get_parameter('pointcloud_processor.plane_removal.min_inliers').value
        
        # RANSAC 평면 제거 (알고리즘 A1)
        filtered_points, normal, d = self.math_foundation.ransac_plane_removal(
            points_3d, epsilon, max_iterations, min_inliers
        )
        
        if len(filtered_points) == 0:
            return points_3d, colors
            
        # 색상도 동일하게 필터링
        outlier_indices = []
        for i, point in enumerate(points_3d):
            distance = abs(np.dot(normal, point) + d)
            if distance >= epsilon:
                outlier_indices.append(i)
                
        filtered_colors = colors[outlier_indices] if len(outlier_indices) > 0 else colors
        
        self.get_logger().debug(f'Removed {len(points_3d) - len(filtered_points)} plane points')
        return filtered_points, filtered_colors

    def voxel_downsample(self, points_3d: np.ndarray, colors: np.ndarray) -> tuple:
        """정리 T5: Voxel 다운샘플링"""
        if len(points_3d) < 10:
            return points_3d, colors
            
        voxel_size = self.get_parameter('pointcloud_processor.voxel_downsample.size_m').value
        
        if HAS_OPEN3D:
            return self._voxel_downsample_open3d(points_3d, colors, voxel_size)
        else:
            return self._voxel_downsample_basic(points_3d, colors, voxel_size)

    def _voxel_downsample_open3d(self, points_3d: np.ndarray, colors: np.ndarray, 
                                voxel_size: float) -> tuple:
        """Open3D를 사용한 고급 Voxel 다운샘플링"""
        try:
            # Create Open3D point cloud
            pcd = o3d.geometry.PointCloud()
            pcd.points = o3d.utility.Vector3dVector(points_3d)
            
            if len(colors) == len(points_3d):
                pcd.colors = o3d.utility.Vector3dVector(colors / 255.0)  # Normalize to [0,1]
                
            # Voxel downsampling
            downsampled = pcd.voxel_down_sample(voxel_size)
            
            # Extract results
            down_points = np.asarray(downsampled.points)
            down_colors = np.asarray(downsampled.colors) * 255.0 if downsampled.has_colors() else colors[:len(down_points)]
            
            return down_points, down_colors.astype(np.uint8)
            
        except Exception as e:
            self.get_logger().error(f'Open3D voxel downsampling error: {e}')
            return self._voxel_downsample_basic(points_3d, colors, voxel_size)

    def _voxel_downsample_basic(self, points_3d: np.ndarray, colors: np.ndarray, 
                               voxel_size: float) -> tuple:
        """수학적 기초 구현 Voxel 다운샘플링"""
        # 정리 T5 직접 구현
        downsampled_points = self.math_foundation.voxel_downsample(points_3d, voxel_size)
        
        # 색상 매핑 (간단한 최근접 이웃)
        if len(colors) == len(points_3d) and len(downsampled_points) > 0:
            from scipy.spatial.distance import cdist
            distances = cdist(downsampled_points, points_3d)
            closest_indices = np.argmin(distances, axis=1)
            downsampled_colors = colors[closest_indices]
        else:
            downsampled_colors = colors[:len(downsampled_points)]
            
        return downsampled_points, downsampled_colors

    def cluster_objects(self, points_3d: np.ndarray) -> list:
        """정리 T6: DBSCAN 기반 객체 클러스터링"""
        if len(points_3d) < 50:
            return []
            
        eps = self.get_parameter('pointcloud_processor.clustering.eps').value
        min_samples = self.get_parameter('pointcloud_processor.clustering.min_samples').value
        min_cluster_points = self.get_parameter('pointcloud_processor.clustering.min_cluster_points').value
        
        try:
            from sklearn.cluster import DBSCAN
            
            # DBSCAN 클러스터링
            clustering = DBSCAN(eps=eps, min_samples=min_samples)
            cluster_labels = clustering.fit_predict(points_3d)
            
            # 클러스터별로 점들 분리
            clusters = []
            unique_labels = np.unique(cluster_labels)
            
            for label in unique_labels:
                if label == -1:  # 노이즈 제외
                    continue
                    
                cluster_points = points_3d[cluster_labels == label]
                
                if len(cluster_points) >= min_cluster_points:
                    cluster_info = {
                        'label': int(label),
                        'points': cluster_points.tolist(),
                        'size': len(cluster_points),
                        'centroid': np.mean(cluster_points, axis=0).tolist(),
                        'bounds': {
                            'min': np.min(cluster_points, axis=0).tolist(),
                            'max': np.max(cluster_points, axis=0).tolist()
                        }
                    }
                    clusters.append(cluster_info)
                    
            self.get_logger().debug(f'Found {len(clusters)} object clusters')
            return clusters
            
        except ImportError:
            self.get_logger().warn('scikit-learn not available, skipping clustering')
            return []
        except Exception as e:
            self.get_logger().error(f'Clustering error: {e}')
            return []

    def publish_processed_pointcloud(self, points_3d: np.ndarray, colors: np.ndarray):
        """처리된 점군 발행"""
        try:
            pc_msg = self.create_pointcloud2_msg(points_3d, colors)
            pc_msg.header.stamp = self.get_clock().now().to_msg()
            pc_msg.header.frame_id = self.get_parameter('common.frames.camera').value
            
            self.processed_pc_pub.publish(pc_msg)
            
        except Exception as e:
            self.get_logger().error(f'Failed to publish processed pointcloud: {e}')

    def publish_segmented_objects(self, clusters: list, colors: np.ndarray):
        """세그멘테이션된 객체들 발행"""
        if not clusters:
            return
            
        try:
            segmented_data = {
                'header': {
                    'stamp': self.get_clock().now().to_msg(),
                    'frame_id': self.get_parameter('common.frames.camera').value
                },
                'total_clusters': len(clusters),
                'clusters': clusters
            }
            
            json_msg = String()
            json_msg.data = json.dumps(segmented_data)
            self.segmented_objects_pub.publish(json_msg)
            
        except Exception as e:
            self.get_logger().error(f'Failed to publish segmented objects: {e}')

    def add_to_global_map(self, points_3d: np.ndarray, colors: np.ndarray):
        """글로벌 맵에 점군 추가"""
        if self.current_camera_pose is None or len(points_3d) == 0:
            return
            
        try:
            # 카메라 포즈를 4x4 변환 행렬로 변환
            pose = self.current_camera_pose.pose
            
            # 변환 행렬 구성
            T = np.eye(4)
            T[:3, 3] = [pose.position.x, pose.position.y, pose.position.z]
            
            from scipy.spatial.transform import Rotation as R
            quat = [pose.orientation.x, pose.orientation.y, 
                   pose.orientation.z, pose.orientation.w]
            T[:3, :3] = R.from_quat(quat).as_matrix()
            
            # 점들을 글로벌 좌표계로 변환
            points_homo = np.column_stack([points_3d, np.ones(len(points_3d))])
            global_points_homo = (T @ points_homo.T).T
            global_points = global_points_homo[:, :3]
            
            # 글로벌 맵에 추가
            self.global_pointcloud.extend(global_points.tolist())
            if len(colors) == len(points_3d):
                self.global_colors.extend(colors.tolist())
                
            # 메모리 관리
            max_points = self.get_parameter('pointcloud_processor.global_map.max_points').value
            if len(self.global_pointcloud) > max_points:
                # 오래된 점들 제거 (FIFO)
                excess = len(self.global_pointcloud) - max_points
                self.global_pointcloud = self.global_pointcloud[excess:]
                if self.global_colors:
                    self.global_colors = self.global_colors[excess:]
                    
            # 글로벌 점군 발행
            if len(self.global_pointcloud) > 0:
                global_points_array = np.array(self.global_pointcloud)
                global_colors_array = np.array(self.global_colors) if self.global_colors else None
                
                # Voxel 다운샘플링으로 글로벌 맵 압축
                voxel_size = self.get_parameter('pointcloud_processor.global_map.voxel_size_m').value
                if HAS_OPEN3D and len(global_points_array) > 1000:
                    global_points_array, global_colors_array = self._voxel_downsample_open3d(
                        global_points_array, global_colors_array, voxel_size
                    )
                
                global_pc_msg = self.create_pointcloud2_msg(global_points_array, global_colors_array)
                global_pc_msg.header.stamp = self.get_clock().now().to_msg()
                global_pc_msg.header.frame_id = self.get_parameter('common.frames.world').value
                
                self.global_pc_pub.publish(global_pc_msg)
                
        except Exception as e:
            self.get_logger().error(f'Global map update error: {e}')

    def create_pointcloud2_msg(self, points_3d: np.ndarray, colors: np.ndarray = None):
        """PointCloud2 메시지 생성"""
        from sensor_msgs.msg import PointField
        import struct
        
        msg = PointCloud2()
        msg.height = 1
        msg.width = len(points_3d)
        msg.is_dense = False
        msg.is_bigendian = False
        
        # Fields definition
        if colors is not None and len(colors) == len(points_3d):
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
            
        msg.row_step = msg.point_step * len(points_3d)
        
        # Pack data
        buffer = []
        for i, point in enumerate(points_3d):
            if colors is not None and i < len(colors):
                # RGB packing
                r, g, b = colors[i][:3]
                rgb = (int(r) << 16) | (int(g) << 8) | int(b)
                buffer.append(struct.pack('fffI', point[0], point[1], point[2], rgb))
            else:
                buffer.append(struct.pack('fff', point[0], point[1], point[2]))
                
        msg.data = b''.join(buffer)
        return msg


def main(args=None):
    rclpy.init(args=args)
    node = PointCloudProcessorNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()