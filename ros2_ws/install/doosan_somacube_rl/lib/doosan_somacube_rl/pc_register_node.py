#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from sensor_msgs.msg import PointCloud2
from geometry_msgs.msg import PoseStamped
from doosan_somacube_rl.msg import RegisterQuality
import numpy as np
from scipy.spatial.transform import Rotation as R
import tf2_ros
import tf2_geometry_msgs
from builtin_interfaces.msg import Time

try:
    import open3d as o3d
    HAS_OPEN3D = True
except ImportError:
    HAS_OPEN3D = False


class PCRegisterNode(Node):
    def __init__(self):
        super().__init__('pc_register')
        
        # Parameters
        self.declare_parameters_from_yaml()
        
        # TF buffer
        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)
        
        # QoS profiles
        sensor_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=5
        )
        
        # Subscribers
        self.pc_sub = self.create_subscription(
            PointCloud2,
            '/pc_preprocess/output',
            self.pc_callback,
            sensor_qos
        )
        
        # Publishers
        self.pose_pub = self.create_publisher(
            PoseStamped,
            self.get_parameter('pc_register.outputs.publish_pose_topic').value,
            10
        )
        
        self.quality_pub = self.create_publisher(
            RegisterQuality,
            self.get_parameter('pc_register.outputs.publish_quality_topic').value,
            10
        )
        
        # State
        self.template_pc = None
        self.latest_pc = None
        self.current_target_pose = None
        
        # 24-rotation group (cube symmetries)
        self.rot_24_group = self.generate_24_rotations()
        
        # Timer for processing
        rate_hz = self.get_parameter('common.realtime.register_rate_hz').value
        self.timer = self.create_timer(1.0 / rate_hz, self.process_callback)
        
        # Load template point cloud (placeholder - in practice load from file/service)
        self.load_template_pointcloud()
        
        self.get_logger().info('PC Register node initialized')

    def declare_parameters_from_yaml(self):
        """Declare parameters from YAML config"""
        defaults = {
            'common.realtime.register_rate_hz': 30,
            'common.frames.base': 'base',
            'common.frames.camera': 'camera_link',
            'pc_register.rot24_initialization': True,
            'pc_register.coarse.method': 'ransac_fpfh',
            'pc_register.coarse.normal_radius_m': 0.01,
            'pc_register.coarse.fpfh_radius_m': 0.02,
            'pc_register.coarse.voxel_down_m': 0.006,
            'pc_register.coarse.ransac.max_iter': 4000,
            'pc_register.coarse.ransac.inlier_thresh_m': 0.006,
            'pc_register.coarse.ransac.confidence': 0.999,
            'pc_register.refine.method': 'icp_point_to_plane',
            'pc_register.refine.max_iter': 60,
            'pc_register.refine.max_corr_dist_m': 0.008,
            'pc_register.refine.trans_eps': 1.0e-4,
            'pc_register.refine.rot_eps_rad': 1.0e-3,
            'pc_register.outputs.publish_pose_topic': '/pc_register/pose',
            'pc_register.outputs.publish_quality_topic': '/pc_register/quality'
        }
        
        for name, default_value in defaults.items():
            self.declare_parameter(name, default_value)

    def generate_24_rotations(self):
        """Generate 24-element rotation group for cube symmetries"""
        rotations = []
        
        # Face rotations (6 faces × 4 orientations each)
        faces = [
            [0, 0, 0],      # +Z up
            [0, 0, 90],     
            [0, 0, 180],    
            [0, 0, 270],    
            [0, 90, 0],     # +Y up
            [0, 90, 90],    
            [0, 90, 180],   
            [0, 90, 270],   
            [0, -90, 0],    # -Y up
            [0, -90, 90],   
            [0, -90, 180],  
            [0, -90, 270],  
            [90, 0, 0],     # +X up
            [90, 0, 90],    
            [90, 0, 180],   
            [90, 0, 270],   
            [-90, 0, 0],    # -X up
            [-90, 0, 90],   
            [-90, 0, 180],  
            [-90, 0, 270],  
            [0, 180, 0],    # -Z up
            [0, 180, 90],   
            [0, 180, 180],  
            [0, 180, 270]   
        ]
        
        for rpy in faces:
            rot_matrix = R.from_euler('xyz', np.deg2rad(rpy)).as_matrix()
            rotations.append(rot_matrix)
            
        return rotations

    def load_template_pointcloud(self):
        """Load template point cloud for soma cube piece"""
        # Placeholder: generate simple cube template
        # In practice, load from file or service call
        size = 0.02  # 2cm cube
        points = []
        
        # Generate cube vertices and faces
        for x in [-size/2, size/2]:
            for y in [-size/2, size/2]:
                for z in [-size/2, size/2]:
                    points.append([x, y, z])
        
        # Add face centers and edge points for better registration
        for i in range(10):
            for j in range(10):
                # Top/bottom faces
                x = -size/2 + (size * i / 9)
                y = -size/2 + (size * j / 9)
                points.append([x, y, size/2])
                points.append([x, y, -size/2])
                
        self.template_pc = np.array(points)
        self.get_logger().info(f'Loaded template PC with {len(points)} points')

    def pc_callback(self, msg):
        """Store latest point cloud"""
        try:
            self.latest_pc = self.pointcloud2_to_points(msg)
        except Exception as e:
            self.get_logger().error(f'PC conversion error: {e}')

    def pointcloud2_to_points(self, msg):
        """Convert PointCloud2 to numpy array"""
        import struct
        
        points = []
        step = msg.point_step
        
        for i in range(0, len(msg.data), step):
            x, y, z = struct.unpack('fff', msg.data[i:i+12])
            points.append([x, y, z])
            
        return np.array(points)

    def process_callback(self):
        """Main registration processing loop"""
        if self.latest_pc is None or self.template_pc is None:
            return
            
        if self.latest_pc.shape[0] < 50:  # Too few points
            return
            
        try:
            # Perform registration
            best_pose, quality_metrics = self.register_pointclouds(
                self.template_pc, self.latest_pc
            )
            
            if best_pose is not None:
                # Publish pose
                pose_msg = PoseStamped()
                pose_msg.header.stamp = self.get_clock().now().to_msg()
                pose_msg.header.frame_id = self.get_parameter('common.frames.camera').value
                
                # Convert matrix to pose
                pose_msg.pose.position.x = best_pose[0, 3]
                pose_msg.pose.position.y = best_pose[1, 3]
                pose_msg.pose.position.z = best_pose[2, 3]
                
                quat = R.from_matrix(best_pose[:3, :3]).as_quat()  # [x,y,z,w]
                pose_msg.pose.orientation.x = quat[0]
                pose_msg.pose.orientation.y = quat[1]
                pose_msg.pose.orientation.z = quat[2]
                pose_msg.pose.orientation.w = quat[3]
                
                self.pose_pub.publish(pose_msg)
                
                # Publish quality metrics
                quality_msg = RegisterQuality()
                quality_msg.stamp = pose_msg.header.stamp
                quality_msg.mean_point2plane_m = quality_metrics['mean_point2plane_m']
                quality_msg.chamfer_bidir_m = quality_metrics['chamfer_bidir_m']
                quality_msg.inlier_ratio = quality_metrics['inlier_ratio']
                quality_msg.icp_residual_std = quality_metrics['icp_residual_std']
                quality_msg.geodesic_deg = quality_metrics['geodesic_deg']
                
                self.quality_pub.publish(quality_msg)
                
        except Exception as e:
            self.get_logger().error(f'Registration error: {e}')

    def register_pointclouds(self, template_pc, scene_pc):
        """Main registration pipeline with 24-rotation coarse + ICP refinement"""
        if HAS_OPEN3D:
            return self._register_open3d(template_pc, scene_pc)
        else:
            return self._register_basic(template_pc, scene_pc)

    def _register_open3d(self, template_pc, scene_pc):
        """Advanced registration using Open3D"""
        # Convert to Open3D
        template_pcd = o3d.geometry.PointCloud()
        template_pcd.points = o3d.utility.Vector3dVector(template_pc)
        
        scene_pcd = o3d.geometry.PointCloud()
        scene_pcd.points = o3d.utility.Vector3dVector(scene_pc)
        
        # Downsample for coarse registration
        voxel_size = self.get_parameter('pc_register.coarse.voxel_down_m').value
        template_down = template_pcd.voxel_down_sample(voxel_size)
        scene_down = scene_pcd.voxel_down_sample(voxel_size)
        
        # Compute normals
        normal_radius = self.get_parameter('pc_register.coarse.normal_radius_m').value
        template_down.estimate_normals(o3d.geometry.KDTreeSearchParamHybrid(normal_radius, 30))
        scene_down.estimate_normals(o3d.geometry.KDTreeSearchParamHybrid(normal_radius, 30))
        
        # Compute FPFH features
        fpfh_radius = self.get_parameter('pc_register.coarse.fpfh_radius_m').value
        template_fpfh = o3d.pipelines.registration.compute_fpfh_feature(
            template_down, o3d.geometry.KDTreeSearchParamHybrid(fpfh_radius, 100)
        )
        scene_fpfh = o3d.pipelines.registration.compute_fpfh_feature(
            scene_down, o3d.geometry.KDTreeSearchParamHybrid(fpfh_radius, 100)
        )
        
        best_fitness = -1
        best_transformation = None
        
        # Try 24 rotations if enabled
        rotations_to_try = self.rot_24_group if self.get_parameter('pc_register.rot24_initialization').value else [np.eye(3)]
        
        for rot_init in rotations_to_try:
            # Apply initial rotation
            init_transform = np.eye(4)
            init_transform[:3, :3] = rot_init
            
            template_rot = template_down.transform(init_transform)
            template_fpfh_rot = o3d.pipelines.registration.compute_fpfh_feature(
                template_rot, o3d.geometry.KDTreeSearchParamHybrid(fpfh_radius, 100)
            )
            
            # RANSAC coarse registration
            result_ransac = o3d.pipelines.registration.registration_ransac_based_on_feature_matching(
                template_rot, scene_down,
                template_fpfh_rot, scene_fpfh,
                mutual_filter=True,
                max_correspondence_distance=self.get_parameter('pc_register.coarse.ransac.inlier_thresh_m').value,
                estimation_method=o3d.pipelines.registration.TransformationEstimationPointToPoint(False),
                ransac_n=3,
                checkers=[
                    o3d.pipelines.registration.CorrespondenceCheckerBasedOnEdgeLength(0.9),
                    o3d.pipelines.registration.CorrespondenceCheckerBasedOnDistance(
                        self.get_parameter('pc_register.coarse.ransac.inlier_thresh_m').value
                    )
                ],
                criteria=o3d.pipelines.registration.RANSACConvergenceCriteria(
                    self.get_parameter('pc_register.coarse.ransac.max_iter').value,
                    self.get_parameter('pc_register.coarse.ransac.confidence').value
                )
            )
            
            if result_ransac.fitness > best_fitness:
                best_fitness = result_ransac.fitness
                # Combine initial rotation with RANSAC result
                best_transformation = result_ransac.transformation @ init_transform
        
        if best_transformation is None:
            return None, {}
        
        # ICP refinement
        max_corr_dist = self.get_parameter('pc_register.refine.max_corr_dist_m').value
        
        # Point-to-plane ICP
        template_pcd.estimate_normals(o3d.geometry.KDTreeSearchParamHybrid(normal_radius, 30))
        scene_pcd.estimate_normals(o3d.geometry.KDTreeSearchParamHybrid(normal_radius, 30))
        
        result_icp = o3d.pipelines.registration.registration_icp(
            template_pcd, scene_pcd,
            max_corr_dist, best_transformation,
            o3d.pipelines.registration.TransformationEstimationPointToPlane(),
            o3d.pipelines.registration.ICPConvergenceCriteria(
                max_iteration=self.get_parameter('pc_register.refine.max_iter').value
            )
        )
        
        # Compute quality metrics
        quality_metrics = self._compute_quality_metrics(
            template_pcd, scene_pcd, result_icp.transformation
        )
        
        return result_icp.transformation, quality_metrics

    def _register_basic(self, template_pc, scene_pc):
        """Basic registration fallback without Open3D"""
        # Simple centroid alignment with best rotation from 24-group
        template_centroid = np.mean(template_pc, axis=0)
        scene_centroid = np.mean(scene_pc, axis=0)
        
        # Center point clouds
        template_centered = template_pc - template_centroid
        scene_centered = scene_pc - scene_centroid
        
        best_error = float('inf')
        best_rotation = np.eye(3)
        
        # Try 24 rotations
        for rot_matrix in self.rot_24_group[:6]:  # Subset for speed
            template_rot = template_centered @ rot_matrix.T
            
            # Simple nearest neighbor matching
            if template_rot.shape[0] > 0 and scene_centered.shape[0] > 0:
                from scipy.spatial.distance import cdist
                distances = cdist(template_rot, scene_centered)
                min_distances = np.min(distances, axis=1)
                error = np.mean(min_distances)
                
                if error < best_error:
                    best_error = error
                    best_rotation = rot_matrix
        
        # Construct transformation matrix
        transformation = np.eye(4)
        transformation[:3, :3] = best_rotation
        transformation[:3, 3] = scene_centroid - best_rotation @ template_centroid
        
        # Basic quality metrics
        quality_metrics = {
            'mean_point2plane_m': best_error,
            'chamfer_bidir_m': best_error,
            'inlier_ratio': 0.5,  # Placeholder
            'icp_residual_std': best_error * 0.5,
            'geodesic_deg': 0.0  # Placeholder
        }
        
        return transformation, quality_metrics

    def _compute_quality_metrics(self, template_pcd, scene_pcd, transformation):
        """Compute registration quality metrics"""
        # Transform template
        template_transformed = template_pcd.transform(transformation)
        
        # Point-to-plane distances
        distances = []
        template_points = np.asarray(template_transformed.points)
        template_normals = np.asarray(template_transformed.normals)
        scene_points = np.asarray(scene_pcd.points)
        
        if len(template_points) > 0 and len(scene_points) > 0:
            from scipy.spatial import KDTree
            tree = KDTree(scene_points)
            
            for i, (point, normal) in enumerate(zip(template_points, template_normals)):
                dist, idx = tree.query(point, k=1)
                if dist < 0.02:  # Only close correspondences
                    closest_point = scene_points[idx]
                    point_to_plane_dist = abs(np.dot(point - closest_point, normal))
                    distances.append(point_to_plane_dist)
        
        if len(distances) == 0:
            distances = [0.01]  # Fallback
        
        # Compute metrics
        mean_point2plane = np.mean(distances)
        icp_residual_std = np.std(distances)
        inlier_ratio = len(distances) / max(len(template_points), 1)
        
        # Geodesic distance (rotation error)
        rotation_part = transformation[:3, :3]
        try:
            geodesic_deg = np.rad2deg(np.arccos((np.trace(rotation_part) - 1) / 2))
            if np.isnan(geodesic_deg):
                geodesic_deg = 0.0
        except:
            geodesic_deg = 0.0
        
        # Chamfer distance (bidirectional)
        chamfer_bidir = mean_point2plane  # Simplified
        
        return {
            'mean_point2plane_m': float(mean_point2plane),
            'chamfer_bidir_m': float(chamfer_bidir),
            'inlier_ratio': float(inlier_ratio),
            'icp_residual_std': float(icp_residual_std),
            'geodesic_deg': float(geodesic_deg)
        }


def main(args=None):
    rclpy.init(args=args)
    node = PCRegisterNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()