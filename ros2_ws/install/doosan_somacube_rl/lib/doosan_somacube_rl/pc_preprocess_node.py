#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from sensor_msgs.msg import PointCloud2, Image, CameraInfo
from geometry_msgs.msg import TransformStamped
import cv2
import numpy as np
from cv_bridge import CvBridge
import tf2_ros
import yaml

try:
    import open3d as o3d
    HAS_OPEN3D = True
except ImportError:
    HAS_OPEN3D = False


class PCPreprocessNode(Node):
    def __init__(self):
        super().__init__('pc_preprocess')
        
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
        
        # Publishers
        self.pc_pub = self.create_publisher(
            PointCloud2,
            '/pc_preprocess/output',
            10
        )
        
        self.heightmap_pub = self.create_publisher(
            Image,
            '/debug/heightmap',
            10
        )
        
        # State
        self.latest_rgb = None
        self.latest_depth = None
        self.camera_info = None
        
        # Timer
        rate_hz = self.get_parameter('common.realtime.preprocess_rate_hz').value
        self.timer = self.create_timer(1.0 / rate_hz, self.process_callback)
        
        self.get_logger().info('PC Preprocess node initialized')

    def declare_parameters_from_yaml(self):
        # Define default parameters (subset of full config)
        defaults = {
            'common.topics.rgb': '/camera/color/image_raw',
            'common.topics.depth': '/camera/aligned_depth_to_color/image_raw',
            'common.topics.camera_info': '/camera/color/camera_info',
            'common.realtime.preprocess_rate_hz': 30,
            'common.frames.camera': 'camera_link',
            'common.frames.base': 'base',
            'pc_preprocess.voxel_size_m': 0.004,
            'pc_preprocess.plane_remove.enable': True,
            'pc_preprocess.plane_remove.dist_thresh_m': 0.005,
            'pc_preprocess.plane_remove.max_iter': 1000,
            'pc_preprocess.knn_denoise.enable': True,
            'pc_preprocess.knn_denoise.k': 24,
            'pc_preprocess.knn_denoise.std_ratio': 1.0,
            'pc_preprocess.heightmap.enable': True,
            'pc_preprocess.heightmap.resolution_m': 0.0025,
            'pc_preprocess.heightmap.roi_margin_m': 0.02,
        }
        
        for name, default_value in defaults.items():
            self.declare_parameter(name, default_value)

    def rgb_callback(self, msg):
        self.latest_rgb = msg

    def depth_callback(self, msg):
        self.latest_depth = msg

    def camera_info_callback(self, msg):
        self.camera_info = msg

    def process_callback(self):
        if not all([self.latest_rgb, self.latest_depth, self.camera_info]):
            return
            
        try:
            # Convert to OpenCV
            rgb_image = self.bridge.imgmsg_to_cv2(self.latest_rgb, 'bgr8')
            depth_image = self.bridge.imgmsg_to_cv2(self.latest_depth, 'passthrough')
            
            # Generate point cloud
            points_3d = self.depth_to_pointcloud(depth_image, self.camera_info)
            
            if points_3d.shape[0] < 100:  # Too few points
                return
                
            # Apply preprocessing pipeline
            filtered_points = self.preprocess_pipeline(points_3d, rgb_image)
            
            if filtered_points.shape[0] > 0:
                # Publish processed point cloud
                pc_msg = self.points_to_pointcloud2(filtered_points)
                pc_msg.header.stamp = self.get_clock().now().to_msg()
                pc_msg.header.frame_id = self.get_parameter('common.frames.camera').value
                self.pc_pub.publish(pc_msg)
                
                # Generate heightmap if enabled
                if self.get_parameter('pc_preprocess.heightmap.enable').value:
                    heightmap = self.generate_heightmap(filtered_points)
                    if heightmap is not None:
                        heightmap_msg = self.bridge.cv2_to_imgmsg(heightmap, 'mono8')
                        heightmap_msg.header = pc_msg.header
                        self.heightmap_pub.publish(heightmap_msg)
                        
        except Exception as e:
            self.get_logger().error(f'Processing error: {e}')

    def depth_to_pointcloud(self, depth_image, camera_info):
        """Convert depth image to 3D point cloud"""
        h, w = depth_image.shape
        
        # Intrinsic matrix
        fx = camera_info.k[0]
        fy = camera_info.k[4]
        cx = camera_info.k[2]
        cy = camera_info.k[5]
        
        # Create coordinate arrays
        u, v = np.meshgrid(np.arange(w), np.arange(h))
        
        # Valid depth mask
        valid_mask = (depth_image > 0) & (depth_image < 5000)  # 5m max
        
        # Extract valid pixels
        u_valid = u[valid_mask]
        v_valid = v[valid_mask]
        z_valid = depth_image[valid_mask] / 1000.0  # mm to m
        
        # Back-project to 3D
        x_valid = (u_valid - cx) * z_valid / fx
        y_valid = (v_valid - cy) * z_valid / fy
        
        points_3d = np.column_stack([x_valid, y_valid, z_valid])
        return points_3d

    def preprocess_pipeline(self, points_3d, rgb_image):
        """Apply preprocessing: plane removal → voxel → denoise → cluster"""
        if HAS_OPEN3D:
            return self._preprocess_open3d(points_3d)
        else:
            return self._preprocess_basic(points_3d)

    def _preprocess_open3d(self, points_3d):
        """Advanced preprocessing with Open3D"""
        # Convert to Open3D
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(points_3d)
        
        # Plane removal (table surface)
        if self.get_parameter('pc_preprocess.plane_remove.enable').value:
            plane_model, inliers = pcd.segment_plane(
                distance_threshold=self.get_parameter('pc_preprocess.plane_remove.dist_thresh_m').value,
                ransac_n=3,
                num_iterations=self.get_parameter('pc_preprocess.plane_remove.max_iter').value
            )
            pcd = pcd.select_by_index(inliers, invert=True)
        
        # Voxel downsampling
        voxel_size = self.get_parameter('pc_preprocess.voxel_size_m').value
        pcd = pcd.voxel_down_sample(voxel_size)
        
        # Statistical outlier removal
        if self.get_parameter('pc_preprocess.knn_denoise.enable').value:
            pcd, _ = pcd.remove_statistical_outlier(
                nb_neighbors=self.get_parameter('pc_preprocess.knn_denoise.k').value,
                std_ratio=self.get_parameter('pc_preprocess.knn_denoise.std_ratio').value
            )
        
        return np.asarray(pcd.points)

    def _preprocess_basic(self, points_3d):
        """Basic preprocessing without Open3D"""
        # Simple plane removal (remove points close to z=0 table)
        if self.get_parameter('pc_preprocess.plane_remove.enable').value:
            table_thresh = self.get_parameter('pc_preprocess.plane_remove.dist_thresh_m').value
            mask = np.abs(points_3d[:, 2]) > table_thresh
            points_3d = points_3d[mask]
        
        # Basic voxel downsampling
        voxel_size = self.get_parameter('pc_preprocess.voxel_size_m').value
        if points_3d.shape[0] > 1000:  # Only if enough points
            indices = np.arange(0, points_3d.shape[0], max(1, points_3d.shape[0] // 1000))
            points_3d = points_3d[indices]
        
        return points_3d

    def generate_heightmap(self, points_3d):
        """Generate top-down heightmap from point cloud"""
        if points_3d.shape[0] < 10:
            return None
            
        resolution = self.get_parameter('pc_preprocess.heightmap.resolution_m').value
        margin = self.get_parameter('pc_preprocess.heightmap.roi_margin_m').value
        
        # Find bounds
        x_min, x_max = points_3d[:, 0].min() - margin, points_3d[:, 0].max() + margin
        y_min, y_max = points_3d[:, 1].min() - margin, points_3d[:, 1].max() + margin
        
        # Grid dimensions
        w = int((x_max - x_min) / resolution)
        h = int((y_max - y_min) / resolution)
        
        if w <= 0 or h <= 0 or w > 1000 or h > 1000:
            return None
            
        # Initialize heightmap
        heightmap = np.zeros((h, w), dtype=np.float32)
        
        # Fill heightmap
        for point in points_3d:
            px = int((point[0] - x_min) / resolution)
            py = int((point[1] - y_min) / resolution)
            if 0 <= px < w and 0 <= py < h:
                heightmap[py, px] = max(heightmap[py, px], point[2])
        
        # Convert to uint8
        if heightmap.max() > 0:
            heightmap = ((heightmap / heightmap.max()) * 255).astype(np.uint8)
        
        return heightmap

    def points_to_pointcloud2(self, points_3d):
        """Convert numpy array to PointCloud2 message"""
        # This is a simplified conversion - in practice, use sensor_msgs_py or similar
        from sensor_msgs.msg import PointField
        import struct
        
        msg = PointCloud2()
        msg.height = 1
        msg.width = points_3d.shape[0]
        msg.is_dense = True
        msg.is_bigendian = False
        
        msg.fields = [
            PointField(name='x', offset=0, datatype=PointField.FLOAT32, count=1),
            PointField(name='y', offset=4, datatype=PointField.FLOAT32, count=1),
            PointField(name='z', offset=8, datatype=PointField.FLOAT32, count=1),
        ]
        msg.point_step = 12
        msg.row_step = msg.point_step * points_3d.shape[0]
        
        # Pack points
        buffer = []
        for point in points_3d:
            buffer.append(struct.pack('fff', point[0], point[1], point[2]))
        msg.data = b''.join(buffer)
        
        return msg


def main(args=None):
    rclpy.init(args=args)
    node = PCPreprocessNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()