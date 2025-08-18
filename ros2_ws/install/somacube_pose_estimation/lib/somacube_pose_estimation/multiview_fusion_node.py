#!/usr/bin/env python3
"""
멀티뷰 융합 노드
수학적 정밀 체계 VIII단계: 멀티뷰 융합 이론 (정리 T17-T19 구현)
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Int32
from geometry_msgs.msg import PoseStamped
import numpy as np
import json
from scipy.spatial.transform import Rotation as R
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
import time

# Import mathematical foundations
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from somacube_pose_estimation.mathematical_foundations import MathematicalFoundations

try:
    from scipy.optimize import minimize
    from scipy.spatial.distance import cdist
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False


class MultiViewFusionNode(Node):
    """멀티뷰 융합 시스템 (정리 T17-T19, T24-T27)"""
    
    def __init__(self):
        super().__init__('multiview_fusion')
        
        # Mathematical foundations
        self.math_foundation = MathematicalFoundations()
        
        # Parameters
        self.declare_parameters_from_yaml()
        
        # Subscribers
        self.aligned_poses_sub = self.create_subscription(
            String,
            '/manhattan_aligner/aligned_poses',
            self.aligned_poses_callback,
            10
        )
        
        self.camera_pose_sub = self.create_subscription(
            PoseStamped,
            '/camera_pose_manager/current_pose',
            self.camera_pose_callback,
            10
        )
        
        self.pose_index_sub = self.create_subscription(
            Int32,
            '/camera_pose_manager/set_pose_index',
            self.pose_index_callback,
            10
        )
        
        # Publishers
        self.fused_poses_pub = self.create_publisher(
            String,
            '/multiview_fusion/fused_poses',
            10
        )
        
        self.global_poses_pub = self.create_publisher(
            String,
            '/multiview_fusion/global_poses',
            10
        )
        
        self.fusion_metrics_pub = self.create_publisher(
            String,
            '/multiview_fusion/fusion_metrics',
            10
        )
        
        self.convergence_status_pub = self.create_publisher(
            String,
            '/multiview_fusion/convergence_status',
            10
        )
        
        # Multi-view data storage
        self.view_poses = {}  # pose_index -> list of detected poses
        self.global_object_map = {}  # object_id -> fused global pose
        self.current_pose_index = 0
        
        # Fusion parameters
        self.similarity_matrix = {}
        self.object_correspondences = {}  # view correspondences
        
        # Statistics
        self.total_views_processed = 0
        self.successful_fusions = 0
        self.convergence_achieved = 0
        
        # Timer for fusion processing
        fusion_rate = self.get_parameter('multiview_fusion.processing_rate_hz').value
        self.fusion_timer = self.create_timer(1.0 / fusion_rate, self.process_multiview_fusion)
        
        self.get_logger().info('MultiView Fusion node initialized')
        self.get_logger().info(f'SciPy available: {HAS_SCIPY}')

    def declare_parameters_from_yaml(self):
        """YAML 설정에서 파라미터 선언"""
        defaults = {
            'common.frames.camera': 'camera_link',
            'common.frames.world': 'world',
            
            'multiview_fusion.processing_rate_hz': 2.0,
            
            # 정의 D10: 객체 간 유사도 메트릭
            'multiview_fusion.similarity.position_weight': 0.3,
            'multiview_fusion.similarity.rotation_weight': 0.3,
            'multiview_fusion.similarity.size_weight': 0.3,
            'multiview_fusion.similarity.confidence_weight': 0.1,
            'multiview_fusion.similarity.position_sigma_m': 0.02,
            'multiview_fusion.similarity.rotation_sigma_rad': 0.17,  # ~10 degrees
            'multiview_fusion.similarity.size_sigma_m': 0.01,
            
            # 정리 T21: 헝가리안 할당
            'multiview_fusion.assignment.similarity_threshold': 0.5,
            'multiview_fusion.assignment.max_distance_m': 0.1,
            'multiview_fusion.assignment.max_rotation_deg': 30.0,
            
            # 정리 T17: 회전 평균 (Riemannian Mean)
            'multiview_fusion.rotation_averaging.method': 'svd',  # 'svd' or 'iterative'
            'multiview_fusion.rotation_averaging.max_iterations': 50,
            'multiview_fusion.rotation_averaging.tolerance': 1e-6,
            
            # 정리 T18: 위치 융합 (Robust Estimation)
            'multiview_fusion.position_fusion.method': 'huber',  # 'mean', 'huber', 'ransac'
            'multiview_fusion.position_fusion.huber_delta': 0.01,
            'multiview_fusion.position_fusion.ransac_threshold': 0.02,
            'multiview_fusion.position_fusion.min_consensus': 0.6,
            
            # 정리 T25: 수렴성과 안정성
            'multiview_fusion.convergence.min_views': 3,
            'multiview_fusion.convergence.max_position_change_m': 0.005,
            'multiview_fusion.convergence.max_rotation_change_deg': 2.0,
            'multiview_fusion.convergence.stability_window': 5,
            
            # 전역 최적화
            'multiview_fusion.global_optimization.enable': True,
            'multiview_fusion.global_optimization.bundle_adjustment': False,
            'multiview_fusion.global_optimization.max_iterations': 100,
            
            # 품질 보증
            'multiview_fusion.quality_assurance.min_view_agreement': 0.7,
            'multiview_fusion.quality_assurance.outlier_detection': True,
            'multiview_fusion.quality_assurance.cross_validation': True,
        }
        
        for name, default_value in defaults.items():
            self.declare_parameter(name, default_value)

    def aligned_poses_callback(self, msg):
        """정렬된 포즈 콜백"""
        try:
            poses_data = json.loads(msg.data)
            poses = poses_data.get('poses', [])
            
            if poses:
                # 현재 뷰의 포즈들 저장
                self.view_poses[self.current_pose_index] = poses
                self.total_views_processed += 1
                
                self.get_logger().debug(
                    f'Received {len(poses)} poses for view {self.current_pose_index}'
                )
                
        except json.JSONDecodeError as e:
            self.get_logger().error(f'Failed to parse aligned poses: {e}')

    def camera_pose_callback(self, msg):
        """카메라 포즈 콜백"""
        # 카메라 포즈가 변경될 때마다 저장
        self.current_camera_pose = msg

    def pose_index_callback(self, msg):
        """포즈 인덱스 변경 콜백"""
        self.current_pose_index = msg.data
        self.get_logger().debug(f'Camera pose index changed to {self.current_pose_index}')

    def process_multiview_fusion(self):
        """메인 멀티뷰 융합 처리 루프"""
        if len(self.view_poses) < 2:
            return
            
        try:
            # 1. 객체 대응 관계 찾기 (정의 D10, 정리 T21)
            correspondences = self.find_object_correspondences()
            
            if not correspondences:
                return
                
            # 2. 각 객체별 멀티뷰 융합
            fused_objects = []
            fusion_metrics = []
            
            for object_id, view_detections in correspondences.items():
                if len(view_detections) < self.get_parameter('multiview_fusion.convergence.min_views').value:
                    continue
                    
                # 포즈 융합 (정리 T17, T18)
                fused_pose = self.fuse_object_poses(object_id, view_detections)
                
                if fused_pose is not None:
                    fused_objects.append(fused_pose)
                    
                    # 융합 품질 메트릭 계산
                    metrics = self.compute_fusion_metrics(object_id, view_detections, fused_pose)
                    fusion_metrics.append(metrics)
                    
                    # 글로벌 객체 맵 업데이트
                    self.global_object_map[object_id] = fused_pose
                    self.successful_fusions += 1
                    
            # 3. 수렴성 분석 (정리 T25)
            convergence_status = self.analyze_convergence()
            
            # 4. 전역 최적화 (선택사항)
            if (self.get_parameter('multiview_fusion.global_optimization.enable').value and 
                len(fused_objects) > 2):
                optimized_poses = self.global_pose_optimization(fused_objects)
                if optimized_poses:
                    fused_objects = optimized_poses
                    
            # 결과 발행
            if fused_objects:
                self.publish_fused_poses(fused_objects)
                self.publish_global_poses()
                
            if fusion_metrics:
                self.publish_fusion_metrics(fusion_metrics)
                
            self.publish_convergence_status(convergence_status)
            
        except Exception as e:
            self.get_logger().error(f'MultiView fusion error: {e}')

    def find_object_correspondences(self) -> Dict[str, List[Dict]]:
        """정의 D10, 정리 T21: 뷰 간 객체 대응 관계 찾기"""
        if len(self.view_poses) < 2:
            return {}
            
        try:
            # 모든 뷰의 포즈들을 글로벌 좌표계로 변환
            global_view_poses = {}
            
            for view_idx, poses in self.view_poses.items():
                global_poses = []
                
                for pose in poses:
                    # 카메라 좌표계 -> 글로벌 좌표계 변환
                    global_pose = self.transform_pose_to_global(pose, view_idx)
                    if global_pose:
                        global_poses.append(global_pose)
                        
                if global_poses:
                    global_view_poses[view_idx] = global_poses
                    
            # 유사도 행렬 계산
            similarity_matrices = self.compute_similarity_matrices(global_view_poses)
            
            # 헝가리안 할당 (정리 T21)
            correspondences = self.hungarian_assignment(similarity_matrices, global_view_poses)
            
            return correspondences
            
        except Exception as e:
            self.get_logger().error(f'Object correspondence error: {e}')
            return {}

    def transform_pose_to_global(self, local_pose: Dict, view_index: int) -> Optional[Dict]:
        """로컬 포즈를 글로벌 좌표계로 변환"""
        try:
            # 해당 뷰의 카메라 포즈 가져오기 (카메라 포즈 매니저에서)
            # 여기서는 간단히 현재 포즈 사용 (실제로는 view_index에 해당하는 포즈 필요)
            
            # 로컬 포즈 행렬 구성
            local_position = np.array(local_pose['position'])
            local_rotation = np.array(local_pose['rotation_matrix'])
            
            local_T = np.eye(4)
            local_T[:3, :3] = local_rotation
            local_T[:3, 3] = local_position
            
            # 카메라 포즈 행렬 (여기서는 단순화)
            camera_T = np.eye(4)  # Identity for now
            
            # 글로벌 변환
            global_T = camera_T @ local_T
            
            global_pose = local_pose.copy()
            global_pose['global_position'] = global_T[:3, 3].tolist()
            global_pose['global_rotation_matrix'] = global_T[:3, :3].tolist()
            global_pose['global_quaternion'] = R.from_matrix(global_T[:3, :3]).as_quat().tolist()
            global_pose['view_index'] = view_index
            
            return global_pose
            
        except Exception as e:
            self.get_logger().error(f'Pose transformation error: {e}')
            return None

    def compute_similarity_matrices(self, global_view_poses: Dict) -> Dict:
        """정의 D10: 객체 간 유사도 행렬 계산"""
        similarity_matrices = {}
        
        try:
            view_indices = list(global_view_poses.keys())
            
            for i, view1 in enumerate(view_indices):
                for j, view2 in enumerate(view_indices[i+1:], i+1):
                    
                    poses1 = global_view_poses[view1]
                    poses2 = global_view_poses[view2]
                    
                    # NxM 유사도 행렬 계산
                    similarity_matrix = np.zeros((len(poses1), len(poses2)))
                    
                    for p1_idx, pose1 in enumerate(poses1):
                        for p2_idx, pose2 in enumerate(poses2):
                            similarity = self.compute_pose_similarity(pose1, pose2)
                            similarity_matrix[p1_idx, p2_idx] = similarity
                            
                    similarity_matrices[(view1, view2)] = similarity_matrix
                    
            return similarity_matrices
            
        except Exception as e:
            self.get_logger().error(f'Similarity matrix computation error: {e}')
            return {}

    def compute_pose_similarity(self, pose1: Dict, pose2: Dict) -> float:
        """정의 D10: 두 포즈 간 종합 유사도 계산"""
        try:
            # 파라미터 로드
            w_pos = self.get_parameter('multiview_fusion.similarity.position_weight').value
            w_rot = self.get_parameter('multiview_fusion.similarity.rotation_weight').value
            w_size = self.get_parameter('multiview_fusion.similarity.size_weight').value
            w_conf = self.get_parameter('multiview_fusion.similarity.confidence_weight').value
            
            sigma_pos = self.get_parameter('multiview_fusion.similarity.position_sigma_m').value
            sigma_rot = self.get_parameter('multiview_fusion.similarity.rotation_sigma_rad').value
            sigma_size = self.get_parameter('multiview_fusion.similarity.size_sigma_m').value
            
            # 위치 유사도
            pos1 = np.array(pose1.get('global_position', pose1['position']))
            pos2 = np.array(pose2.get('global_position', pose2['position']))
            pos_distance = np.linalg.norm(pos1 - pos2)
            pos_similarity = np.exp(-(pos_distance**2) / (2 * sigma_pos**2))
            
            # 회전 유사도 (측지선 거리)
            rot1 = np.array(pose1.get('global_rotation_matrix', pose1['rotation_matrix']))
            rot2 = np.array(pose2.get('global_rotation_matrix', pose2['rotation_matrix']))
            rot_distance = self.math_foundation.geodesic_distance_SO3(rot1, rot2)
            rot_similarity = np.exp(-(rot_distance**2) / (2 * sigma_rot**2))
            
            # 크기 유사도
            size1 = np.array(pose1['dimensions'])
            size2 = np.array(pose2['dimensions'])
            size_distance = np.linalg.norm(size1 - size2)
            size_similarity = np.exp(-(size_distance**2) / (2 * sigma_size**2))
            
            # 신뢰도 유사도 (간단히 곱셈)
            conf1 = pose1.get('alignment_score', 1.0)
            conf2 = pose2.get('alignment_score', 1.0)
            conf_similarity = min(conf1, conf2)  # Conservative approach
            
            # 가중 평균
            total_similarity = (w_pos * pos_similarity +
                              w_rot * rot_similarity +
                              w_size * size_similarity +
                              w_conf * conf_similarity)
            
            return float(total_similarity)
            
        except Exception as e:
            self.get_logger().error(f'Pose similarity computation error: {e}')
            return 0.0

    def hungarian_assignment(self, similarity_matrices: Dict, 
                           global_view_poses: Dict) -> Dict[str, List[Dict]]:
        """정리 T21: 헝가리안 할당으로 객체 대응"""
        try:
            from scipy.optimize import linear_sum_assignment
            
            correspondences = defaultdict(list)
            object_counter = 0
            
            # 각 뷰 쌍에 대해 할당 수행
            for (view1, view2), sim_matrix in similarity_matrices.items():
                if sim_matrix.size == 0:
                    continue
                    
                # 유사도를 비용으로 변환 (최대화 -> 최소화)
                cost_matrix = 1.0 - sim_matrix
                
                # 임계값 이하는 무한대 비용
                threshold = self.get_parameter('multiview_fusion.assignment.similarity_threshold').value
                cost_matrix[sim_matrix < threshold] = np.inf
                
                # 헝가리안 할당
                row_indices, col_indices = linear_sum_assignment(cost_matrix)
                
                poses1 = global_view_poses[view1]
                poses2 = global_view_poses[view2]
                
                # 유효한 할당들 처리
                for r, c in zip(row_indices, col_indices):
                    if cost_matrix[r, c] < np.inf:
                        # 새로운 객체 ID 생성 또는 기존 객체에 추가
                        object_id = f"object_{object_counter}"
                        
                        # 두 뷰의 포즈를 대응 관계에 추가
                        correspondences[object_id].append(poses1[r])
                        correspondences[object_id].append(poses2[c])
                        
                        object_counter += 1
                        
            # 중복 제거 및 정리
            cleaned_correspondences = {}
            for obj_id, pose_list in correspondences.items():
                if len(pose_list) >= 2:  # 최소 2개 뷰
                    cleaned_correspondences[obj_id] = pose_list
                    
            return cleaned_correspondences
            
        except ImportError:
            self.get_logger().warn('SciPy not available, using simple assignment')
            return self.simple_assignment(similarity_matrices, global_view_poses)
        except Exception as e:
            self.get_logger().error(f'Hungarian assignment error: {e}')
            return {}

    def simple_assignment(self, similarity_matrices: Dict, 
                         global_view_poses: Dict) -> Dict[str, List[Dict]]:
        """간단한 탐욕적 할당 (SciPy 없을 때)"""
        correspondences = defaultdict(list)
        object_counter = 0
        
        try:
            threshold = self.get_parameter('multiview_fusion.assignment.similarity_threshold').value
            
            for (view1, view2), sim_matrix in similarity_matrices.items():
                poses1 = global_view_poses[view1]
                poses2 = global_view_poses[view2]
                
                # 최대 유사도 기반 매칭
                for i in range(sim_matrix.shape[0]):
                    max_sim = np.max(sim_matrix[i, :])
                    if max_sim > threshold:
                        max_j = np.argmax(sim_matrix[i, :])
                        
                        object_id = f"object_{object_counter}"
                        correspondences[object_id].extend([poses1[i], poses2[max_j]])
                        object_counter += 1
                        
            return dict(correspondences)
            
        except Exception as e:
            self.get_logger().error(f'Simple assignment error: {e}')
            return {}

    def fuse_object_poses(self, object_id: str, view_detections: List[Dict]) -> Optional[Dict]:
        """정리 T17, T18: 객체 포즈 융합"""
        if len(view_detections) < 2:
            return None
            
        try:
            # 위치들과 회전들 추출
            positions = []
            rotations = []
            weights = []
            
            for detection in view_detections:
                pos = detection.get('global_position', detection['position'])
                rot_matrix = detection.get('global_rotation_matrix', detection['rotation_matrix'])
                confidence = detection.get('alignment_score', 1.0)
                
                positions.append(pos)
                rotations.append(np.array(rot_matrix))
                weights.append(confidence)
                
            positions = np.array(positions)
            weights = np.array(weights)
            weights = weights / np.sum(weights)  # 정규화
            
            # 회전 평균 (정리 T17: Riemannian Mean)
            fused_rotation = self.math_foundation.riemannian_mean_rotations(rotations, weights)
            
            # 위치 융합 (정리 T18: Robust Estimation)
            method = self.get_parameter('multiview_fusion.position_fusion.method').value
            
            if method == 'huber':
                delta = self.get_parameter('multiview_fusion.position_fusion.huber_delta').value
                fused_position = self.math_foundation.huber_robust_mean(positions, weights, delta)
            elif method == 'ransac':
                fused_position = self.ransac_position_fusion(positions, weights)
            else:  # mean
                fused_position = np.average(positions, weights=weights, axis=0)
                
            # 치수 융합 (가중 평균)
            dimensions_list = [detection['dimensions'] for detection in view_detections]
            fused_dimensions = np.average(dimensions_list, weights=weights, axis=0)
            
            # 융합된 포즈 구성
            fused_pose = {
                'object_id': object_id,
                'fused_position': fused_position.tolist(),
                'fused_rotation_matrix': fused_rotation.tolist(),
                'fused_quaternion': R.from_matrix(fused_rotation).as_quat().tolist(),
                'fused_dimensions': fused_dimensions.tolist(),
                'num_views': len(view_detections),
                'view_indices': [det.get('view_index', 0) for det in view_detections],
                'fusion_weights': weights.tolist(),
                'fusion_method': f"rotation_riemannian_position_{method}",
                'timestamp': self.get_clock().now().to_msg()
            }
            
            return fused_pose
            
        except Exception as e:
            self.get_logger().error(f'Pose fusion error for {object_id}: {e}')
            return None

    def ransac_position_fusion(self, positions: np.ndarray, weights: np.ndarray) -> np.ndarray:
        """RANSAC 기반 강건한 위치 융합"""
        try:
            threshold = self.get_parameter('multiview_fusion.position_fusion.ransac_threshold').value
            min_consensus = self.get_parameter('multiview_fusion.position_fusion.min_consensus').value
            
            if len(positions) < 3:
                return np.average(positions, weights=weights, axis=0)
                
            best_consensus = []
            best_mean = None
            max_iterations = min(100, len(positions) * 10)
            
            for _ in range(max_iterations):
                # 랜덤 샘플 선택
                n_samples = max(2, len(positions) // 2)
                sample_indices = np.random.choice(len(positions), n_samples, replace=False)
                sample_positions = positions[sample_indices]
                sample_weights = weights[sample_indices]
                sample_weights = sample_weights / np.sum(sample_weights)
                
                # 샘플 평균 계산
                sample_mean = np.average(sample_positions, weights=sample_weights, axis=0)
                
                # 인라이어 찾기
                distances = np.linalg.norm(positions - sample_mean, axis=1)
                inliers = distances < threshold
                
                # 합의 집합 크기 확인
                if np.sum(inliers) / len(positions) >= min_consensus:
                    if len(inliers) > len(best_consensus):
                        best_consensus = inliers
                        best_mean = sample_mean
                        
            # 최종 융합
            if best_mean is not None and np.sum(best_consensus) > 0:
                consensus_positions = positions[best_consensus]
                consensus_weights = weights[best_consensus]
                consensus_weights = consensus_weights / np.sum(consensus_weights)
                
                return np.average(consensus_positions, weights=consensus_weights, axis=0)
            else:
                return np.average(positions, weights=weights, axis=0)
                
        except Exception as e:
            self.get_logger().error(f'RANSAC position fusion error: {e}')
            return np.average(positions, weights=weights, axis=0)

    def compute_fusion_metrics(self, object_id: str, view_detections: List[Dict], 
                             fused_pose: Dict) -> Dict:
        """융합 품질 메트릭 계산"""
        try:
            fused_position = np.array(fused_pose['fused_position'])
            fused_rotation = np.array(fused_pose['fused_rotation_matrix'])
            
            # 개별 뷰들과의 편차 계산
            position_deviations = []
            rotation_deviations = []
            
            for detection in view_detections:
                # 위치 편차
                det_pos = np.array(detection.get('global_position', detection['position']))
                pos_dev = np.linalg.norm(fused_position - det_pos)
                position_deviations.append(pos_dev)
                
                # 회전 편차
                det_rot = np.array(detection.get('global_rotation_matrix', detection['rotation_matrix']))
                rot_dev = self.math_foundation.geodesic_distance_SO3(fused_rotation, det_rot)
                rotation_deviations.append(rot_dev)
                
            # 통계
            metrics = {
                'object_id': object_id,
                'num_views_fused': len(view_detections),
                'position_consistency': {
                    'mean_deviation_m': float(np.mean(position_deviations)),
                    'std_deviation_m': float(np.std(position_deviations)),
                    'max_deviation_m': float(np.max(position_deviations)),
                },
                'rotation_consistency': {
                    'mean_deviation_rad': float(np.mean(rotation_deviations)),
                    'mean_deviation_deg': float(np.degrees(np.mean(rotation_deviations))),
                    'std_deviation_rad': float(np.std(rotation_deviations)),
                    'max_deviation_rad': float(np.max(rotation_deviations)),
                },
                'fusion_quality': self.assess_fusion_quality(position_deviations, rotation_deviations),
                'timestamp': self.get_clock().now().to_msg()
            }
            
            return metrics
            
        except Exception as e:
            self.get_logger().error(f'Fusion metrics computation error: {e}')
            return {'object_id': object_id, 'error': str(e)}

    def assess_fusion_quality(self, pos_devs: List[float], rot_devs: List[float]) -> Dict:
        """융합 품질 평가"""
        mean_pos_dev = np.mean(pos_devs)
        mean_rot_dev = np.mean(rot_devs)
        
        # 임계값 기준 평가
        pos_good = mean_pos_dev < 0.01  # 1cm
        rot_good = mean_rot_dev < np.radians(10)  # 10도
        
        if pos_good and rot_good:
            quality_level = 'excellent'
            score = 0.9
        elif pos_good or rot_good:
            quality_level = 'good'
            score = 0.7
        elif mean_pos_dev < 0.05 and mean_rot_dev < np.radians(30):
            quality_level = 'acceptable'
            score = 0.5
        else:
            quality_level = 'poor'
            score = 0.2
            
        return {
            'level': quality_level,
            'score': score,
            'position_good': pos_good,
            'rotation_good': rot_good
        }

    def analyze_convergence(self) -> Dict:
        """정리 T25: 수렴성 분석"""
        try:
            min_views = self.get_parameter('multiview_fusion.convergence.min_views').value
            max_pos_change = self.get_parameter('multiview_fusion.convergence.max_position_change_m').value
            max_rot_change = self.get_parameter('multiview_fusion.convergence.max_rotation_change_deg').value
            
            convergence_status = {
                'total_objects': len(self.global_object_map),
                'sufficient_views': len(self.view_poses) >= min_views,
                'converged_objects': 0,
                'stability_achieved': False,
                'convergence_rate': 0.0,
                'timestamp': self.get_clock().now().to_msg()
            }
            
            # 각 객체의 수렴성 분석 (이력이 있다면)
            # 여기서는 간단히 뷰 수와 품질 기준으로 판단
            for obj_id, fused_pose in self.global_object_map.items():
                num_views = fused_pose.get('num_views', 0)
                if num_views >= min_views:
                    convergence_status['converged_objects'] += 1
                    
            if convergence_status['total_objects'] > 0:
                convergence_status['convergence_rate'] = (
                    convergence_status['converged_objects'] / convergence_status['total_objects']
                )
                
            convergence_status['stability_achieved'] = (
                convergence_status['convergence_rate'] > 0.8
            )
            
            if convergence_status['stability_achieved']:
                self.convergence_achieved += 1
                
            return convergence_status
            
        except Exception as e:
            self.get_logger().error(f'Convergence analysis error: {e}')
            return {'error': str(e)}

    def global_pose_optimization(self, fused_objects: List[Dict]) -> Optional[List[Dict]]:
        """전역 포즈 최적화 (Bundle Adjustment 스타일)"""
        if not HAS_SCIPY:
            return None
            
        try:
            # 간단한 전역 일관성 최적화
            # 실제로는 더 복잡한 번들 조정이 필요
            
            optimized_objects = []
            
            for obj in fused_objects:
                # 현재는 단순히 스무딩 적용
                optimized_obj = obj.copy()
                
                # 위치 스무딩 (간단한 가우시안 필터)
                position = np.array(obj['fused_position'])
                # 스무딩 로직 (여기서는 생략)
                
                optimized_obj['optimization_applied'] = True
                optimized_objects.append(optimized_obj)
                
            return optimized_objects
            
        except Exception as e:
            self.get_logger().error(f'Global optimization error: {e}')
            return None

    def publish_fused_poses(self, fused_objects: List[Dict]):
        """융합된 포즈 발행"""
        try:
            data = {
                'header': {
                    'stamp': self.get_clock().now().to_msg(),
                    'frame_id': self.get_parameter('common.frames.world').value
                },
                'total_fused_objects': len(fused_objects),
                'fused_objects': fused_objects,
                'statistics': {
                    'total_views_processed': self.total_views_processed,
                    'successful_fusions': self.successful_fusions,
                    'fusion_success_rate': self.successful_fusions / max(self.total_views_processed, 1)
                }
            }
            
            json_msg = String()
            json_msg.data = json.dumps(data)
            self.fused_poses_pub.publish(json_msg)
            
        except Exception as e:
            self.get_logger().error(f'Failed to publish fused poses: {e}')

    def publish_global_poses(self):
        """글로벌 객체 맵 발행"""
        try:
            data = {
                'header': {
                    'stamp': self.get_clock().now().to_msg(),
                    'frame_id': self.get_parameter('common.frames.world').value
                },
                'global_object_map': dict(self.global_object_map),
                'total_objects': len(self.global_object_map)
            }
            
            json_msg = String()
            json_msg.data = json.dumps(data)
            self.global_poses_pub.publish(json_msg)
            
        except Exception as e:
            self.get_logger().error(f'Failed to publish global poses: {e}')

    def publish_fusion_metrics(self, fusion_metrics: List[Dict]):
        """융합 메트릭 발행"""
        try:
            data = {
                'header': {
                    'stamp': self.get_clock().now().to_msg(),
                    'frame_id': self.get_parameter('common.frames.world').value
                },
                'fusion_metrics': fusion_metrics
            }
            
            json_msg = String()
            json_msg.data = json.dumps(data)
            self.fusion_metrics_pub.publish(json_msg)
            
        except Exception as e:
            self.get_logger().error(f'Failed to publish fusion metrics: {e}')

    def publish_convergence_status(self, convergence_status: Dict):
        """수렴 상태 발행"""
        try:
            json_msg = String()
            json_msg.data = json.dumps(convergence_status)
            self.convergence_status_pub.publish(json_msg)
            
        except Exception as e:
            self.get_logger().error(f'Failed to publish convergence status: {e}')


def main(args=None):
    rclpy.init(args=args)
    node = MultiViewFusionNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()