#!/usr/bin/env python3
"""
YOLO 기반 소마큐브 조각 검출 노드
수학적 정밀 체계의 첫 번째 단계: 객체 검출 및 관심 영역 추출
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from sensor_msgs.msg import Image, CameraInfo
from geometry_msgs.msg import Point
from std_msgs.msg import Header
import cv2
import numpy as np
from cv_bridge import CvBridge
import yaml
import os
from pathlib import Path

# Custom message types (would be defined in msg/ directory)
from std_msgs.msg import String
import json

try:
    import torch
    from ultralytics import YOLO
    HAS_YOLO = True
except ImportError:
    HAS_YOLO = False


class YOLODetectorNode(Node):
    """YOLO 기반 소마큐브 조각 검출"""
    
    def __init__(self):
        super().__init__('yolo_detector')
        
        # Parameters
        self.declare_parameters_from_yaml()
        
        # CV bridge
        self.bridge = CvBridge()
        
        # Load YOLO model
        self.yolo_model = self.load_yolo_model()
        
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
        
        self.camera_info_sub = self.create_subscription(
            CameraInfo,
            self.get_parameter('common.topics.camera_info').value,
            self.camera_info_callback,
            sensor_qos
        )
        
        # Publishers - using String for detection results (JSON format)
        self.detection_pub = self.create_publisher(
            String,
            '/yolo_detector/detections',
            10
        )
        
        self.annotated_image_pub = self.create_publisher(
            Image,
            '/yolo_detector/annotated_image',
            10
        )
        
        # State
        self.camera_info = None
        self.soma_cube_classes = self.get_soma_cube_classes()
        
        # Statistics
        self.detection_count = 0
        self.false_positive_count = 0
        
        # Timer for processing
        processing_rate = self.get_parameter('yolo_detector.processing_rate_hz').value
        self.timer = self.create_timer(1.0 / processing_rate, self.process_detections)
        
        self.latest_image = None
        
        self.get_logger().info('YOLO Detector node initialized')
        self.get_logger().info(f'YOLO available: {HAS_YOLO}')
        if self.yolo_model is not None:
            self.get_logger().info('YOLO model loaded successfully')

    def declare_parameters_from_yaml(self):
        """YAML 설정에서 파라미터 선언"""
        defaults = {
            'common.topics.rgb': '/camera/color/image_raw',
            'common.topics.camera_info': '/camera/color/camera_info',
            'common.frames.camera': 'camera_link',
            'common.frames.base': 'base',
            
            'yolo_detector.model_path': 'models/somacube_best.pt',
            'yolo_detector.confidence_threshold': 0.5,
            'yolo_detector.iou_threshold': 0.4,
            'yolo_detector.processing_rate_hz': 30.0,
            'yolo_detector.max_detections': 20,
            'yolo_detector.input_size': [640, 640],
            'yolo_detector.device': 'cpu',  # or 'cuda' if available
            
            # Mathematical validation parameters
            'yolo_detector.validation.min_area_pixels': 400,
            'yolo_detector.validation.max_area_pixels': 50000,
            'yolo_detector.validation.min_aspect_ratio': 0.3,
            'yolo_detector.validation.max_aspect_ratio': 3.0,
            'yolo_detector.validation.edge_exclusion_margin': 10,
        }
        
        for name, default_value in defaults.items():
            self.declare_parameter(name, default_value)

    def get_soma_cube_classes(self) -> dict:
        """소마큐브 조각 클래스 정의"""
        return {
            0: 'piece_L',      # L자 조각
            1: 'piece_T',      # T자 조각  
            2: 'piece_Z',      # Z자 조각
            3: 'piece_O',      # O자 조각 (2x2x1)
            4: 'piece_I',      # I자 조각 (직선)
            5: 'piece_S',      # S자 조각
            6: 'piece_P',      # P자 조각
            # 필요에 따라 더 세분화 가능
        }

    def load_yolo_model(self):
        """YOLO 모델 로드"""
        if not HAS_YOLO:
            self.get_logger().warn('YOLO not available, using mock detections')
            return None
            
        model_path = self.get_parameter('yolo_detector.model_path').value
        
        # 패키지 경로 기준으로 모델 파일 찾기
        package_dir = Path(__file__).parent.parent
        full_model_path = package_dir / model_path
        
        if not full_model_path.exists():
            self.get_logger().warn(f'YOLO model not found at {full_model_path}')
            self.get_logger().info('Please place your trained .pt file in the models/ directory')
            return None
            
        try:
            device = self.get_parameter('yolo_detector.device').value
            if device == 'cuda' and not torch.cuda.is_available():
                device = 'cpu'
                self.get_logger().warn('CUDA not available, using CPU')
                
            model = YOLO(str(full_model_path))
            model.to(device)
            return model
            
        except Exception as e:
            self.get_logger().error(f'Failed to load YOLO model: {e}')
            return None

    def camera_info_callback(self, msg):
        """카메라 정보 콜백"""
        self.camera_info = msg

    def rgb_callback(self, msg):
        """RGB 이미지 콜백"""
        self.latest_image = msg

    def process_detections(self):
        """메인 검출 처리 루프"""
        if self.latest_image is None:
            return
            
        try:
            # Convert ROS image to OpenCV
            cv_image = self.bridge.imgmsg_to_cv2(self.latest_image, 'bgr8')
            
            # Run YOLO detection
            detections = self.run_yolo_detection(cv_image)
            
            # Mathematical validation of detections
            validated_detections = self.validate_detections(detections, cv_image.shape)
            
            # Publish results
            if validated_detections:
                self.publish_detections(validated_detections, self.latest_image.header)
                
            # Publish annotated image
            annotated_image = self.draw_detections(cv_image, validated_detections)
            annotated_msg = self.bridge.cv2_to_imgmsg(annotated_image, 'bgr8')
            annotated_msg.header = self.latest_image.header
            self.annotated_image_pub.publish(annotated_msg)
            
        except Exception as e:
            self.get_logger().error(f'Detection processing error: {e}')

    def run_yolo_detection(self, image: np.ndarray) -> list:
        """YOLO 모델로 검출 실행"""
        if self.yolo_model is None:
            # Mock detection for testing
            return self.generate_mock_detections(image)
            
        try:
            conf_thresh = self.get_parameter('yolo_detector.confidence_threshold').value
            iou_thresh = self.get_parameter('yolo_detector.iou_threshold').value
            max_det = self.get_parameter('yolo_detector.max_detections').value
            
            # YOLO inference
            results = self.yolo_model(
                image,
                conf=conf_thresh,
                iou=iou_thresh,
                max_det=max_det,
                verbose=False
            )
            
            detections = []
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        confidence = float(box.conf[0].cpu().numpy())
                        class_id = int(box.cls[0].cpu().numpy())
                        
                        detection = {
                            'bbox': [float(x1), float(y1), float(x2), float(y2)],
                            'confidence': confidence,
                            'class_id': class_id,
                            'class_name': self.soma_cube_classes.get(class_id, 'unknown')
                        }
                        detections.append(detection)
                        
            return detections
            
        except Exception as e:
            self.get_logger().error(f'YOLO inference error: {e}')
            return []

    def generate_mock_detections(self, image: np.ndarray) -> list:
        """테스트용 모의 검출 생성"""
        h, w = image.shape[:2]
        
        # 간단한 모의 검출 (중앙 영역에 하나)
        mock_detections = [
            {
                'bbox': [w*0.3, h*0.3, w*0.7, h*0.7],
                'confidence': 0.85,
                'class_id': 0,
                'class_name': 'piece_L'
            }
        ]
        return mock_detections

    def validate_detections(self, detections: list, image_shape: tuple) -> list:
        """수학적 검증을 통한 검출 결과 필터링"""
        h, w = image_shape[:2]
        validated = []
        
        min_area = self.get_parameter('yolo_detector.validation.min_area_pixels').value
        max_area = self.get_parameter('yolo_detector.validation.max_area_pixels').value
        min_aspect = self.get_parameter('yolo_detector.validation.min_aspect_ratio').value
        max_aspect = self.get_parameter('yolo_detector.validation.max_aspect_ratio').value
        margin = self.get_parameter('yolo_detector.validation.edge_exclusion_margin').value
        
        for detection in detections:
            x1, y1, x2, y2 = detection['bbox']
            
            # 기본 검증
            if x1 >= x2 or y1 >= y2:
                continue
                
            # 영역 크기 검증
            area = (x2 - x1) * (y2 - y1)
            if area < min_area or area > max_area:
                continue
                
            # 종횡비 검증
            width = x2 - x1
            height = y2 - y1
            aspect_ratio = width / height if height > 0 else float('inf')
            
            if aspect_ratio < min_aspect or aspect_ratio > max_aspect:
                continue
                
            # 가장자리 제외 검증 (잘린 물체 제외)
            if (x1 < margin or y1 < margin or 
                x2 > w - margin or y2 > h - margin):
                continue
                
            # 신뢰도 추가 검증
            if detection['confidence'] < 0.3:  # 최소 임계값
                continue
                
            # 기하학적 일관성 검증 추가 가능
            # (예: 소마큐브 조각의 예상 크기 범위 등)
            
            validated.append(detection)
            
        self.detection_count += len(validated)
        self.false_positive_count += len(detections) - len(validated)
        
        return validated

    def publish_detections(self, detections: list, header: Header):
        """검출 결과 발행"""
        detection_data = {
            'header': {
                'stamp': {
                    'sec': header.stamp.sec,
                    'nanosec': header.stamp.nanosec
                },
                'frame_id': header.frame_id
            },
            'detections': detections,
            'camera_info': {
                'height': self.camera_info.height if self.camera_info else 0,
                'width': self.camera_info.width if self.camera_info else 0,
                'k': list(self.camera_info.k) if self.camera_info else []
            }
        }
        
        json_msg = String()
        json_msg.data = json.dumps(detection_data)
        self.detection_pub.publish(json_msg)

    def draw_detections(self, image: np.ndarray, detections: list) -> np.ndarray:
        """검출 결과 시각화"""
        annotated = image.copy()
        
        for detection in detections:
            x1, y1, x2, y2 = map(int, detection['bbox'])
            confidence = detection['confidence']
            class_name = detection['class_name']
            
            # 바운딩 박스
            color = (0, 255, 0)  # 초록색
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
            
            # 라벨
            label = f'{class_name}: {confidence:.2f}'
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
            
            # 라벨 배경
            cv2.rectangle(annotated, 
                         (x1, y1 - label_size[1] - 10),
                         (x1 + label_size[0], y1),
                         color, -1)
            
            # 라벨 텍스트
            cv2.putText(annotated, label,
                       (x1, y1 - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                       (255, 255, 255), 2)
            
            # 중심점 표시
            center_x = int((x1 + x2) / 2)
            center_y = int((y1 + y2) / 2)
            cv2.circle(annotated, (center_x, center_y), 5, (0, 0, 255), -1)
        
        # 통계 정보 표시
        stats_text = f'Detections: {len(detections)}, Total: {self.detection_count}'
        cv2.putText(annotated, stats_text,
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                   (255, 255, 255), 2)
        
        return annotated


def main(args=None):
    rclpy.init(args=args)
    node = YOLODetectorNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()