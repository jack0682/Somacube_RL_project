"""
수학적 기초 이론 구현
소마큐브 6DoF 포즈 추정의 수학적 정밀 체계
"""

import numpy as np
from scipy.spatial.transform import Rotation as R
from scipy import linalg
from typing import Tuple, List, Optional, Dict, Any
import logging


class MathematicalFoundations:
    """수학적 기초 이론 클래스 (정리 T1-T28 구현)"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 맨해튼 세계 기본 축들 (공리 A1)
        self.manhattan_axes = np.array([
            [1, 0, 0],   # +X
            [0, 1, 0],   # +Y  
            [0, 0, 1],   # +Z
            [-1, 0, 0],  # -X
            [0, -1, 0],  # -Y
            [0, 0, -1]   # -Z
        ])
        
        # 24-회전 그룹 (정육면체 대칭)
        self.rotation_24_group = self._generate_24_rotations()
    
    def _generate_24_rotations(self) -> List[np.ndarray]:
        """정육면체의 24개 회전 대칭 생성 (알고리즘 A1 확장)"""
        rotations = []
        
        # 6개 면 × 4개 회전 방향
        face_rotations = [
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
        
        for rpy in face_rotations:
            rot_matrix = R.from_euler('xyz', np.deg2rad(rpy)).as_matrix()
            rotations.append(rot_matrix)
            
        return rotations
    
    def pinhole_projection(self, points_3d: np.ndarray, K: np.ndarray) -> np.ndarray:
        """정리 T1: 핀홀 카메라 투영 변환"""
        if points_3d.shape[1] != 3:
            raise ValueError("Points must be Nx3 array")
            
        # 동차좌표로 변환
        points_homo = np.column_stack([points_3d, np.ones(points_3d.shape[0])])
        
        # 투영
        projected = K @ points_3d.T  # 3xN
        
        # 정규화 (Z로 나누기)
        valid_mask = projected[2, :] > 0  # 카메라 앞쪽만
        u = projected[0, valid_mask] / projected[2, valid_mask]
        v = projected[1, valid_mask] / projected[2, valid_mask]
        
        return np.column_stack([u, v]), valid_mask
    
    def inverse_projection(self, pixels: np.ndarray, depths: np.ndarray, 
                          K: np.ndarray) -> np.ndarray:
        """정리 T2: 역투영 (픽셀 → 3D)"""
        fx, fy = K[0, 0], K[1, 1]
        cx, cy = K[0, 2], K[1, 2]
        
        # K의 역행렬 (정리 T2 증명)
        K_inv = np.array([
            [1/fx, 0, -cx/fx],
            [0, 1/fy, -cy/fy],
            [0, 0, 1]
        ])
        
        # 역투영
        u, v = pixels[:, 0], pixels[:, 1]
        pixel_homo = np.column_stack([u, v, np.ones(len(u))])
        
        # 3D 좌표 복원
        points_3d = depths[:, np.newaxis] * (K_inv @ pixel_homo.T).T
        return points_3d
    
    def ransac_plane_removal(self, points: np.ndarray, 
                           epsilon: float = 0.005,
                           max_iterations: int = 1000,
                           min_inliers: int = 100) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """정리 T4: RANSAC 기반 평면 제거 (알고리즘 A1)"""
        if points.shape[0] < 3:
            return points, np.array([0, 0, 1]), 0
            
        best_inliers = []
        best_model = None
        best_count = 0
        
        for i in range(max_iterations):
            # 1. 3개 점 샘플링
            if points.shape[0] < 3:
                break
            sample_indices = np.random.choice(points.shape[0], 3, replace=False)
            p1, p2, p3 = points[sample_indices]
            
            # 2. 평면 방정식 계산
            v1, v2 = p2 - p1, p3 - p1
            normal = np.cross(v1, v2)
            
            if np.linalg.norm(normal) < 1e-8:  # 선형 종속
                continue
                
            normal = normal / np.linalg.norm(normal)
            d = -np.dot(normal, p1)
            
            # 3. 인라이어 계산
            distances = np.abs(points @ normal + d)
            inliers = distances < epsilon
            inlier_count = np.sum(inliers)
            
            if inlier_count > best_count:
                best_count = inlier_count
                best_inliers = inliers
                best_model = (normal, d)
        
        if best_model is None or best_count < min_inliers:
            return points, np.array([0, 0, 1]), 0
            
        # 테이블 점들 제거
        outliers = ~best_inliers
        return points[outliers], best_model[0], best_model[1]
    
    def voxel_downsample(self, points: np.ndarray, voxel_size: float) -> np.ndarray:
        """정리 T5: Voxel 다운샘플링"""
        if points.shape[0] == 0:
            return points
            
        # Voxel 격자로 양자화
        voxel_indices = np.floor(points / voxel_size).astype(int)
        
        # 고유한 voxel들 찾기
        unique_voxels, inverse_indices = np.unique(
            voxel_indices, axis=0, return_inverse=True
        )
        
        # 각 voxel의 중심점 계산
        downsampled = []
        for i in range(len(unique_voxels)):
            voxel_points = points[inverse_indices == i]
            centroid = np.mean(voxel_points, axis=0)
            downsampled.append(centroid)
            
        return np.array(downsampled)
    
    def compute_covariance_matrix(self, points: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """정의 D4: 공분산 행렬 계산"""
        if points.shape[0] < 2:
            return np.eye(3), np.zeros(3)
            
        # 중심점
        centroid = np.mean(points, axis=0)
        
        # 중심화
        centered = points - centroid
        
        # 공분산 행렬
        cov_matrix = (centered.T @ centered) / (points.shape[0] - 1)
        
        return cov_matrix, centroid
    
    def spectral_decomposition(self, cov_matrix: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """정리 T7: 고유분해 (Spectral Decomposition)"""
        try:
            eigenvals, eigenvecs = linalg.eigh(cov_matrix)
            
            # 내림차순 정렬
            sort_indices = np.argsort(eigenvals)[::-1]
            eigenvals = eigenvals[sort_indices]
            eigenvecs = eigenvecs[:, sort_indices]
            
            # 양수로 보정
            eigenvals = np.maximum(eigenvals, 0)
            
            return eigenvals, eigenvecs
            
        except Exception as e:
            self.logger.warning(f"Eigendecomposition failed: {e}")
            return np.array([1, 1, 1]), np.eye(3)
    
    def singular_value_decomposition(self, matrix: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """정리 T8: 특이값 분해 (Singular Value Decomposition)"""
        try:
            U, S, Vt = linalg.svd(matrix, full_matrices=False)
            return U, S, Vt
        except Exception as e:
            self.logger.warning(f"SVD failed: {e}")
            m, n = matrix.shape
            return np.eye(m, min(m, n)), np.ones(min(m, n)), np.eye(min(m, n), n)
    
    def compute_pca_confidence(self, eigenvals: np.ndarray) -> Dict[str, float]:
        """정의 D5: 주성분 신뢰도 지표"""
        eigenvals = np.maximum(eigenvals, 1e-12)  # 수치적 안정성
        
        total_var = np.sum(eigenvals)
        
        return {
            'primary_dominance': eigenvals[0] / total_var,      # ρ1
            'planar_ratio': (eigenvals[0] + eigenvals[1]) / total_var,  # ρ12
            'linearity_ratio': eigenvals[0] / eigenvals[1] if eigenvals[1] > 1e-12 else 1e6,
            'isotropy': eigenvals[2] / eigenvals[0]
        }
    
    def is_linear_structure(self, eigenvals: np.ndarray) -> bool:
        """정리 T8: 선형 물체 판정"""
        confidence = self.compute_pca_confidence(eigenvals)
        return (confidence['primary_dominance'] > 0.7 and 
                confidence['linearity_ratio'] > 3.0)
    
    def estimate_surface_normals_knn(self, points: np.ndarray, k: int = 30) -> np.ndarray:
        """알고리즘 A3: KNN 기반 노멀 추정"""
        from scipy.spatial import KDTree
        
        if points.shape[0] < k:
            return np.tile([0, 0, 1], (points.shape[0], 1))
            
        tree = KDTree(points)
        normals = []
        
        for i, point in enumerate(points):
            # k-최근접 이웃
            distances, indices = tree.query(point, k=k+1)
            neighbors = points[indices[1:]]  # 자기 자신 제외
            
            # 지역 공분산
            local_cov, _ = self.compute_covariance_matrix(neighbors)
            eigenvals, eigenvecs = self.spectral_decomposition(local_cov)
            
            # 최소 고유값에 대응하는 벡터가 노멀
            normal = eigenvecs[:, -1]
            
            # 일관된 방향성 보장 (카메라 쪽으로)
            if np.dot(normal, -point) < 0:
                normal = -normal
                
            normals.append(normal)
            
        return np.array(normals)
    
    def align_to_manhattan_world(self, local_axes: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """정리 T13: 맨해튼 축 정렬 (알고리즘 A5)"""
        global_axes = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]]).T
        
        best_score = -np.inf
        best_rotation = np.eye(3)
        
        # 48가지 가능한 정렬 시도
        for perm in [[0,1,2], [0,2,1], [1,0,2], [1,2,0], [2,0,1], [2,1,0]]:
            for signs in [[1,1,1], [1,1,-1], [1,-1,1], [1,-1,-1], 
                         [-1,1,1], [-1,1,-1], [-1,-1,1], [-1,-1,-1]]:
                
                # 부호와 순열 적용
                S = np.diag(signs)[:, perm]  # 3x3
                aligned_axes = local_axes @ S
                
                # Frobenius 노름 기준 점수
                score = np.trace(global_axes.T @ aligned_axes)
                
                if score > best_score:
                    best_score = score
                    best_rotation = global_axes @ aligned_axes.T
        
        return self.orthogonalize_rotation(best_rotation), S
    
    def orthogonalize_rotation(self, R: np.ndarray) -> np.ndarray:
        """정리 T14: SVD 기반 회전 행렬 정규화"""
        try:
            U, S, Vh = np.linalg.svd(R)
            R_ortho = U @ Vh
            
            # det(R) = 1 보장
            if np.linalg.det(R_ortho) < 0:
                U[:, -1] *= -1
                R_ortho = U @ Vh
                
            return R_ortho
            
        except Exception:
            return np.eye(3)
    
    def compute_object_dimensions(self, points: np.ndarray, axes: np.ndarray) -> np.ndarray:
        """정의 D7: 축 방향 치수 계산"""
        if points.shape[0] == 0:
            return np.zeros(3)
            
        # 각 축 방향으로 투영
        projections = points @ axes  # Nx3
        
        # 최대-최소 범위
        dimensions = np.max(projections, axis=0) - np.min(projections, axis=0)
        return dimensions
    
    def compute_geometric_center(self, points: np.ndarray, axes: np.ndarray) -> np.ndarray:
        """정의 D8: 축 정렬된 바운딩 박스 중심"""
        if points.shape[0] == 0:
            return np.zeros(3)
            
        projections = points @ axes
        
        # 각 축의 중점
        min_proj = np.min(projections, axis=0)
        max_proj = np.max(projections, axis=0)
        center_proj = (min_proj + max_proj) / 2
        
        # 원래 좌표계로 변환
        center_3d = center_proj @ axes.T
        return center_3d
    
    def geodesic_distance_SO3(self, R1: np.ndarray, R2: np.ndarray) -> float:
        """SO(3) 매니폴드 상의 측지선 거리"""
        try:
            trace_val = np.trace(R1.T @ R2)
            # 수치적 안정성
            trace_val = np.clip(trace_val, -1, 3)
            angle = np.arccos((trace_val - 1) / 2)
            return angle
        except:
            return 0.0
    
    def riemannian_mean_rotations(self, rotations: List[np.ndarray], 
                                weights: Optional[np.ndarray] = None) -> np.ndarray:
        """정리 T17: SO(3) 상의 Riemannian 평균 (알고리즘 A6)"""
        if not rotations:
            return np.eye(3)
            
        if weights is None:
            weights = np.ones(len(rotations)) / len(rotations)
            
        # 가중 합 행렬
        M = np.zeros((3, 3))
        for R, w in zip(rotations, weights):
            M += w * R
            
        # SVD 기반 평균
        U, _, Vh = np.linalg.svd(M)
        R_mean = U @ Vh
        
        # det 보정
        if np.linalg.det(R_mean) < 0:
            U[:, -1] *= -1
            R_mean = U @ Vh
            
        return R_mean
    
    def huber_robust_mean(self, positions: List[np.ndarray], 
                         weights: Optional[np.ndarray] = None,
                         delta: float = 0.01) -> np.ndarray:
        """정리 T18: Huber 손실 기반 강건 평균"""
        if not positions:
            return np.zeros(3)
            
        if weights is None:
            weights = np.ones(len(positions)) / len(positions)
            
        positions = np.array(positions)
        
        # 초기 추정: 가중 평균
        mean_estimate = np.average(positions, weights=weights, axis=0)
        
        # Huber 손실 최적화 (단순한 반복)
        for _ in range(10):
            residuals = np.linalg.norm(positions - mean_estimate, axis=1)
            
            # Huber 가중치
            huber_weights = np.where(
                residuals <= delta,
                1.0,
                delta / residuals
            )
            
            # 전체 가중치
            total_weights = weights * huber_weights
            total_weights /= np.sum(total_weights)
            
            # 새로운 추정
            new_estimate = np.average(positions, weights=total_weights, axis=0)
            
            if np.linalg.norm(new_estimate - mean_estimate) < 1e-6:
                break
                
            mean_estimate = new_estimate
            
        return mean_estimate