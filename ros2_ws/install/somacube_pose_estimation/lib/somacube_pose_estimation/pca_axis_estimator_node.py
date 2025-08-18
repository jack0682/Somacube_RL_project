#!/usr/bin/env python3
"""
PCA 기반 축 추정 노드
수학적 정밀 체계 IV단계: 주성분 분석 기반 축 추정 (정리 T7-T12 구현)
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from geometry_msgs.msg import PoseStamped, Vector3Stamped
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

try:
    from sklearn.mixture import GaussianMixture
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False


class PCAxisEstimatorNode(Node):
    """PCA 기반 축 추정 및 면 노멀 분석 (정리 T7-T12)"""
    
    def __init__(self):
        super().__init__('pca_axis_estimator')
        
        # Mathematical foundations
        self.math_foundation = MathematicalFoundations()
        
        # Parameters
        self.declare_parameters_from_yaml()
        
        # Subscribers
        self.segmented_objects_sub = self.create_subscription(
            String,
            '/pointcloud_processor/segmented_objects',
            self.segmented_objects_callback,
            10
        )
        
        # Publishers
        self.axis_estimates_pub = self.create_publisher(
            String,
            '/pca_axis_estimator/axis_estimates',
            10
        )
        
        self.confidence_metrics_pub = self.create_publisher(
            String,
            '/pca_axis_estimator/confidence_metrics',
            10
        )
        
        self.debug_markers_pub = self.create_publisher(
            MarkerArray,
            '/pca_axis_estimator/debug_markers',
            10
        )
        
        self.surface_normals_pub = self.create_publisher(
            String,
            '/pca_axis_estimator/surface_normals',
            10
        )
        
        # State
        self.latest_clusters = []
        self.axis_history = {}  # cluster_id -> list of axis estimates
        
        # Statistics
        self.processed_objects = 0
        self.reliable_estimates = 0
        
        # Timer for processing
        processing_rate = self.get_parameter('pca_axis_estimator.processing_rate_hz').value
        self.timer = self.create_timer(1.0 / processing_rate, self.process_axis_estimation)
        
        self.get_logger().info('PCA Axis Estimator node initialized')
        self.get_logger().info(f'scikit-learn available: {HAS_SKLEARN}')

    def declare_parameters_from_yaml(self):
        """YAML 설정에서 파라미터 선언"""
        defaults = {
            'common.frames.camera': 'camera_link',
            'common.frames.world': 'world',
            
            'pca_axis_estimator.processing_rate_hz': 5.0,
            
            # 정리 T7-T8: PCA 파라미터
            'pca_axis_estimator.pca.min_points': 50,
            'pca_axis_estimator.pca.primary_dominance_threshold': 0.7,
            'pca_axis_estimator.pca.linearity_ratio_threshold': 3.0,
            'pca_axis_estimator.pca.isotropy_threshold': 0.1,
            
            # 정리 T10-T11: 면 노멀 추정
            'pca_axis_estimator.normals.enable': True,
            'pca_axis_estimator.normals.knn_k': 30,
            'pca_axis_estimator.normals.clustering_enable': True,
            'pca_axis_estimator.normals.n_clusters': 6,  # 6개 면 (맨해튼 세계)
            'pca_axis_estimator.normals.consistency_threshold': 0.9,
            
            # 정리 T9: PCA 안정성
            'pca_axis_estimator.stability.history_length': 10,
            'pca_axis_estimator.stability.convergence_threshold': 0.05,  # 라디안
            'pca_axis_estimator.stability.min_stable_frames': 5,
            
            # 수치적 안정성
            'pca_axis_estimator.numerical.eigenvalue_epsilon': 1e-12,
            'pca_axis_estimator.numerical.condition_number_max': 1e6,
            
            # 디버그 및 시각화
            'pca_axis_estimator.debug.visualize_axes': True,
            'pca_axis_estimator.debug.visualize_normals': True,
            'pca_axis_estimator.debug.axis_length_m': 0.05,
        }
        
        for name, default_value in defaults.items():
            self.declare_parameter(name, default_value)

    def segmented_objects_callback(self, msg):
        """세그멘테이션된 객체 콜백"""
        try:
            segmented_data = json.loads(msg.data)
            self.latest_clusters = segmented_data.get('clusters', [])
            self.get_logger().debug(f'Received {len(self.latest_clusters)} clusters')
        except json.JSONDecodeError as e:
            self.get_logger().error(f'Failed to parse segmented objects: {e}')

    def process_axis_estimation(self):
        """메인 축 추정 처리 루프"""
        if not self.latest_clusters:
            return
            
        try:
            axis_estimates = []
            confidence_metrics = []
            debug_markers = MarkerArray()
            surface_normals_data = []
            
            for cluster in self.latest_clusters:
                # 클러스터 점들 추출
                points_list = cluster.get('points', [])
                if not points_list:
                    continue
                    
                points_3d = np.array(points_list)
                cluster_id = cluster.get('label', 0)
                
                # 최소 점수 확인
                min_points = self.get_parameter('pca_axis_estimator.pca.min_points').value
                if len(points_3d) < min_points:
                    continue
                    
                # PCA 축 추정 (정리 T7)
                axis_estimate = self.estimate_pca_axes(points_3d, cluster_id)
                if axis_estimate:
                    axis_estimates.append(axis_estimate)
                    
                    # 신뢰도 계산 (정의 D5, 정리 T8)
                    confidence = self.compute_axis_confidence(axis_estimate)
                    confidence_metrics.append(confidence)
                    
                    # 안정성 추적 (정리 T9)
                    self.update_axis_history(cluster_id, axis_estimate)
                    
                    # 면 노멀 추정 (알고리즘 A3, A4)
                    if self.get_parameter('pca_axis_estimator.normals.enable').value:
                        normals_data = self.estimate_surface_normals(points_3d, cluster_id)
                        if normals_data:
                            surface_normals_data.append(normals_data)
                            
                    # 디버그 마커 생성
                    if self.get_parameter('pca_axis_estimator.debug.visualize_axes').value:
                        markers = self.create_axis_markers(axis_estimate, cluster_id)
                        debug_markers.markers.extend(markers)
                        
                self.processed_objects += 1
                
            # 결과 발행
            if axis_estimates:
                self.publish_axis_estimates(axis_estimates)
                
            if confidence_metrics:
                self.publish_confidence_metrics(confidence_metrics)
                
            if surface_normals_data:
                self.publish_surface_normals(surface_normals_data)
                
            if debug_markers.markers:
                self.debug_markers_pub.publish(debug_markers)
                
        except Exception as e:
            self.get_logger().error(f'Axis estimation error: {e}')

    def estimate_pca_axes(self, points_3d: np.ndarray, cluster_id: int) -> Optional[Dict]:
        """정리 T7: PCA 기반 축 추정"""
        try:
            # 공분산 행렬 계산 (정의 D4)
            cov_matrix, centroid = self.math_foundation.compute_covariance_matrix(points_3d)
            
            # 수치적 안정성 검사
            condition_number = np.linalg.cond(cov_matrix)
            max_condition = self.get_parameter('pca_axis_estimator.numerical.condition_number_max').value
            
            if condition_number > max_condition:
                self.get_logger().warn(f'Ill-conditioned covariance matrix for cluster {cluster_id}')
                return None
                
            # 고유분해 (정리 T7)
            eigenvals, eigenvecs = self.math_foundation.spectral_decomposition(cov_matrix)
            
            # 고유값 검증
            epsilon = self.get_parameter('pca_axis_estimator.numerical.eigenvalue_epsilon').value
            eigenvals = np.maximum(eigenvals, epsilon)
            
            # 축 추정 결과 구성
            axis_estimate = {
                'cluster_id': cluster_id,
                'centroid': centroid.tolist(),
                'eigenvalues': eigenvals.tolist(),
                'eigenvectors': eigenvecs.tolist(),
                'primary_axis': eigenvecs[:, 0].tolist(),    # 주축
                'secondary_axis': eigenvecs[:, 1].tolist(),  # 부축
                'tertiary_axis': eigenvecs[:, 2].tolist(),   # 삼차축
                'total_variance': float(np.sum(eigenvals)),
                'condition_number': float(condition_number),
                'num_points': len(points_3d),
                'timestamp': self.get_clock().now().to_msg()
            }
            
            return axis_estimate
            
        except Exception as e:
            self.get_logger().error(f'PCA estimation error for cluster {cluster_id}: {e}')
            return None

    def compute_axis_confidence(self, axis_estimate: Dict) -> Dict:
        """정의 D5, 정리 T8: 축 추정 신뢰도 계산"""
        eigenvals = np.array(axis_estimate['eigenvalues'])
        cluster_id = axis_estimate['cluster_id']
        
        # 신뢰도 지표 계산 (정의 D5)
        confidence_metrics = self.math_foundation.compute_pca_confidence(eigenvals)
        
        # 선형 구조 판정 (정리 T8)
        is_linear = self.math_foundation.is_linear_structure(eigenvals)
        
        # 추가 신뢰도 지표
        stability_score = self.compute_stability_score(cluster_id)
        
        confidence = {
            'cluster_id': cluster_id,
            'primary_dominance': confidence_metrics['primary_dominance'],
            'planar_ratio': confidence_metrics['planar_ratio'],
            'linearity_ratio': confidence_metrics['linearity_ratio'],
            'isotropy': confidence_metrics['isotropy'],
            'is_linear_structure': is_linear,
            'stability_score': stability_score,
            'overall_confidence': self.compute_overall_confidence(confidence_metrics, stability_score),
            'reliable': self.is_estimate_reliable(confidence_metrics, stability_score),
            'timestamp': self.get_clock().now().to_msg()
        }
        
        if confidence['reliable']:
            self.reliable_estimates += 1
            
        return confidence

    def compute_stability_score(self, cluster_id: int) -> float:
        """정리 T9: PCA 축 추정 안정성 점수"""
        if cluster_id not in self.axis_history:
            return 0.0
            
        history = self.axis_history[cluster_id]
        if len(history) < 2:
            return 0.0
            
        # 최근 추정들 간 각도 편차 계산
        recent_axes = [np.array(est['primary_axis']) for est in history[-5:]]
        
        angle_deviations = []
        for i in range(1, len(recent_axes)):
            # 두 축 간 각도 계산
            cos_angle = np.clip(np.abs(np.dot(recent_axes[i-1], recent_axes[i])), 0, 1)
            angle = np.arccos(cos_angle)
            angle_deviations.append(angle)
            
        if not angle_deviations:
            return 0.0
            
        # 안정성 점수 (각도 편차의 역수)
        mean_deviation = np.mean(angle_deviations)
        convergence_thresh = self.get_parameter('pca_axis_estimator.stability.convergence_threshold').value
        
        if mean_deviation < convergence_thresh:
            stability_score = 1.0 - (mean_deviation / convergence_thresh)
        else:
            stability_score = 0.0
            
        return float(stability_score)

    def compute_overall_confidence(self, pca_metrics: Dict, stability_score: float) -> float:
        """전체 신뢰도 점수 계산"""
        # 가중 평균
        weights = {
            'primary_dominance': 0.3,
            'linearity_ratio': 0.2,
            'isotropy': 0.2,
            'stability': 0.3
        }
        
        # 정규화된 지표들
        norm_primary = min(pca_metrics['primary_dominance'], 1.0)
        norm_linearity = min(pca_metrics['linearity_ratio'] / 10.0, 1.0)  # 10으로 스케일링
        norm_isotropy = 1.0 - min(pca_metrics['isotropy'], 1.0)  # 낮은 isotropy가 좋음
        
        overall = (weights['primary_dominance'] * norm_primary +
                  weights['linearity_ratio'] * norm_linearity +
                  weights['isotropy'] * norm_isotropy +
                  weights['stability'] * stability_score)
        
        return float(overall)

    def is_estimate_reliable(self, pca_metrics: Dict, stability_score: float) -> bool:
        """신뢰할만한 추정인지 판정"""
        primary_thresh = self.get_parameter('pca_axis_estimator.pca.primary_dominance_threshold').value
        linearity_thresh = self.get_parameter('pca_axis_estimator.pca.linearity_ratio_threshold').value
        
        return (pca_metrics['primary_dominance'] > primary_thresh and
                pca_metrics['linearity_ratio'] > linearity_thresh and
                stability_score > 0.5)

    def update_axis_history(self, cluster_id: int, axis_estimate: Dict):
        """축 추정 이력 업데이트 (정리 T9 안정성 추적)"""
        history_length = self.get_parameter('pca_axis_estimator.stability.history_length').value
        
        if cluster_id not in self.axis_history:
            self.axis_history[cluster_id] = []
            
        self.axis_history[cluster_id].append(axis_estimate)
        
        # 이력 길이 제한
        if len(self.axis_history[cluster_id]) > history_length:
            self.axis_history[cluster_id] = self.axis_history[cluster_id][-history_length:]

    def estimate_surface_normals(self, points_3d: np.ndarray, cluster_id: int) -> Optional[Dict]:
        """알고리즘 A3, A4: 면 노멀 추정 및 클러스터링"""
        try:
            # KNN 기반 노멀 추정 (알고리즘 A3)
            k = self.get_parameter('pca_axis_estimator.normals.knn_k').value
            normals = self.math_foundation.estimate_surface_normals_knn(points_3d, k)
            
            if len(normals) == 0:
                return None
                
            # 노멀 클러스터링 (von Mises-Fisher, 알고리즘 A4 변형)
            if self.get_parameter('pca_axis_estimator.normals.clustering_enable').value:
                normal_clusters = self.cluster_normals(normals)
            else:
                normal_clusters = []
                
            # 맨해튼 축과의 정렬도 계산
            manhattan_alignment = self.compute_manhattan_alignment(normals)
            
            normals_data = {
                'cluster_id': cluster_id,
                'num_points': len(points_3d),
                'num_normals': len(normals),
                'normals': normals.tolist(),
                'normal_clusters': normal_clusters,
                'manhattan_alignment': manhattan_alignment,
                'dominant_normals': self.extract_dominant_normals(normals),
                'timestamp': self.get_clock().now().to_msg()
            }
            
            return normals_data
            
        except Exception as e:
            self.get_logger().error(f'Surface normal estimation error: {e}')
            return None

    def cluster_normals(self, normals: np.ndarray) -> List[Dict]:
        """노멀 벡터 클러스터링 (구면 상에서)"""
        if not HAS_SKLEARN or len(normals) < 10:
            return []
            
        try:
            n_clusters = self.get_parameter('pca_axis_estimator.normals.n_clusters').value
            
            # Gaussian Mixture Model on sphere (단순화된 접근)
            # 실제로는 von Mises-Fisher 분포를 사용해야 하지만,
            # 여기서는 정규화된 벡터에 GMM 적용
            
            gmm = GaussianMixture(n_components=n_clusters, random_state=42)
            cluster_labels = gmm.fit_predict(normals)
            
            clusters = []
            for label in range(n_clusters):
                mask = cluster_labels == label
                if np.sum(mask) < 5:  # 최소 클러스터 크기
                    continue
                    
                cluster_normals = normals[mask]
                
                # 클러스터 중심 (평균 방향)
                mean_normal = np.mean(cluster_normals, axis=0)
                mean_normal = mean_normal / np.linalg.norm(mean_normal)
                
                # 클러스터 내 일관성 (각도 표준편차)
                angles_to_mean = []
                for normal in cluster_normals:
                    cos_angle = np.clip(np.dot(normal, mean_normal), -1, 1)
                    angle = np.arccos(np.abs(cos_angle))  # 방향 무관
                    angles_to_mean.append(angle)
                    
                cluster_info = {
                    'label': int(label),
                    'size': int(np.sum(mask)),
                    'mean_normal': mean_normal.tolist(),
                    'angle_std_rad': float(np.std(angles_to_mean)),
                    'consistency': float(1.0 - np.mean(angles_to_mean) / (np.pi/2))  # 0-1 스케일
                }
                
                clusters.append(cluster_info)
                
            return clusters
            
        except Exception as e:
            self.get_logger().error(f'Normal clustering error: {e}')
            return []

    def compute_manhattan_alignment(self, normals: np.ndarray) -> Dict:
        """맨해튼 축과의 정렬도 계산"""
        manhattan_axes = self.math_foundation.manhattan_axes
        
        # 각 맨해튼 축에 대한 정렬도
        alignments = {}
        for i, axis in enumerate(['±X', '±Y', '±Z']):
            # 양방향 축 고려
            axis_vec_pos = manhattan_axes[i]
            axis_vec_neg = manhattan_axes[i + 3]
            
            # 모든 노멀과의 내적 계산
            dots_pos = np.abs(normals @ axis_vec_pos)
            dots_neg = np.abs(normals @ axis_vec_neg)
            
            # 최대 정렬도
            max_alignment = np.maximum(dots_pos, dots_neg)
            
            # 통계
            alignments[axis] = {
                'mean_alignment': float(np.mean(max_alignment)),
                'max_alignment': float(np.max(max_alignment)),
                'aligned_count': int(np.sum(max_alignment > 0.8)),  # cos(36°) ≈ 0.8
                'alignment_ratio': float(np.sum(max_alignment > 0.8) / len(normals))
            }
            
        return alignments

    def extract_dominant_normals(self, normals: np.ndarray) -> List[List[float]]:
        """주요 노멀 방향 추출 (빈도 기준)"""
        if len(normals) == 0:
            return []
            
        try:
            # 구면을 격자로 나누어 히스토그램 생성 (간단한 방법)
            # 더 정교한 방법: 구면 조화함수 또는 HEALPix
            
            # 구면 좌표 변환
            x, y, z = normals[:, 0], normals[:, 1], normals[:, 2]
            
            # Azimuth, elevation angles
            azimuth = np.arctan2(y, x)  # [-π, π]
            elevation = np.arcsin(z)    # [-π/2, π/2]
            
            # 격자화
            n_bins = 18  # 10도 간격
            azimuth_bins = np.linspace(-np.pi, np.pi, n_bins)
            elevation_bins = np.linspace(-np.pi/2, np.pi/2, n_bins//2)
            
            # 2D 히스토그램
            hist, _, _ = np.histogram2d(azimuth, elevation, bins=[azimuth_bins, elevation_bins])
            
            # 상위 피크 찾기
            flat_hist = hist.flatten()
            peak_indices = np.argsort(flat_hist)[-3:]  # 상위 3개
            
            dominant_normals = []
            for idx in peak_indices:
                if flat_hist[idx] < 5:  # 최소 빈도
                    continue
                    
                # 인덱스를 2D 좌표로 변환
                az_idx, el_idx = np.unravel_index(idx, hist.shape)
                
                # 빈 중심의 각도
                az_center = (azimuth_bins[az_idx] + azimuth_bins[az_idx+1]) / 2
                el_center = (elevation_bins[el_idx] + elevation_bins[el_idx+1]) / 2
                
                # 카테시안 좌표로 변환
                x_dom = np.cos(el_center) * np.cos(az_center)
                y_dom = np.cos(el_center) * np.sin(az_center)
                z_dom = np.sin(el_center)
                
                dominant_normals.append([float(x_dom), float(y_dom), float(z_dom)])
                
            return dominant_normals
            
        except Exception as e:
            self.get_logger().error(f'Dominant normals extraction error: {e}')
            return []

    def create_axis_markers(self, axis_estimate: Dict, cluster_id: int) -> List[Marker]:
        """축 시각화 마커 생성"""
        markers = []
        
        try:
            centroid = np.array(axis_estimate['centroid'])
            eigenvecs = np.array(axis_estimate['eigenvectors'])
            eigenvals = np.array(axis_estimate['eigenvalues'])
            
            axis_length = self.get_parameter('pca_axis_estimator.debug.axis_length_m').value
            
            # 축 색상 (RGB)
            axis_colors = [
                [1.0, 0.0, 0.0],  # 주축: 빨강
                [0.0, 1.0, 0.0],  # 부축: 초록
                [0.0, 0.0, 1.0]   # 삼차축: 파랑
            ]
            
            for i in range(3):
                marker = Marker()
                marker.header.frame_id = self.get_parameter('common.frames.camera').value
                marker.header.stamp = self.get_clock().now().to_msg()
                marker.id = cluster_id * 10 + i
                marker.type = Marker.ARROW
                marker.action = Marker.ADD
                
                # 시작점
                marker.points = []
                start_point = geometry_msgs.msg.Point()
                start_point.x, start_point.y, start_point.z = centroid
                
                # 끝점 (축 방향으로 이동, 고유값 크기로 스케일링)
                axis_vec = eigenvecs[:, i] * axis_length * np.sqrt(eigenvals[i])
                end_point = geometry_msgs.msg.Point()
                end_point.x = centroid[0] + axis_vec[0]
                end_point.y = centroid[1] + axis_vec[1]
                end_point.z = centroid[2] + axis_vec[2]
                
                marker.points = [start_point, end_point]
                
                # 스타일
                marker.scale.x = 0.002  # 샤프트 직경
                marker.scale.y = 0.004  # 화살표 머리 직경
                marker.scale.z = 0.008  # 화살표 머리 길이
                
                # 색상
                marker.color.r = axis_colors[i][0]
                marker.color.g = axis_colors[i][1]
                marker.color.b = axis_colors[i][2]
                marker.color.a = 0.8
                
                marker.lifetime.sec = 1  # 1초 후 사라짐
                
                markers.append(marker)
                
        except Exception as e:
            self.get_logger().error(f'Marker creation error: {e}')
            
        return markers

    def publish_axis_estimates(self, axis_estimates: List[Dict]):
        """축 추정 결과 발행"""
        try:
            data = {
                'header': {
                    'stamp': self.get_clock().now().to_msg(),
                    'frame_id': self.get_parameter('common.frames.camera').value
                },
                'total_estimates': len(axis_estimates),
                'estimates': axis_estimates,
                'statistics': {
                    'processed_objects': self.processed_objects,
                    'reliable_estimates': self.reliable_estimates,
                    'reliability_rate': self.reliable_estimates / max(self.processed_objects, 1)
                }
            }
            
            json_msg = String()
            json_msg.data = json.dumps(data)
            self.axis_estimates_pub.publish(json_msg)
            
        except Exception as e:
            self.get_logger().error(f'Failed to publish axis estimates: {e}')

    def publish_confidence_metrics(self, confidence_metrics: List[Dict]):
        """신뢰도 메트릭 발행"""
        try:
            data = {
                'header': {
                    'stamp': self.get_clock().now().to_msg(),
                    'frame_id': self.get_parameter('common.frames.camera').value
                },
                'confidence_metrics': confidence_metrics
            }
            
            json_msg = String()
            json_msg.data = json.dumps(data)
            self.confidence_metrics_pub.publish(json_msg)
            
        except Exception as e:
            self.get_logger().error(f'Failed to publish confidence metrics: {e}')

    def publish_surface_normals(self, surface_normals_data: List[Dict]):
        """면 노멀 데이터 발행"""
        try:
            data = {
                'header': {
                    'stamp': self.get_clock().now().to_msg(),
                    'frame_id': self.get_parameter('common.frames.camera').value
                },
                'surface_normals': surface_normals_data
            }
            
            json_msg = String()
            json_msg.data = json.dumps(data)
            self.surface_normals_pub.publish(json_msg)
            
        except Exception as e:
            self.get_logger().error(f'Failed to publish surface normals: {e}')


def main(args=None):
    rclpy.init(args=args)
    node = PCAxisEstimatorNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()