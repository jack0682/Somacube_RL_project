#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from doosan_somacube_rl.msg import RegisterQuality
import numpy as np
from scipy.spatial.transform import Rotation as R
import tf2_ros
from collections import deque
import time


class PoseTrackerNode(Node):
    def __init__(self):
        super().__init__('pose_tracker')
        
        # Parameters
        self.declare_parameters_from_yaml()
        
        # State variables
        self.smoothed_pose = None
        self.smoothed_rotation_matrix = None
        self.pose_history = deque(maxlen=10)
        self.quality_history = deque(maxlen=10)
        self.last_timestamp = None
        
        # Subscribers
        self.pose_sub = self.create_subscription(
            PoseStamped,
            '/pc_register/pose',
            self.pose_callback,
            10
        )
        
        self.quality_sub = self.create_subscription(
            RegisterQuality,
            '/pc_register/quality',
            self.quality_callback,
            10
        )
        
        # Publishers
        self.smoothed_pose_pub = self.create_publisher(
            PoseStamped,
            '/pose_tracker/smoothed_pose',
            10
        )
        
        # Timer for publishing at constant rate
        rate_hz = self.get_parameter('common.realtime.node_rate_hz').value
        self.timer = self.create_timer(1.0 / rate_hz, self.publish_callback)
        
        self.get_logger().info('Pose Tracker node initialized')

    def declare_parameters_from_yaml(self):
        """Declare parameters from YAML config"""
        defaults = {
            'common.realtime.node_rate_hz': 100,
            'pose_tracker.smoothing.so3_method': 'exp_ema',
            'pose_tracker.smoothing.so3_alpha': 0.3,
            'pose_tracker.smoothing.pos_alpha': 0.3,
            'pose_tracker.outlier_rejection.max_geodesic_jump_deg': 8.0,
            'pose_tracker.outlier_rejection.max_pos_jump_m': 0.01,
            'pose_tracker.axis_flip_protect': True
        }
        
        for name, default_value in defaults.items():
            self.declare_parameter(name, default_value)

    def pose_callback(self, msg):
        """Handle incoming pose measurements"""
        try:
            current_time = time.time()
            
            # Extract pose
            position = np.array([
                msg.pose.position.x,
                msg.pose.position.y,
                msg.pose.position.z
            ])
            
            orientation = [
                msg.pose.orientation.x,
                msg.pose.orientation.y,
                msg.pose.orientation.z,
                msg.pose.orientation.w
            ]
            rotation_matrix = R.from_quat(orientation).as_matrix()
            
            # Outlier rejection
            if self.is_outlier(position, rotation_matrix):
                self.get_logger().warn('Outlier pose rejected')
                return
            
            # Store in history
            pose_data = {
                'timestamp': current_time,
                'position': position,
                'rotation': rotation_matrix,
                'msg': msg
            }
            self.pose_history.append(pose_data)
            
            # Update smoothed estimates
            self.update_smoothed_pose(position, rotation_matrix)
            
        except Exception as e:
            self.get_logger().error(f'Pose callback error: {e}')

    def quality_callback(self, msg):
        """Handle incoming quality metrics"""
        quality_data = {
            'timestamp': time.time(),
            'mean_point2plane_m': msg.mean_point2plane_m,
            'chamfer_bidir_m': msg.chamfer_bidir_m,
            'inlier_ratio': msg.inlier_ratio,
            'icp_residual_std': msg.icp_residual_std,
            'geodesic_deg': msg.geodesic_deg
        }
        self.quality_history.append(quality_data)

    def is_outlier(self, position, rotation_matrix):
        """Check if pose is an outlier based on jump thresholds"""
        if self.smoothed_pose is None or self.smoothed_rotation_matrix is None:
            return False  # No reference yet
        
        # Position jump check
        pos_jump = np.linalg.norm(position - self.smoothed_pose)
        max_pos_jump = self.get_parameter('pose_tracker.outlier_rejection.max_pos_jump_m').value
        if pos_jump > max_pos_jump:
            return True
        
        # Rotation jump check (geodesic distance)
        try:
            relative_rotation = rotation_matrix @ self.smoothed_rotation_matrix.T
            geodesic_angle = np.arccos(np.clip((np.trace(relative_rotation) - 1) / 2, -1, 1))
            geodesic_deg = np.rad2deg(geodesic_angle)
            
            max_geodesic_jump = self.get_parameter('pose_tracker.outlier_rejection.max_geodesic_jump_deg').value
            if geodesic_deg > max_geodesic_jump:
                return True
        except Exception as e:
            self.get_logger().warn(f'Geodesic computation error: {e}')
            return True  # Conservative: reject on error
        
        return False

    def update_smoothed_pose(self, position, rotation_matrix):
        """Update smoothed pose using SO(3) EMA"""
        pos_alpha = self.get_parameter('pose_tracker.smoothing.pos_alpha').value
        so3_alpha = self.get_parameter('pose_tracker.smoothing.so3_alpha').value
        
        # Initialize if first measurement
        if self.smoothed_pose is None:
            self.smoothed_pose = position.copy()
            self.smoothed_rotation_matrix = rotation_matrix.copy()
            return
        
        # Position EMA (Euclidean space)
        self.smoothed_pose = (1 - pos_alpha) * self.smoothed_pose + pos_alpha * position
        
        # SO(3) EMA on manifold
        method = self.get_parameter('pose_tracker.smoothing.so3_method').value
        
        if method == 'exp_ema':
            # Exponential map EMA on SO(3)
            relative_rotation = rotation_matrix @ self.smoothed_rotation_matrix.T
            
            # Axis-flip protection
            if self.get_parameter('pose_tracker.axis_flip_protect').value:
                if np.trace(relative_rotation) < 0:
                    # Choose closer rotation path
                    relative_rotation = -relative_rotation
            
            # Convert to axis-angle
            try:
                axis_angle = R.from_matrix(relative_rotation).as_rotvec()
                # Scale by alpha
                scaled_axis_angle = so3_alpha * axis_angle
                # Convert back to rotation matrix
                update_rotation = R.from_rotvec(scaled_axis_angle).as_matrix()
                # Update smoothed rotation
                self.smoothed_rotation_matrix = update_rotation @ self.smoothed_rotation_matrix
                
                # Ensure orthogonality (handle numerical drift)
                U, _, Vt = np.linalg.svd(self.smoothed_rotation_matrix)
                self.smoothed_rotation_matrix = U @ Vt
                
            except Exception as e:
                self.get_logger().warn(f'SO(3) EMA error: {e}')
                # Fallback to direct interpolation
                self.smoothed_rotation_matrix = rotation_matrix.copy()
        else:
            # Fallback: direct rotation matrix update
            self.smoothed_rotation_matrix = rotation_matrix.copy()

    def publish_callback(self):
        """Publish smoothed pose at constant rate"""
        if self.smoothed_pose is None or self.smoothed_rotation_matrix is None:
            return
        
        try:
            # Create pose message
            msg = PoseStamped()
            msg.header.stamp = self.get_clock().now().to_msg()
            msg.header.frame_id = 'camera_link'
            
            # Position
            msg.pose.position.x = float(self.smoothed_pose[0])
            msg.pose.position.y = float(self.smoothed_pose[1])
            msg.pose.position.z = float(self.smoothed_pose[2])
            
            # Orientation
            quat = R.from_matrix(self.smoothed_rotation_matrix).as_quat()  # [x,y,z,w]
            msg.pose.orientation.x = float(quat[0])
            msg.pose.orientation.y = float(quat[1])
            msg.pose.orientation.z = float(quat[2])
            msg.pose.orientation.w = float(quat[3])
            
            self.smoothed_pose_pub.publish(msg)
            
        except Exception as e:
            self.get_logger().error(f'Publish error: {e}')

    def get_pose_quality_score(self):
        """Compute overall pose quality score from recent measurements"""
        if not self.quality_history:
            return 0.0
        
        # Use most recent quality metrics
        recent_quality = self.quality_history[-1]
        
        # Composite score (higher is better)
        inlier_score = recent_quality['inlier_ratio']  # [0,1]
        distance_score = max(0, 1.0 - recent_quality['mean_point2plane_m'] / 0.01)  # 1cm threshold
        std_score = max(0, 1.0 - recent_quality['icp_residual_std'] / 0.005)  # 5mm std threshold
        geodesic_score = max(0, 1.0 - recent_quality['geodesic_deg'] / 10.0)  # 10 deg threshold
        
        # Weighted average
        weights = [0.4, 0.3, 0.2, 0.1]  # inlier, distance, std, geodesic
        scores = [inlier_score, distance_score, std_score, geodesic_score]
        
        overall_score = sum(w * s for w, s in zip(weights, scores))
        return np.clip(overall_score, 0.0, 1.0)

    def get_tracking_stability(self):
        """Assess pose tracking stability over recent history"""
        if len(self.pose_history) < 3:
            return 0.0
        
        # Compute pose variations over recent history
        recent_poses = list(self.pose_history)[-5:]  # Last 5 measurements
        
        positions = [p['position'] for p in recent_poses]
        rotations = [p['rotation'] for p in recent_poses]
        
        # Position stability (std deviation)
        pos_array = np.array(positions)
        pos_std = np.mean(np.std(pos_array, axis=0))
        pos_stability = max(0, 1.0 - pos_std / 0.005)  # 5mm threshold
        
        # Rotation stability (average geodesic distances)
        rot_variations = []
        for i in range(1, len(rotations)):
            try:
                rel_rot = rotations[i] @ rotations[i-1].T
                geodesic = np.arccos(np.clip((np.trace(rel_rot) - 1) / 2, -1, 1))
                rot_variations.append(np.rad2deg(geodesic))
            except:
                rot_variations.append(0.0)
        
        if rot_variations:
            avg_rot_variation = np.mean(rot_variations)
            rot_stability = max(0, 1.0 - avg_rot_variation / 2.0)  # 2 deg threshold
        else:
            rot_stability = 1.0
        
        # Combined stability
        stability = 0.6 * pos_stability + 0.4 * rot_stability
        return np.clip(stability, 0.0, 1.0)

    def get_current_pose_confidence(self):
        """Get current pose confidence for downstream nodes"""
        if self.smoothed_pose is None:
            return 0.0
        
        quality_score = self.get_pose_quality_score()
        stability_score = self.get_tracking_stability()
        
        # Recent measurement availability
        time_since_last = time.time() - (self.pose_history[-1]['timestamp'] if self.pose_history else 0)
        freshness_score = max(0, 1.0 - time_since_last / 1.0)  # 1 second timeout
        
        # Combined confidence
        confidence = 0.5 * quality_score + 0.3 * stability_score + 0.2 * freshness_score
        return np.clip(confidence, 0.0, 1.0)


def main(args=None):
    rclpy.init(args=args)
    node = PoseTrackerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()