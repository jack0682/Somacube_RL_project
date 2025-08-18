#!/usr/bin/env python3
"""
포즈 추정 모듈
PCA 기반 축 추출 및 포즈 추정 기능 제공
"""

import numpy as np
from typing import Dict, Tuple
from scipy.spatial.transform import Rotation as R


class PoseEstimator:
    """포즈 추정 클래스"""
    
    def __init__(self):
        """초기화"""
        pass
    
    def extract_pca_axes(self, points: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """PCA 축 추출"""
        if len(points) < 3:
            # 기본 축 반환
            return np.array([1, 0, 0]), np.array([0, 1, 0]), np.array([0, 0, 1])
            
        try:
            # 중심점 계산
            centroid = np.mean(points, axis=0)
            centered_points = points - centroid
            
            # 공분산 행렬
            cov_matrix = np.cov(centered_points.T)
            
            # 고유값 분해
            eigenvalues, eigenvectors = np.linalg.eigh(cov_matrix)
            
            # 내림차순 정렬
            sort_indices = np.argsort(eigenvalues)[::-1]
            eigenvalues = eigenvalues[sort_indices]
            eigenvectors = eigenvectors[:, sort_indices]
            
            primary_axis = eigenvectors[:, 0]
            secondary_axis = eigenvectors[:, 1]
            tertiary_axis = eigenvectors[:, 2]
            
            return primary_axis, secondary_axis, tertiary_axis
            
        except Exception:
            # 오류 시 기본 축 반환
            return np.array([1, 0, 0]), np.array([0, 1, 0]), np.array([0, 0, 1])
    
    def estimate_pose(self, points: np.ndarray) -> Dict:
        """포즈 추정"""
        if len(points) < 3:
            return {
                'position': [0, 0, 0],
                'orientation': [0, 0, 0, 1],
                'confidence': 0.0
            }
            
        try:
            # 중심점 계산
            centroid = np.mean(points, axis=0)
            
            # PCA 축 추출
            primary, secondary, tertiary = self.extract_pca_axes(points)
            
            # 회전 행렬 구성
            rotation_matrix = np.column_stack([primary, secondary, tertiary])
            
            # 쿼터니언 변환
            rotation = R.from_matrix(rotation_matrix)
            quaternion = rotation.as_quat()  # [x, y, z, w]
            
            # 신뢰도 계산 (간단한 기준)
            centered_points = points - centroid
            cov_matrix = np.cov(centered_points.T)
            eigenvalues = np.linalg.eigvals(cov_matrix)
            eigenvalues = np.sort(eigenvalues)[::-1]
            
            # 주축의 지배도로 신뢰도 계산
            if eigenvalues[1] > 0:
                confidence = min(eigenvalues[0] / eigenvalues[1], 5.0) / 5.0
            else:
                confidence = 1.0
                
            confidence = max(0.0, min(1.0, confidence))
            
            return {
                'position': centroid.tolist(),
                'orientation': quaternion.tolist(),
                'confidence': float(confidence)
            }
            
        except Exception:
            return {
                'position': [0, 0, 0],
                'orientation': [0, 0, 0, 1],
                'confidence': 0.0
            }