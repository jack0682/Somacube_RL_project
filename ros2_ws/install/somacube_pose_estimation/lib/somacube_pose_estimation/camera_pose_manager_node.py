#!/usr/bin/env python3
"""
카메라 포즈 매니저 노드
SLAM 없이 미리 정의된 카메라 포즈들을 관리하고 global map 구성을 위한 좌표 변환 제공
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped, TransformStamped, Pose
from std_msgs.msg import String, Int32
import tf2_ros
import numpy as np
from scipy.spatial.transform import Rotation as R
import yaml
import json
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional


class CameraPoseManagerNode(Node):
    """미리 정의된 카메라 포즈 관리 및 글로벌 맵 구성"""
    
    def __init__(self):
        super().__init__('camera_pose_manager')
        
        # Parameters
        self.declare_parameters_from_yaml()
        
        # TF broadcaster
        self.tf_broadcaster = tf2_ros.TransformBroadcaster(self)
        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)
        
        # Camera calibration data
        self.T_gripper2camera = self.load_gripper_camera_calibration()
        
        # Predefined camera poses
        self.camera_poses = self.load_predefined_poses()
        self.current_pose_index = 0
        self.current_pose = None
        
        # Publishers
        self.current_pose_pub = self.create_publisher(
            PoseStamped,
            '/camera_pose_manager/current_pose',
            10
        )
        
        self.pose_list_pub = self.create_publisher(
            String,
            '/camera_pose_manager/pose_list',
            10
        )
        
        self.global_map_status_pub = self.create_publisher(
            String,
            '/camera_pose_manager/global_map_status',
            10
        )
        
        # Subscribers for external control
        self.pose_index_sub = self.create_subscription(
            Int32,
            '/camera_pose_manager/set_pose_index',
            self.set_pose_index_callback,
            10
        )
        
        self.manual_pose_sub = self.create_subscription(
            PoseStamped,
            '/camera_pose_manager/set_manual_pose',
            self.manual_pose_callback,
            10
        )
        
        # Service-like behavior through topics
        self.next_pose_sub = self.create_subscription(
            String,
            '/camera_pose_manager/next_pose',
            self.next_pose_callback,
            10
        )
        
        self.prev_pose_sub = self.create_subscription(
            String,
            '/camera_pose_manager/prev_pose',
            self.prev_pose_callback,
            10
        )
        
        # Global map data
        self.global_objects = {}  # pose_id -> list of detected objects
        self.global_pointclouds = {}  # pose_id -> point cloud data
        
        # Timer for publishing current pose and TF
        self.timer = self.create_timer(0.1, self.publish_current_pose)  # 10Hz
        
        # Initialize with first pose
        if self.camera_poses:
            self.set_current_pose(0)
            
        self.get_logger().info(f'Camera Pose Manager initialized with {len(self.camera_poses)} poses')
        self.publish_pose_list()

    def declare_parameters_from_yaml(self):
        """YAML 설정에서 파라미터 선언"""
        defaults = {
            'common.frames.base': 'base_link',
            'common.frames.world': 'world',
            'common.frames.camera': 'camera_link',
            
            'camera_pose_manager.pose_file': 'config/camera_poses.yaml',
            'camera_pose_manager.auto_tf_broadcast': True,
            'camera_pose_manager.global_map_frame': 'world',
            
            # Default camera positions (multi-view setup)
            'camera_pose_manager.default_poses': {
                'front_high': {
                    'position': [0.5, 0.0, 0.8],
                    'orientation': [0.0, -0.3, 0.0, 0.95],  # x,y,z,w quaternion
                    'description': 'Front view, elevated'
                },
                'left_side': {
                    'position': [0.0, 0.5, 0.6],
                    'orientation': [0.0, 0.0, 0.7, 0.7],
                    'description': 'Left side view'
                },
                'right_side': {
                    'position': [0.0, -0.5, 0.6],
                    'orientation': [0.0, 0.0, -0.7, 0.7],
                    'description': 'Right side view'
                },
                'top_down': {
                    'position': [0.0, 0.0, 1.2],
                    'orientation': [0.0, 0.0, 0.0, 1.0],
                    'description': 'Top-down view'
                },
                'angled_corner': {
                    'position': [0.4, 0.4, 0.7],
                    'orientation': [0.0, -0.2, 0.4, 0.9],
                    'description': 'Corner angled view'
                }
            }
        }
        
        for name, default_value in defaults.items():
            self.declare_parameter(name, default_value)

    def load_predefined_poses(self) -> List[Dict]:
        """미리 정의된 카메라 포즈들 로드"""
        pose_file = self.get_parameter('camera_pose_manager.pose_file').value
        
        try:
            # Try to load from file first
            with open(pose_file, 'r') as f:
                pose_data = yaml.safe_load(f)
                poses = pose_data.get('camera_poses', [])
                self.get_logger().info(f'Loaded {len(poses)} poses from {pose_file}')
                return poses
        except (FileNotFoundError, yaml.YAMLError) as e:
            self.get_logger().warn(f'Could not load poses from {pose_file}: {e}')
            
        # Use default poses from parameters
        default_poses_param = self.get_parameter('camera_pose_manager.default_poses').value
        poses = []
        
        for pose_id, pose_data in default_poses_param.items():
            pose = {
                'id': pose_id,
                'position': pose_data['position'],
                'orientation': pose_data['orientation'],
                'description': pose_data.get('description', ''),
                'frame_id': 'world'
            }
            poses.append(pose)
            
        self.get_logger().info(f'Using {len(poses)} default poses')
        return poses

    def save_poses_to_file(self):
        """현재 포즈들을 파일로 저장"""
        pose_file = self.get_parameter('camera_pose_manager.pose_file').value
        
        pose_data = {
            'camera_poses': self.camera_poses,
            'metadata': {
                'created_by': 'camera_pose_manager_node',
                'total_poses': len(self.camera_poses),
                'frame_id': 'world'
            }
        }
        
        try:
            with open(pose_file, 'w') as f:
                yaml.dump(pose_data, f, default_flow_style=False)
            self.get_logger().info(f'Saved {len(self.camera_poses)} poses to {pose_file}')
        except Exception as e:
            self.get_logger().error(f'Failed to save poses: {e}')

    def set_current_pose(self, index: int) -> bool:
        """현재 포즈 설정"""
        if 0 <= index < len(self.camera_poses):
            self.current_pose_index = index
            self.current_pose = self.camera_poses[index].copy()
            
            self.get_logger().info(
                f'Set pose {index}: {self.current_pose.get("description", "")} '
                f'at {self.current_pose["position"]}'
            )
            return True
        return False

    def set_pose_index_callback(self, msg):
        """포즈 인덱스 설정 콜백"""
        if self.set_current_pose(msg.data):
            self.publish_global_map_status()

    def manual_pose_callback(self, msg):
        """수동 포즈 설정 콜백"""
        # Convert PoseStamped to our pose format
        manual_pose = {
            'id': f'manual_{len(self.camera_poses)}',
            'position': [
                msg.pose.position.x,
                msg.pose.position.y,
                msg.pose.position.z
            ],
            'orientation': [
                msg.pose.orientation.x,
                msg.pose.orientation.y,
                msg.pose.orientation.z,
                msg.pose.orientation.w
            ],
            'description': 'Manually set pose',
            'frame_id': msg.header.frame_id or 'world'
        }
        
        # Add to pose list
        self.camera_poses.append(manual_pose)
        self.current_pose_index = len(self.camera_poses) - 1
        self.current_pose = manual_pose
        
        self.get_logger().info(f'Added manual pose: {manual_pose["position"]}')
        self.publish_pose_list()
        self.publish_global_map_status()

    def next_pose_callback(self, msg):
        """다음 포즈로 이동"""
        next_index = (self.current_pose_index + 1) % len(self.camera_poses)
        self.set_current_pose(next_index)

    def prev_pose_callback(self, msg):
        """이전 포즈로 이동"""
        prev_index = (self.current_pose_index - 1) % len(self.camera_poses)
        self.set_current_pose(prev_index)

    def publish_current_pose(self):
        """현재 포즈 발행 및 TF 브로드캐스트"""
        if self.current_pose is None:
            return
            
        # Publish current pose
        pose_msg = PoseStamped()
        pose_msg.header.stamp = self.get_clock().now().to_msg()
        pose_msg.header.frame_id = self.current_pose.get('frame_id', 'world')
        
        # Position
        pos = self.current_pose['position']
        pose_msg.pose.position.x = float(pos[0])
        pose_msg.pose.position.y = float(pos[1])
        pose_msg.pose.position.z = float(pos[2])
        
        # Orientation
        ori = self.current_pose['orientation']
        pose_msg.pose.orientation.x = float(ori[0])
        pose_msg.pose.orientation.y = float(ori[1])
        pose_msg.pose.orientation.z = float(ori[2])
        pose_msg.pose.orientation.w = float(ori[3])
        
        self.current_pose_pub.publish(pose_msg)
        
        # Broadcast TF if enabled
        if self.get_parameter('camera_pose_manager.auto_tf_broadcast').value:
            self.broadcast_camera_tf(pose_msg)

    def broadcast_camera_tf(self, pose_msg: PoseStamped):
        """카메라 TF 브로드캐스트"""
        tf_msg = TransformStamped()
        tf_msg.header = pose_msg.header
        tf_msg.child_frame_id = self.get_parameter('common.frames.camera').value
        
        # Copy pose to transform
        tf_msg.transform.translation.x = pose_msg.pose.position.x
        tf_msg.transform.translation.y = pose_msg.pose.position.y
        tf_msg.transform.translation.z = pose_msg.pose.position.z
        
        tf_msg.transform.rotation = pose_msg.pose.orientation
        
        self.tf_broadcaster.sendTransform(tf_msg)

    def publish_pose_list(self):
        """포즈 목록 발행"""
        pose_list_data = {
            'total_poses': len(self.camera_poses),
            'current_index': self.current_pose_index,
            'poses': []
        }
        
        for i, pose in enumerate(self.camera_poses):
            pose_info = {
                'index': i,
                'id': pose.get('id', f'pose_{i}'),
                'description': pose.get('description', ''),
                'position': pose['position'],
                'orientation': pose['orientation'],
                'is_current': i == self.current_pose_index
            }
            pose_list_data['poses'].append(pose_info)
            
        json_msg = String()
        json_msg.data = json.dumps(pose_list_data, indent=2)
        self.pose_list_pub.publish(json_msg)

    def publish_global_map_status(self):
        """글로벌 맵 상태 발행"""
        status_data = {
            'current_pose_index': self.current_pose_index,
            'total_poses': len(self.camera_poses),
            'global_objects_count': len(self.global_objects),
            'poses_with_data': list(self.global_objects.keys()),
            'current_pose_info': self.current_pose
        }
        
        json_msg = String()
        json_msg.data = json.dumps(status_data, indent=2)
        self.global_map_status_pub.publish(json_msg)

    def transform_pose_to_global(self, local_pose: np.ndarray, 
                                camera_pose_index: Optional[int] = None) -> np.ndarray:
        """로컬 포즈를 글로벌 좌표계로 변환"""
        if camera_pose_index is None:
            camera_pose_index = self.current_pose_index
            
        if camera_pose_index >= len(self.camera_poses):
            return local_pose
            
        camera_pose = self.camera_poses[camera_pose_index]
        
        # 카메라 포즈 행렬 구성
        pos = np.array(camera_pose['position'])
        quat = camera_pose['orientation']  # [x,y,z,w]
        
        # Rotation matrix from quaternion
        rot = R.from_quat(quat).as_matrix()
        
        # 4x4 homogeneous transformation matrix
        T_world_camera = np.eye(4)
        T_world_camera[:3, :3] = rot
        T_world_camera[:3, 3] = pos
        
        # Transform local pose to global
        if local_pose.shape == (4, 4):
            # If local_pose is already 4x4 matrix
            global_pose = T_world_camera @ local_pose
        else:
            # If local_pose is position vector
            local_homo = np.append(local_pose, 1)
            global_homo = T_world_camera @ local_homo
            global_pose = global_homo[:3]
            
        return global_pose

    def add_global_object(self, object_data: Dict, pose_index: Optional[int] = None):
        """글로벌 맵에 객체 추가"""
        if pose_index is None:
            pose_index = self.current_pose_index
            
        if pose_index not in self.global_objects:
            self.global_objects[pose_index] = []
            
        # Transform object pose to global coordinates
        if 'pose' in object_data:
            local_pose_matrix = self.pose_dict_to_matrix(object_data['pose'])
            global_pose_matrix = self.transform_pose_to_global(local_pose_matrix, pose_index)
            object_data['global_pose'] = self.matrix_to_pose_dict(global_pose_matrix)
            
        self.global_objects[pose_index].append(object_data)
        self.get_logger().debug(f'Added object to global map at pose {pose_index}')

    def pose_dict_to_matrix(self, pose_dict: Dict) -> np.ndarray:
        """포즈 딕셔너리를 4x4 행렬로 변환"""
        pos = pose_dict.get('position', [0, 0, 0])
        ori = pose_dict.get('orientation', [0, 0, 0, 1])  # [x,y,z,w]
        
        T = np.eye(4)
        T[:3, :3] = R.from_quat(ori).as_matrix()
        T[:3, 3] = pos
        return T

    def matrix_to_pose_dict(self, matrix: np.ndarray) -> Dict:
        """4x4 행렬을 포즈 딕셔너리로 변환"""
        pos = matrix[:3, 3]
        rot_matrix = matrix[:3, :3]
        quat = R.from_matrix(rot_matrix).as_quat()  # [x,y,z,w]
        
        return {
            'position': pos.tolist(),
            'orientation': quat.tolist()
        }

    def get_all_global_objects(self) -> List[Dict]:
        """모든 글로벌 객체 반환"""
        all_objects = []
        for pose_index, objects in self.global_objects.items():
            for obj in objects:
                obj_copy = obj.copy()
                obj_copy['source_pose_index'] = pose_index
                all_objects.append(obj_copy)
        return all_objects

    def clear_global_map(self):
        """글로벌 맵 초기화"""
        self.global_objects.clear()
        self.global_pointclouds.clear()
        self.get_logger().info('Global map cleared')
        self.publish_global_map_status()

    def load_gripper_camera_calibration(self) -> np.ndarray:
        """DoosanRobotics M0609 gripper-to-camera calibration 로드"""
        try:
            # Default calibration file path
            calibration_path = "/home/jack/ros2_ws/src/DoosanBootcamp3rd/dsr_rokey/pick_and_place_text/resource/T_gripper2camera.npy"
            
            if os.path.exists(calibration_path):
                T_gripper2camera = np.load(calibration_path)
                self.get_logger().info(f"Loaded gripper-to-camera calibration from: {calibration_path}")
                self.get_logger().info(f"Translation: {T_gripper2camera[:3, 3]}")
                
                # Log rotation as Euler angles
                rot_matrix = T_gripper2camera[:3, :3]
                r = R.from_matrix(rot_matrix)
                euler_deg = r.as_euler('xyz', degrees=True)
                self.get_logger().info(f"Rotation (XYZ Euler degrees): {euler_deg}")
                
                return T_gripper2camera
            else:
                self.get_logger().warn(f"Calibration file not found: {calibration_path}")
                self.get_logger().warn("Using identity transformation")
                return np.eye(4)
                
        except Exception as e:
            self.get_logger().error(f"Failed to load calibration file: {e}")
            self.get_logger().warn("Using identity transformation")
            return np.eye(4)

    def get_camera_pose_from_gripper(self, gripper_pose: np.ndarray) -> np.ndarray:
        """Gripper 포즈에서 카메라 포즈 계산"""
        # T_base_camera = T_base_gripper @ T_gripper_camera
        if gripper_pose.shape == (4, 4):
            T_base_gripper = gripper_pose
        else:
            # gripper_pose가 [x,y,z,rx,ry,rz] 형태라면 변환
            T_base_gripper = np.eye(4)
            T_base_gripper[:3, 3] = gripper_pose[:3]
            if len(gripper_pose) > 3:
                # Euler angles to rotation matrix
                euler = gripper_pose[3:6]
                T_base_gripper[:3, :3] = R.from_euler('xyz', euler, degrees=True).as_matrix()
                
        # Calculate camera pose
        T_base_camera = T_base_gripper @ self.T_gripper2camera
        return T_base_camera

    def transform_pose_with_calibration(self, pose_in_camera: np.ndarray, 
                                      gripper_pose: np.ndarray) -> np.ndarray:
        """Calibration을 고려한 포즈 변환"""
        # Camera frame에서 gripper frame으로 변환
        T_gripper_camera_inv = np.linalg.inv(self.T_gripper2camera)
        
        if pose_in_camera.shape == (4, 4):
            pose_in_gripper = T_gripper_camera_inv @ pose_in_camera
        else:
            # Position vector
            pose_homo = np.append(pose_in_camera, 1)
            pose_in_gripper_homo = T_gripper_camera_inv @ pose_homo
            pose_in_gripper = pose_in_gripper_homo[:3]
            
        # Gripper frame에서 base frame으로 변환
        T_base_gripper = gripper_pose if gripper_pose.shape == (4, 4) else self.pose_to_matrix(gripper_pose)
        
        if pose_in_gripper.shape == (4, 4):
            pose_in_base = T_base_gripper @ pose_in_gripper
        else:
            pose_homo = np.append(pose_in_gripper, 1)
            pose_in_base_homo = T_base_gripper @ pose_homo
            pose_in_base = pose_in_base_homo[:3]
            
        return pose_in_base

    def pose_to_matrix(self, pose: np.ndarray) -> np.ndarray:
        """포즈 벡터를 4x4 매트릭스로 변환"""
        T = np.eye(4)
        T[:3, 3] = pose[:3]
        if len(pose) > 3:
            if len(pose) == 6:
                # [x,y,z,rx,ry,rz] format
                T[:3, :3] = R.from_euler('xyz', pose[3:6], degrees=True).as_matrix()
            elif len(pose) == 7:
                # [x,y,z,qx,qy,qz,qw] format
                T[:3, :3] = R.from_quat(pose[3:7]).as_matrix()
        return T


def main(args=None):
    rclpy.init(args=args)
    node = CameraPoseManagerNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        # Save poses before shutting down
        node.save_poses_to_file()
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()