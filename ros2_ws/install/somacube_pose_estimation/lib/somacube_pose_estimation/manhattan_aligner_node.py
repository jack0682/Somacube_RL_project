#!/usr/bin/env python3
"""
맨해튼 정렬 및 자세 복원 노드
수학적 정밀 체계 VI단계: 맨해튼 정렬과 자세 복원 (정리 T12-T16 구현)
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from geometry_msgs.msg import PoseStamped, PoseArray
from visualization_msgs.msg import Marker, MarkerArray
import numpy as np
import json
from scipy.spatial.transform import Rotation as R
from typing import Dict, List, Tuple, Optional

# Import mathematical foundations
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from somacube_pose_estimation.mathematical_foundations import MathematicalFoundations


class ManhattanAlignerNode(Node):
    """맨해튼 정렬 및 6DoF 자세 복원 (정리 T12-T16)"""
    
    def __init__(self):
        super().__init__('manhattan_aligner')
        
        # Mathematical foundations
        self.math_foundation = MathematicalFoundations()
        
        # Parameters
        self.declare_parameters_from_yaml()
        
        # Subscribers
        self.axis_estimates_sub = self.create_subscription(
            String,
            '/pca_axis_estimator/axis_estimates',
            self.axis_estimates_callback,
            10
        )
        
        self.surface_normals_sub = self.create_subscription(
            String,
            '/pca_axis_estimator/surface_normals',
            self.surface_normals_callback,
            10
        )
        
        self.segmented_objects_sub = self.create_subscription(
            String,
            '/pointcloud_processor/segmented_objects',
            self.segmented_objects_callback,
            10
        )
        
        # Publishers
        self.aligned_poses_pub = self.create_publisher(
            String,
            '/manhattan_aligner/aligned_poses',
            10
        )
        
        self.pose_array_pub = self.create_publisher(
            PoseArray,
            '/manhattan_aligner/pose_array',
            10
        )
        
        self.quality_metrics_pub = self.create_publisher(
            String,
            '/manhattan_aligner/quality_metrics',
            10
        )
        
        self.debug_markers_pub = self.create_publisher(
            MarkerArray,
            '/manhattan_aligner/debug_markers',
            10
        )
        
        # State
        self.latest_axis_estimates = []
        self.latest_surface_normals = []
        self.latest_clusters = []
        
        # 24-rotation group for cube symmetries
        self.rotation_24_group = self.math_foundation.rotation_24_group
        
        # Statistics
        self.processed_poses = 0
        self.successful_alignments = 0
        self.alignment_failures = 0
        
        # Timer for processing
        processing_rate = self.get_parameter('manhattan_aligner.processing_rate_hz').value
        self.timer = self.create_timer(1.0 / processing_rate, self.process_manhattan_alignment)
        
        self.get_logger().info('Manhattan Aligner node initialized')

    def declare_parameters_from_yaml(self):
        """YAML 설정에서 파라미터 선언"""
        defaults = {
            'common.frames.camera': 'camera_link',
            'common.frames.world': 'world',
            
            'manhattan_aligner.processing_rate_hz': 5.0,
            
            # 정리 T13: 최적 축 정렬
            'manhattan_aligner.alignment.method': 'brute_force',  # 'brute_force' or 'optimization'
            'manhattan_aligner.alignment.score_threshold': 0.7,
            'manhattan_aligner.alignment.max_iterations': 48,  # 24 rotations * 2 (flip test)
            
            # 정리 T14: 회전 행렬 정규화
            'manhattan_aligner.orthogonalization.enable': True,
            'manhattan_aligner.orthogonalization.tolerance': 1e-6,
            'manhattan_aligner.orthogonalization.max_condition_number': 1e12,
            
            # 정리 T15-T16: 치수 및 위치 계산
            'manhattan_aligner.dimensions.enable': True,
            'manhattan_aligner.dimensions.noise_tolerance_m': 0.002,
            'manhattan_aligner.dimensions.quantization_error_m': 0.001,
            
            # 보조정리 L2: 테이블 접촉 조건
            'manhattan_aligner.table_contact.enable': True,
            'manhattan_aligner.table_contact.tolerance_m': 0.005,
            'manhattan_aligner.table_contact.table_z': 0.0,
            
            # 다중 방법 융합
            'manhattan_aligner.fusion.enable_pca': True,
            'manhattan_aligner.fusion.enable_normals': True,
            'manhattan_aligner.fusion.pca_weight': 0.6,
            'manhattan_aligner.fusion.normals_weight': 0.4,
            
            # 품질 검증
            'manhattan_aligner.validation.min_inlier_ratio': 0.6,
            'manhattan_aligner.validation.max_residual_m': 0.01,
            'manhattan_aligner.validation.min_coverage_ratio': 0.8,
            
            # 디버그 시각화
            'manhattan_aligner.debug.visualize_poses': True,
            'manhattan_aligner.debug.visualize_obb': True,
            'manhattan_aligner.debug.pose_scale': 0.05,
        }
        
        for name, default_value in defaults.items():
            self.declare_parameter(name, default_value)

    def axis_estimates_callback(self, msg):
        """축 추정 결과 콜백"""
        try:
            axis_data = json.loads(msg.data)
            self.latest_axis_estimates = axis_data.get('estimates', [])
            self.get_logger().debug(f'Received {len(self.latest_axis_estimates)} axis estimates')
        except json.JSONDecodeError as e:
            self.get_logger().error(f'Failed to parse axis estimates: {e}')

    def surface_normals_callback(self, msg):
        """면 노멀 데이터 콜백"""
        try:
            normals_data = json.loads(msg.data)
            self.latest_surface_normals = normals_data.get('surface_normals', [])
            self.get_logger().debug(f'Received {len(self.latest_surface_normals)} surface normal data')
        except json.JSONDecodeError as e:
            self.get_logger().error(f'Failed to parse surface normals: {e}')

    def segmented_objects_callback(self, msg):
        """세그멘테이션된 객체 콜백"""
        try:
            segmented_data = json.loads(msg.data)
            self.latest_clusters = segmented_data.get('clusters', [])
        except json.JSONDecodeError as e:
            self.get_logger().error(f'Failed to parse segmented objects: {e}')

    def process_manhattan_alignment(self):
        """메인 맨해튼 정렬 처리 루프"""
        if not self.latest_axis_estimates:
            return
            
        try:
            aligned_poses = []
            quality_metrics = []
            debug_markers = MarkerArray()
            
            for axis_estimate in self.latest_axis_estimates:
                cluster_id = axis_estimate.get('cluster_id', 0)
                
                # 해당 클러스터의 점군 데이터 찾기
                cluster_points = self.find_cluster_points(cluster_id)
                if cluster_points is None:
                    continue
                    
                # 해당 클러스터의 면 노멀 데이터 찾기
                surface_normals = self.find_surface_normals(cluster_id)
                
                # 맨해튼 정렬 수행 (정리 T13)
                aligned_pose = self.perform_manhattan_alignment(
                    axis_estimate, surface_normals, cluster_points
                )
                
                if aligned_pose is not None:
                    aligned_poses.append(aligned_pose)
                    
                    # 품질 메트릭 계산 (정리 T15-T16)
                    quality = self.compute_pose_quality(aligned_pose, cluster_points)
                    quality_metrics.append(quality)
                    
                    # 디버그 마커 생성
                    if self.get_parameter('manhattan_aligner.debug.visualize_poses').value:
                        markers = self.create_pose_markers(aligned_pose, cluster_id)
                        debug_markers.markers.extend(markers)
                        
                    self.successful_alignments += 1
                else:
                    self.alignment_failures += 1
                    
                self.processed_poses += 1
                
            # 결과 발행
            if aligned_poses:
                self.publish_aligned_poses(aligned_poses)
                self.publish_pose_array(aligned_poses)
                
            if quality_metrics:
                self.publish_quality_metrics(quality_metrics)
                
            if debug_markers.markers:
                self.debug_markers_pub.publish(debug_markers)
                
        except Exception as e:
            self.get_logger().error(f'Manhattan alignment error: {e}')

    def find_cluster_points(self, cluster_id: int) -> Optional[np.ndarray]:
        """클러스터 ID에 해당하는 점군 찾기"""
        for cluster in self.latest_clusters:
            if cluster.get('label') == cluster_id:
                points_list = cluster.get('points', [])
                if points_list:
                    return np.array(points_list)
        return None

    def find_surface_normals(self, cluster_id: int) -> Optional[Dict]:
        """클러스터 ID에 해당하는 면 노멀 데이터 찾기"""
        for normals_data in self.latest_surface_normals:
            if normals_data.get('cluster_id') == cluster_id:
                return normals_data
        return None

    def perform_manhattan_alignment(self, axis_estimate: Dict, 
                                  surface_normals: Optional[Dict],
                                  cluster_points: np.ndarray) -> Optional[Dict]:
        """정리 T13: 맨해튼 축 정렬 수행"""
        try:
            cluster_id = axis_estimate['cluster_id']
            
            # PCA 축 추출
            pca_axes = np.array(axis_estimate['eigenvectors'])  # 3x3 matrix
            
            # 방법 1: PCA 기반 정렬 (정리 T13)
            if self.get_parameter('manhattan_aligner.fusion.enable_pca').value:
                pca_alignment = self.align_pca_axes_to_manhattan(pca_axes)
            else:
                pca_alignment = None
                
            # 방법 2: 면 노멀 기반 정렬 (정리 T12)
            if (self.get_parameter('manhattan_aligner.fusion.enable_normals').value and 
                surface_normals is not None):
                normals_alignment = self.align_normals_to_manhattan(surface_normals)
            else:
                normals_alignment = None
                
            # 두 방법 융합
            best_alignment = self.fuse_alignment_methods(pca_alignment, normals_alignment)
            
            if best_alignment is None:
                return None
                
            # 회전 행렬 정규화 (정리 T14)
            if self.get_parameter('manhattan_aligner.orthogonalization.enable').value:
                best_rotation = self.math_foundation.orthogonalize_rotation(best_alignment['rotation'])
            else:
                best_rotation = best_alignment['rotation']
                
            # 치수 계산 (정리 T15)
            aligned_axes = best_rotation.T  # World axes in local coordinates
            dimensions = self.math_foundation.compute_object_dimensions(cluster_points, aligned_axes)
            
            # 기하학적 중심 계산 (정리 T16)
            geometric_center = self.math_foundation.compute_geometric_center(cluster_points, aligned_axes)
            
            # 테이블 접촉 조건 검증 (보조정리 L2)
            contact_validation = self.validate_table_contact(cluster_points, best_rotation, geometric_center)
            
            # 최종 자세 구성
            aligned_pose = {
                'cluster_id': cluster_id,
                'position': geometric_center.tolist(),
                'rotation_matrix': best_rotation.tolist(),
                'quaternion': R.from_matrix(best_rotation).as_quat().tolist(),  # [x,y,z,w]
                'dimensions': dimensions.tolist(),
                'centroid': np.array(axis_estimate['centroid']).tolist(),
                'alignment_score': best_alignment['score'],
                'alignment_method': best_alignment['method'],
                'contact_validation': contact_validation,
                'num_points': len(cluster_points),
                'timestamp': self.get_clock().now().to_msg()
            }
            
            return aligned_pose
            
        except Exception as e:
            self.get_logger().error(f'Manhattan alignment error for cluster {cluster_id}: {e}')
            return None

    def align_pca_axes_to_manhattan(self, pca_axes: np.ndarray) -> Optional[Dict]:
        """정리 T13: PCA 축을 맨해튼 축에 정렬 (알고리즘 A5)"""
        try:
            method = self.get_parameter('manhattan_aligner.alignment.method').value
            
            if method == 'brute_force':
                return self.brute_force_alignment(pca_axes)
            elif method == 'optimization':
                return self.optimization_alignment(pca_axes)
            else:
                self.get_logger().error(f'Unknown alignment method: {method}')
                return None
                
        except Exception as e:
            self.get_logger().error(f'PCA axes alignment error: {e}')
            return None

    def brute_force_alignment(self, local_axes: np.ndarray) -> Optional[Dict]:
        """브루트 포스 축 정렬 (알고리즘 A5)"""
        global_axes = np.eye(3)  # World coordinate axes
        
        best_score = -np.inf
        best_rotation = None
        best_permutation = None
        
        # 모든 가능한 축 순열 시도 (6가지)
        permutations = [
            [0, 1, 2], [0, 2, 1], [1, 0, 2],
            [1, 2, 0], [2, 0, 1], [2, 1, 0]
        ]
        
        # 모든 가능한 부호 조합 시도 (8가지)
        sign_combinations = [
            [1, 1, 1], [1, 1, -1], [1, -1, 1], [1, -1, -1],
            [-1, 1, 1], [-1, 1, -1], [-1, -1, 1], [-1, -1, -1]
        ]
        
        for perm in permutations:
            for signs in sign_combinations:
                # 축 변환 적용
                reordered_axes = local_axes[:, perm]  # 순열
                signed_axes = reordered_axes * np.array(signs)  # 부호
                
                # 변환 행렬 계산
                try:
                    rotation_candidate = global_axes @ signed_axes.T
                    
                    # 회전 행렬 유효성 검사
                    if not self.is_valid_rotation_matrix(rotation_candidate):
                        continue
                        
                    # 정렬 점수 계산 (Frobenius norm)
                    score = np.trace(rotation_candidate @ signed_axes @ signed_axes.T @ rotation_candidate.T)
                    
                    if score > best_score:
                        best_score = score
                        best_rotation = rotation_candidate
                        best_permutation = (perm, signs)
                        
                except np.linalg.LinAlgError:
                    continue
                    
        if best_rotation is None:
            return None
            
        return {
            'rotation': best_rotation,
            'score': float(best_score),
            'method': 'pca_brute_force',
            'permutation': best_permutation
        }

    def optimization_alignment(self, local_axes: np.ndarray) -> Optional[Dict]:
        """최적화 기반 축 정렬 (더 효율적이지만 지역 최적해 가능성)"""
        try:
            from scipy.optimize import minimize
            
            def objective(params):
                # 파라미터를 회전 행렬로 변환 (로드리게스 벡터)
                rotation_vec = params[:3]
                rotation_matrix = R.from_rotvec(rotation_vec).as_matrix()
                
                # 정렬 점수 (음수로 변환하여 최소화 문제로)
                transformed_axes = rotation_matrix @ local_axes
                manhattan_axes = np.eye(3)
                
                # 각 축의 맨해튼 축과의 정렬도
                alignment_score = 0
                for i in range(3):
                    max_dot = 0
                    for j in range(3):
                        dot_product = abs(np.dot(transformed_axes[:, i], manhattan_axes[:, j]))
                        max_dot = max(max_dot, dot_product)
                    alignment_score += max_dot
                    
                return -alignment_score  # 최소화를 위해 음수
            
            # 초기 추정 (항등원)
            initial_guess = np.zeros(3)
            
            # 최적화 실행
            result = minimize(
                objective,
                initial_guess,
                method='BFGS',
                options={'maxiter': 100}
            )
            
            if not result.success:
                return None
                
            # 최적 회전 행렬
            optimal_rotation = R.from_rotvec(result.x).as_matrix()
            
            return {
                'rotation': optimal_rotation,
                'score': float(-result.fun),  # 원래 점수로 복원
                'method': 'pca_optimization',
                'iterations': result.nit
            }
            
        except ImportError:
            self.get_logger().warn('SciPy not available for optimization, using brute force')
            return self.brute_force_alignment(local_axes)
        except Exception as e:
            self.get_logger().error(f'Optimization alignment error: {e}')
            return None

    def align_normals_to_manhattan(self, surface_normals: Dict) -> Optional[Dict]:
        """정리 T12: 면 노멀을 기반으로 직교 축 복원"""
        try:
            normals_list = surface_normals.get('normals', [])
            if not normals_list:
                return None
                
            normals_array = np.array(normals_list)
            
            # 주요 노멀들 추출
            dominant_normals = surface_normals.get('dominant_normals', [])
            if len(dominant_normals) < 2:
                return None
                
            # 첫 두 개의 주요 노멀로 직교 기저 구성 (정리 T12)
            n1 = np.array(dominant_normals[0])
            n2 = np.array(dominant_normals[1])
            
            # Gram-Schmidt 직교화
            a1 = n1 / np.linalg.norm(n1)
            
            # n2에서 n1 성분 제거
            n2_proj = n2 - np.dot(n2, a1) * a1
            if np.linalg.norm(n2_proj) < 1e-6:  # 거의 평행한 경우
                return None
                
            a2 = n2_proj / np.linalg.norm(n2_proj)
            a3 = np.cross(a1, a2)
            
            # 직교 행렬 구성
            local_frame = np.column_stack([a1, a2, a3])
            
            # 맨해튼 축에 정렬
            aligned_rotation, _ = self.math_foundation.align_to_manhattan_world(local_frame)
            
            # 정렬 점수 계산 (맨해튼 축과의 일치도)
            manhattan_axes = np.eye(3)
            transformed_axes = aligned_rotation @ local_frame
            
            score = 0
            for i in range(3):
                max_alignment = 0
                for j in range(3):
                    alignment = abs(np.dot(transformed_axes[:, i], manhattan_axes[:, j]))
                    max_alignment = max(max_alignment, alignment)
                score += max_alignment
            score /= 3  # 평균
            
            return {
                'rotation': aligned_rotation,
                'score': float(score),
                'method': 'normals_gramschmidt',
                'local_frame': local_frame.tolist()
            }
            
        except Exception as e:
            self.get_logger().error(f'Normals alignment error: {e}')
            return None

    def fuse_alignment_methods(self, pca_alignment: Optional[Dict], 
                             normals_alignment: Optional[Dict]) -> Optional[Dict]:
        """PCA와 면 노멀 기반 정렬 결과 융합"""
        if pca_alignment is None and normals_alignment is None:
            return None
            
        if pca_alignment is None:
            return normals_alignment
            
        if normals_alignment is None:
            return pca_alignment
            
        # 가중 평균 기반 융합
        pca_weight = self.get_parameter('manhattan_aligner.fusion.pca_weight').value
        normals_weight = self.get_parameter('manhattan_aligner.fusion.normals_weight').value
        
        # 점수 기반 선택 (간단한 방법)
        pca_score = pca_alignment['score']
        normals_score = normals_alignment['score']
        
        weighted_pca_score = pca_score * pca_weight
        weighted_normals_score = normals_score * normals_weight
        
        if weighted_pca_score > weighted_normals_score:
            best_alignment = pca_alignment.copy()
            best_alignment['fusion_method'] = 'pca_dominant'
            best_alignment['alternative_score'] = normals_score
        else:
            best_alignment = normals_alignment.copy()
            best_alignment['fusion_method'] = 'normals_dominant'
            best_alignment['alternative_score'] = pca_score
            
        return best_alignment

    def is_valid_rotation_matrix(self, R: np.ndarray, tolerance: float = 1e-6) -> bool:
        """회전 행렬 유효성 검사"""
        if R.shape != (3, 3):
            return False
            
        # 직교성 검사: R^T @ R = I
        should_be_identity = R.T @ R
        identity_error = np.linalg.norm(should_be_identity - np.eye(3))
        
        if identity_error > tolerance:
            return False
            
        # 결정자 검사: det(R) = 1
        det_error = abs(np.linalg.det(R) - 1.0)
        if det_error > tolerance:
            return False
            
        return True

    def validate_table_contact(self, points: np.ndarray, rotation: np.ndarray, 
                             center: np.ndarray) -> Dict:
        """보조정리 L2: 테이블 접촉 조건 검증"""
        try:
            if not self.get_parameter('manhattan_aligner.table_contact.enable').value:
                return {'enabled': False}
                
            table_z = self.get_parameter('manhattan_aligner.table_contact.table_z').value
            tolerance = self.get_parameter('manhattan_aligner.table_contact.tolerance_m').value
            
            # 점들을 정렬된 좌표계로 변환
            centered_points = points - center
            aligned_points = (rotation.T @ centered_points.T).T
            
            # 최하단 점들
            min_z = np.min(aligned_points[:, 2])
            contact_points = aligned_points[aligned_points[:, 2] < min_z + tolerance]
            
            # 테이블 접촉 검증
            expected_contact_z = table_z - center[2]  # 센터 기준 상대 높이
            contact_error = abs(min_z - expected_contact_z)
            
            is_valid_contact = contact_error < tolerance
            contact_ratio = len(contact_points) / len(points)
            
            return {
                'enabled': True,
                'is_valid': is_valid_contact,
                'contact_error_m': float(contact_error),
                'contact_ratio': float(contact_ratio),
                'min_z_local': float(min_z),
                'expected_z_local': float(expected_contact_z),
                'num_contact_points': len(contact_points)
            }
            
        except Exception as e:
            self.get_logger().error(f'Table contact validation error: {e}')
            return {'enabled': True, 'error': str(e)}

    def compute_pose_quality(self, aligned_pose: Dict, cluster_points: np.ndarray) -> Dict:
        """포즈 품질 메트릭 계산 (정리 T20-T23)"""
        try:
            cluster_id = aligned_pose['cluster_id']
            rotation = np.array(aligned_pose['rotation_matrix'])
            center = np.array(aligned_pose['position'])
            
            # 점들을 정렬된 좌표계로 변환
            centered_points = cluster_points - center
            aligned_points = (rotation.T @ centered_points.T).T
            
            # Coverage 메트릭 (정의 D11)
            dimensions = np.array(aligned_pose['dimensions'])
            bbox_volume = np.prod(dimensions)
            
            # 실제 점들이 차지하는 부피 (근사)
            if len(cluster_points) > 10:
                from scipy.spatial import ConvexHull
                try:
                    hull = ConvexHull(aligned_points)
                    actual_volume = hull.volume
                    coverage = min(actual_volume / bbox_volume, 1.0) if bbox_volume > 0 else 0.0
                except:
                    coverage = 0.5  # 기본값
            else:
                coverage = 0.5
                
            # 경계 정확도 (정의 D12 간소화)
            # OBB 내부 점들 비율
            half_dims = dimensions / 2
            inside_bbox = np.all(np.abs(aligned_points) <= half_dims, axis=1)
            bbox_inlier_ratio = np.sum(inside_bbox) / len(cluster_points)
            
            # 잔차 분석
            # 축 정렬된 좌표에서 각 면까지의 거리
            residuals = []
            for i in range(3):
                face_distances_pos = half_dims[i] - aligned_points[:, i]
                face_distances_neg = half_dims[i] + aligned_points[:, i]
                
                # 각 점에서 가장 가까운 면까지의 거리
                min_face_dist = np.minimum(
                    np.abs(face_distances_pos),
                    np.abs(face_distances_neg)
                )
                residuals.extend(min_face_dist)
                
            residuals = np.array(residuals)
            mean_residual = np.mean(residuals)
            residual_std = np.std(residuals)
            
            # 전체 품질 점수
            alignment_score = aligned_pose.get('alignment_score', 0.0)
            
            # 정규화된 점수들을 결합
            quality_components = {
                'coverage': coverage,
                'bbox_inlier_ratio': bbox_inlier_ratio,
                'alignment_score_norm': min(alignment_score, 1.0),
                'residual_score': max(0, 1.0 - mean_residual / 0.01)  # 1cm 기준
            }
            
            # 가중 평균
            weights = [0.3, 0.3, 0.25, 0.15]
            overall_quality = sum(w * s for w, s in zip(weights, quality_components.values()))
            
            # 신뢰도 등급
            if overall_quality > 0.8:
                confidence_level = 'high'
            elif overall_quality > 0.6:
                confidence_level = 'medium'
            elif overall_quality > 0.4:
                confidence_level = 'low'
            else:
                confidence_level = 'very_low'
                
            return {
                'cluster_id': cluster_id,
                'overall_quality': float(overall_quality),
                'confidence_level': confidence_level,
                'components': quality_components,
                'metrics': {
                    'coverage_ratio': float(coverage),
                    'bbox_inlier_ratio': float(bbox_inlier_ratio),
                    'mean_residual_m': float(mean_residual),
                    'residual_std_m': float(residual_std),
                    'alignment_score': float(alignment_score),
                    'bbox_volume_m3': float(bbox_volume),
                },
                'validation_flags': {
                    'sufficient_coverage': coverage > 0.6,
                    'low_residuals': mean_residual < 0.01,
                    'good_alignment': alignment_score > 0.7,
                    'table_contact_valid': aligned_pose.get('contact_validation', {}).get('is_valid', False)
                },
                'timestamp': self.get_clock().now().to_msg()
            }
            
        except Exception as e:
            self.get_logger().error(f'Quality computation error: {e}')
            return {
                'cluster_id': aligned_pose.get('cluster_id', 0),
                'overall_quality': 0.0,
                'confidence_level': 'error',
                'error': str(e)
            }

    def create_pose_markers(self, aligned_pose: Dict, cluster_id: int) -> List[Marker]:
        """포즈 시각화 마커 생성"""
        markers = []
        
        try:
            position = aligned_pose['position']
            rotation_matrix = np.array(aligned_pose['rotation_matrix'])
            dimensions = aligned_pose['dimensions']
            
            # 좌표계 마커 (X, Y, Z 축)
            pose_scale = self.get_parameter('manhattan_aligner.debug.pose_scale').value
            axis_colors = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]  # RGB
            
            for i in range(3):
                marker = Marker()
                marker.header.frame_id = self.get_parameter('common.frames.camera').value
                marker.header.stamp = self.get_clock().now().to_msg()
                marker.id = cluster_id * 100 + i
                marker.type = Marker.ARROW
                marker.action = Marker.ADD
                
                # 시작점
                start_point = geometry_msgs.msg.Point()
                start_point.x, start_point.y, start_point.z = position
                
                # 끝점 (축 방향)
                axis_vec = rotation_matrix[:, i] * pose_scale
                end_point = geometry_msgs.msg.Point()
                end_point.x = position[0] + axis_vec[0]
                end_point.y = position[1] + axis_vec[1]
                end_point.z = position[2] + axis_vec[2]
                
                marker.points = [start_point, end_point]
                
                # 스타일
                marker.scale.x = 0.003  # 샤프트
                marker.scale.y = 0.006  # 머리
                marker.scale.z = 0.01   # 길이
                
                # 색상
                marker.color.r = axis_colors[i][0]
                marker.color.g = axis_colors[i][1] 
                marker.color.b = axis_colors[i][2]
                marker.color.a = 0.9
                
                marker.lifetime.sec = 2
                markers.append(marker)
                
            # OBB 마커
            if self.get_parameter('manhattan_aligner.debug.visualize_obb').value:
                obb_marker = Marker()
                obb_marker.header.frame_id = self.get_parameter('common.frames.camera').value
                obb_marker.header.stamp = self.get_clock().now().to_msg()
                obb_marker.id = cluster_id * 100 + 10
                obb_marker.type = Marker.CUBE
                obb_marker.action = Marker.ADD
                
                # 위치
                obb_marker.pose.position.x = position[0]
                obb_marker.pose.position.y = position[1]
                obb_marker.pose.position.z = position[2]
                
                # 회전 (쿼터니언)
                quat = R.from_matrix(rotation_matrix).as_quat()
                obb_marker.pose.orientation.x = quat[0]
                obb_marker.pose.orientation.y = quat[1]
                obb_marker.pose.orientation.z = quat[2]
                obb_marker.pose.orientation.w = quat[3]
                
                # 크기
                obb_marker.scale.x = dimensions[0]
                obb_marker.scale.y = dimensions[1]
                obb_marker.scale.z = dimensions[2]
                
                # 스타일 (투명 와이어프레임)
                obb_marker.color.r = 1.0
                obb_marker.color.g = 1.0
                obb_marker.color.b = 0.0
                obb_marker.color.a = 0.3
                
                obb_marker.lifetime.sec = 2
                markers.append(obb_marker)
                
        except Exception as e:
            self.get_logger().error(f'Pose marker creation error: {e}')
            
        return markers

    def publish_aligned_poses(self, aligned_poses: List[Dict]):
        """정렬된 포즈 발행"""
        try:
            data = {
                'header': {
                    'stamp': self.get_clock().now().to_msg(),
                    'frame_id': self.get_parameter('common.frames.camera').value
                },
                'total_poses': len(aligned_poses),
                'poses': aligned_poses,
                'statistics': {
                    'processed_poses': self.processed_poses,
                    'successful_alignments': self.successful_alignments,
                    'alignment_failures': self.alignment_failures,
                    'success_rate': self.successful_alignments / max(self.processed_poses, 1)
                }
            }
            
            json_msg = String()
            json_msg.data = json.dumps(data)
            self.aligned_poses_pub.publish(json_msg)
            
        except Exception as e:
            self.get_logger().error(f'Failed to publish aligned poses: {e}')

    def publish_pose_array(self, aligned_poses: List[Dict]):
        """PoseArray 메시지 발행"""
        try:
            pose_array = PoseArray()
            pose_array.header.stamp = self.get_clock().now().to_msg()
            pose_array.header.frame_id = self.get_parameter('common.frames.camera').value
            
            for aligned_pose in aligned_poses:
                pose = geometry_msgs.msg.Pose()
                
                # 위치
                position = aligned_pose['position']
                pose.position.x = position[0]
                pose.position.y = position[1]
                pose.position.z = position[2]
                
                # 회전 (쿼터니언)
                quat = aligned_pose['quaternion']
                pose.orientation.x = quat[0]
                pose.orientation.y = quat[1]
                pose.orientation.z = quat[2]
                pose.orientation.w = quat[3]
                
                pose_array.poses.append(pose)
                
            self.pose_array_pub.publish(pose_array)
            
        except Exception as e:
            self.get_logger().error(f'Failed to publish pose array: {e}')

    def publish_quality_metrics(self, quality_metrics: List[Dict]):
        """품질 메트릭 발행"""
        try:
            data = {
                'header': {
                    'stamp': self.get_clock().now().to_msg(),
                    'frame_id': self.get_parameter('common.frames.camera').value
                },
                'quality_metrics': quality_metrics
            }
            
            json_msg = String()
            json_msg.data = json.dumps(data)
            self.quality_metrics_pub.publish(json_msg)
            
        except Exception as e:
            self.get_logger().error(f'Failed to publish quality metrics: {e}')


def main(args=None):
    rclpy.init(args=args)
    node = ManhattanAlignerNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()