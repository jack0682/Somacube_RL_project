#!/usr/bin/env python3
"""
시각화 노드
수학적 정밀 체계의 결과 시각화 및 디버깅 지원
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from geometry_msgs.msg import PoseArray, Pose
from visualization_msgs.msg import Marker, MarkerArray
import numpy as np
import json
from scipy.spatial.transform import Rotation as R
from typing import Dict, List, Optional


class VisualizationNode(Node):
    """포즈 추정 결과 시각화"""
    
    def __init__(self):
        super().__init__('pose_visualization')
        
        # Parameters
        self.declare_parameters_from_yaml()
        
        # Subscribers
        self.fused_poses_sub = self.create_subscription(
            String,
            '/multiview_fusion/fused_poses',
            self.fused_poses_callback,
            10
        )
        
        self.global_poses_sub = self.create_subscription(
            String,
            '/multiview_fusion/global_poses',
            self.global_poses_callback,
            10
        )
        
        self.fusion_metrics_sub = self.create_subscription(
            String,
            '/multiview_fusion/fusion_metrics',
            self.fusion_metrics_callback,
            10
        )
        
        # Publishers
        self.pose_array_pub = self.create_publisher(
            PoseArray,
            '/multiview_fusion/pose_array',
            10
        )
        
        self.obb_markers_pub = self.create_publisher(
            MarkerArray,
            '/visualization/obb_markers',
            10
        )
        
        self.quality_markers_pub = self.create_publisher(
            MarkerArray,
            '/visualization/quality_markers',
            10
        )
        
        self.text_markers_pub = self.create_publisher(
            MarkerArray,
            '/visualization/text_markers',
            10
        )
        
        # State
        self.latest_fused_poses = []
        self.latest_global_poses = {}
        self.latest_metrics = []
        
        # Timer for visualization updates
        viz_rate = self.get_parameter('visualization.update_rate_hz').value
        self.timer = self.create_timer(1.0 / viz_rate, self.update_visualization)
        
        self.get_logger().info('Visualization node initialized')

    def declare_parameters_from_yaml(self):
        """YAML 설정에서 파라미터 선언"""
        defaults = {
            'common.frames.world': 'world',
            'common.frames.camera': 'camera_link',
            
            'visualization.update_rate_hz': 10.0,
            'visualization.enable_pose_array': True,
            'visualization.enable_obb_markers': True,
            'visualization.enable_quality_markers': True,
            'visualization.enable_text_labels': True,
            
            # 마커 스타일
            'visualization.markers.obb_alpha': 0.3,
            'visualization.markers.pose_scale': 0.05,
            'visualization.markers.text_scale': 0.02,
            'visualization.markers.lifetime_sec': 5.0,
            
            # 색상 코딩
            'visualization.colors.excellent': [0.0, 1.0, 0.0],  # Green
            'visualization.colors.good': [0.0, 1.0, 1.0],      # Cyan
            'visualization.colors.acceptable': [1.0, 1.0, 0.0], # Yellow
            'visualization.colors.poor': [1.0, 0.0, 0.0],      # Red
        }
        
        for name, default_value in defaults.items():
            self.declare_parameter(name, default_value)

    def fused_poses_callback(self, msg):
        """융합된 포즈 콜백"""
        try:
            poses_data = json.loads(msg.data)
            self.latest_fused_poses = poses_data.get('fused_objects', [])
            self.get_logger().debug(f'Received {len(self.latest_fused_poses)} fused poses for visualization')
        except json.JSONDecodeError as e:
            self.get_logger().error(f'Failed to parse fused poses: {e}')

    def global_poses_callback(self, msg):
        """글로벌 포즈 콜백"""
        try:
            global_data = json.loads(msg.data)
            self.latest_global_poses = global_data.get('global_object_map', {})
        except json.JSONDecodeError as e:
            self.get_logger().error(f'Failed to parse global poses: {e}')

    def fusion_metrics_callback(self, msg):
        """융합 메트릭 콜백"""
        try:
            metrics_data = json.loads(msg.data)
            self.latest_metrics = metrics_data.get('fusion_metrics', [])
        except json.JSONDecodeError as e:
            self.get_logger().error(f'Failed to parse fusion metrics: {e}')

    def update_visualization(self):
        """시각화 업데이트"""
        try:
            # PoseArray 발행
            if (self.get_parameter('visualization.enable_pose_array').value and 
                self.latest_fused_poses):
                self.publish_pose_array()
                
            # OBB 마커 발행
            if (self.get_parameter('visualization.enable_obb_markers').value and 
                self.latest_fused_poses):
                self.publish_obb_markers()
                
            # 품질 마커 발행
            if (self.get_parameter('visualization.enable_quality_markers').value and 
                self.latest_metrics):
                self.publish_quality_markers()
                
            # 텍스트 라벨 발행
            if (self.get_parameter('visualization.enable_text_labels').value and 
                self.latest_fused_poses):
                self.publish_text_markers()
                
        except Exception as e:
            self.get_logger().error(f'Visualization update error: {e}')

    def publish_pose_array(self):
        """PoseArray 발행"""
        try:
            pose_array = PoseArray()
            pose_array.header.stamp = self.get_clock().now().to_msg()
            pose_array.header.frame_id = self.get_parameter('common.frames.world').value
            
            for fused_pose in self.latest_fused_poses:
                pose = Pose()
                
                # 위치
                position = fused_pose.get('fused_position', [0, 0, 0])
                pose.position.x = float(position[0])
                pose.position.y = float(position[1])
                pose.position.z = float(position[2])
                
                # 회전 (쿼터니언)
                quaternion = fused_pose.get('fused_quaternion', [0, 0, 0, 1])
                pose.orientation.x = float(quaternion[0])
                pose.orientation.y = float(quaternion[1])
                pose.orientation.z = float(quaternion[2])
                pose.orientation.w = float(quaternion[3])
                
                pose_array.poses.append(pose)
                
            self.pose_array_pub.publish(pose_array)
            
        except Exception as e:
            self.get_logger().error(f'PoseArray publication error: {e}')

    def publish_obb_markers(self):
        """OBB (Oriented Bounding Box) 마커 발행"""
        try:
            marker_array = MarkerArray()
            lifetime_sec = self.get_parameter('visualization.markers.lifetime_sec').value
            alpha = self.get_parameter('visualization.markers.obb_alpha').value
            
            for i, fused_pose in enumerate(self.latest_fused_poses):
                marker = Marker()
                marker.header.stamp = self.get_clock().now().to_msg()
                marker.header.frame_id = self.get_parameter('common.frames.world').value
                marker.id = i
                marker.type = Marker.CUBE
                marker.action = Marker.ADD
                
                # 위치
                position = fused_pose.get('fused_position', [0, 0, 0])
                marker.pose.position.x = float(position[0])
                marker.pose.position.y = float(position[1])
                marker.pose.position.z = float(position[2])
                
                # 회전
                quaternion = fused_pose.get('fused_quaternion', [0, 0, 0, 1])
                marker.pose.orientation.x = float(quaternion[0])
                marker.pose.orientation.y = float(quaternion[1])
                marker.pose.orientation.z = float(quaternion[2])
                marker.pose.orientation.w = float(quaternion[3])
                
                # 크기
                dimensions = fused_pose.get('fused_dimensions', [0.02, 0.02, 0.02])
                marker.scale.x = float(dimensions[0])
                marker.scale.y = float(dimensions[1])
                marker.scale.z = float(dimensions[2])
                
                # 색상 (품질에 따라)
                quality_score = self.get_quality_score(fused_pose)
                color = self.get_quality_color(quality_score)
                marker.color.r = color[0]
                marker.color.g = color[1]
                marker.color.b = color[2]
                marker.color.a = alpha
                
                # 수명
                marker.lifetime.sec = int(lifetime_sec)
                marker.lifetime.nanosec = int((lifetime_sec - int(lifetime_sec)) * 1e9)
                
                marker_array.markers.append(marker)
                
            self.obb_markers_pub.publish(marker_array)
            
        except Exception as e:
            self.get_logger().error(f'OBB markers publication error: {e}')

    def publish_quality_markers(self):
        """품질 지시 마커 발행"""
        try:
            marker_array = MarkerArray()
            
            for i, metric in enumerate(self.latest_metrics):
                # 신뢰도 막대 마커
                marker = Marker()
                marker.header.stamp = self.get_clock().now().to_msg()
                marker.header.frame_id = self.get_parameter('common.frames.world').value
                marker.id = 1000 + i  # Unique ID
                marker.type = Marker.CYLINDER
                marker.action = Marker.ADD
                
                # 해당 객체 위치 찾기
                object_id = metric.get('object_id', '')
                object_position = self.find_object_position(object_id)
                
                if object_position is not None:
                    # 위치 (객체 위 약간)
                    marker.pose.position.x = float(object_position[0])
                    marker.pose.position.y = float(object_position[1])
                    marker.pose.position.z = float(object_position[2]) + 0.05
                    
                    # 회전 (수직)
                    marker.pose.orientation.w = 1.0
                    
                    # 크기 (품질에 비례)
                    quality_info = metric.get('fusion_quality', {})
                    quality_score = quality_info.get('score', 0.5)
                    
                    marker.scale.x = 0.005  # 직경
                    marker.scale.y = 0.005
                    marker.scale.z = quality_score * 0.02  # 높이
                    
                    # 색상
                    color = self.get_quality_color(quality_score)
                    marker.color.r = color[0]
                    marker.color.g = color[1]
                    marker.color.b = color[2]
                    marker.color.a = 0.8
                    
                    marker.lifetime.sec = 5
                    marker_array.markers.append(marker)
                    
            self.quality_markers_pub.publish(marker_array)
            
        except Exception as e:
            self.get_logger().error(f'Quality markers publication error: {e}')

    def publish_text_markers(self):
        """텍스트 라벨 마커 발행"""
        try:
            marker_array = MarkerArray()
            text_scale = self.get_parameter('visualization.markers.text_scale').value
            
            for i, fused_pose in enumerate(self.latest_fused_poses):
                marker = Marker()
                marker.header.stamp = self.get_clock().now().to_msg()
                marker.header.frame_id = self.get_parameter('common.frames.world').value
                marker.id = 2000 + i  # Unique ID
                marker.type = Marker.TEXT_VIEW_FACING
                marker.action = Marker.ADD
                
                # 위치 (객체 위)
                position = fused_pose.get('fused_position', [0, 0, 0])
                marker.pose.position.x = float(position[0])
                marker.pose.position.y = float(position[1])
                marker.pose.position.z = float(position[2]) + 0.08
                
                # 텍스트 내용
                object_id = fused_pose.get('object_id', 'unknown')
                num_views = fused_pose.get('num_views', 0)
                
                # 품질 정보 추가
                quality_score = self.get_quality_score(fused_pose)
                quality_text = self.get_quality_text(quality_score)
                
                marker.text = f"{object_id}\n{num_views} views\n{quality_text}"
                
                # 스타일
                marker.scale.z = text_scale
                
                # 색상 (흰색)
                marker.color.r = 1.0
                marker.color.g = 1.0
                marker.color.b = 1.0
                marker.color.a = 1.0
                
                marker.lifetime.sec = 5
                marker_array.markers.append(marker)
                
            self.text_markers_pub.publish(marker_array)
            
        except Exception as e:
            self.get_logger().error(f'Text markers publication error: {e}')

    def find_object_position(self, object_id: str) -> Optional[List[float]]:
        """객체 ID로 위치 찾기"""
        for fused_pose in self.latest_fused_poses:
            if fused_pose.get('object_id') == object_id:
                return fused_pose.get('fused_position')
        return None

    def get_quality_score(self, fused_pose: Dict) -> float:
        """포즈의 품질 점수 계산"""
        # 메트릭에서 해당 객체 찾기
        object_id = fused_pose.get('object_id', '')
        
        for metric in self.latest_metrics:
            if metric.get('object_id') == object_id:
                quality_info = metric.get('fusion_quality', {})
                return quality_info.get('score', 0.5)
                
        # 기본값: 뷰 수에 기반한 점수
        num_views = fused_pose.get('num_views', 1)
        return min(num_views / 5.0, 1.0)  # 5뷰를 최대로 정규화

    def get_quality_color(self, quality_score: float) -> List[float]:
        """품질 점수에 따른 색상 반환"""
        if quality_score >= 0.8:
            return self.get_parameter('visualization.colors.excellent').value
        elif quality_score >= 0.6:
            return self.get_parameter('visualization.colors.good').value
        elif quality_score >= 0.4:
            return self.get_parameter('visualization.colors.acceptable').value
        else:
            return self.get_parameter('visualization.colors.poor').value

    def get_quality_text(self, quality_score: float) -> str:
        """품질 점수를 텍스트로 변환"""
        if quality_score >= 0.8:
            return "EXCELLENT"
        elif quality_score >= 0.6:
            return "GOOD"
        elif quality_score >= 0.4:
            return "OK"
        else:
            return "POOR"


def main(args=None):
    rclpy.init(args=args)
    node = VisualizationNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()