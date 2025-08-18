#!/usr/bin/env python3
"""
포인트클라우드 처리 모듈
테이블 제거, 클러스터링, 복셀 다운샘플링 등의 기능 제공
"""

import numpy as np
from typing import List, Tuple, Optional
from sklearn.cluster import DBSCAN


class PointCloudProcessor:
    """포인트클라우드 처리 클래스"""
    
    def __init__(self):
        """초기화"""
        pass
    
    def remove_table_plane(self, points: np.ndarray, epsilon: float = 0.01, 
                          max_iterations: int = 1000) -> np.ndarray:
        """RANSAC을 사용한 테이블 평면 제거"""
        if len(points) < 100:
            return points
            
        try:
            best_inliers = []
            best_count = 0
            
            for _ in range(max_iterations):
                # 3개 점 샘플링
                if len(points) < 3:
                    break
                    
                sample_indices = np.random.choice(len(points), 3, replace=False)
                p1, p2, p3 = points[sample_indices]
                
                # 평면 방정식 계산
                v1, v2 = p2 - p1, p3 - p1
                normal = np.cross(v1, v2)
                
                if np.linalg.norm(normal) < 1e-8:
                    continue
                    
                normal = normal / np.linalg.norm(normal)
                d = -np.dot(normal, p1)
                
                # 인라이어 계산
                distances = np.abs(points @ normal + d)
                inliers = distances < epsilon
                inlier_count = np.sum(inliers)
                
                if inlier_count > best_count:
                    best_count = inlier_count
                    best_inliers = inliers
                    
            if best_count > 100:  # 충분한 테이블 점들이 있다면
                outliers = ~best_inliers
                return points[outliers]
            else:
                return points
                
        except Exception:
            return points
    
    def cluster_objects(self, points: np.ndarray, eps: float = 0.015, 
                       min_samples: int = 10) -> List[np.ndarray]:
        """DBSCAN을 사용한 객체 클러스터링"""
        if len(points) < min_samples:
            return [points] if len(points) > 0 else []
            
        try:
            clustering = DBSCAN(eps=eps, min_samples=min_samples)
            labels = clustering.fit_predict(points)
            
            clusters = []
            unique_labels = set(labels)
            
            for label in unique_labels:
                if label == -1:  # 노이즈 제외
                    continue
                    
                cluster_mask = labels == label
                cluster_points = points[cluster_mask]
                
                if len(cluster_points) >= min_samples:
                    clusters.append(cluster_points)
                    
            return clusters
            
        except Exception:
            return [points] if len(points) > 0 else []
    
    def voxel_downsample(self, points: np.ndarray, voxel_size: float) -> np.ndarray:
        """복셀 다운샘플링"""
        if len(points) == 0:
            return points
            
        try:
            # Voxel 인덱스 계산
            voxel_indices = np.floor(points / voxel_size).astype(int)
            
            # 고유한 voxel 찾기
            unique_voxels, inverse_indices = np.unique(
                voxel_indices, axis=0, return_inverse=True
            )
            
            # 각 voxel의 대표점 계산 (중심점)
            downsampled_points = []
            
            for i in range(len(unique_voxels)):
                voxel_mask = inverse_indices == i
                voxel_points = points[voxel_mask]
                
                # 중심점
                centroid = np.mean(voxel_points, axis=0)
                downsampled_points.append(centroid)
                    
            return np.array(downsampled_points)
            
        except Exception:
            return points