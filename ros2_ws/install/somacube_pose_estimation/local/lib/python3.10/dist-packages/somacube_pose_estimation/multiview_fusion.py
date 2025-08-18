#!/usr/bin/env python3
"""
멀티뷰 융합 모듈
여러 뷰에서의 포즈 추정 결과를 융합하는 기능 제공
"""

import numpy as np
from typing import List, Dict
from scipy.spatial.transform import Rotation as R


class MultiViewFusion:
    """멀티뷰 융합 클래스"""
    
    def __init__(self):
        """초기화"""
        pass
    
    def fuse_poses(self, poses: List[Dict]) -> Dict:
        """여러 포즈를 융합"""
        if not poses:
            return {
                'position': [0, 0, 0],
                'orientation': [0, 0, 0, 1],
                'confidence': 0.0
            }
            
        if len(poses) == 1:
            return poses[0].copy()
            
        try:
            # 가중치 (신뢰도 기반)
            weights = [pose.get('confidence', 1.0) for pose in poses]
            total_weight = sum(weights)
            
            if total_weight == 0:
                weights = [1.0] * len(poses)
                total_weight = len(poses)
            
            # 위치 융합 (가중 평균)
            positions = np.array([pose['position'] for pose in poses])
            weights_array = np.array(weights).reshape(-1, 1)
            fused_position = np.sum(positions * weights_array, axis=0) / total_weight
            
            # 회전 융합 (단순화된 평균)
            quaternions = [pose['orientation'] for pose in poses]
            rotations = [R.from_quat(q) for q in quaternions]
            
            # 첫 번째 회전을 기준으로 평균
            base_rotation = rotations[0]
            fused_rotation = base_rotation
            
            # 신뢰도 융합
            fused_confidence = np.mean([pose.get('confidence', 0.5) for pose in poses])
            
            return {
                'position': fused_position.tolist(),
                'orientation': fused_rotation.as_quat().tolist(),
                'confidence': float(fused_confidence)
            }
            
        except Exception:
            return poses[0].copy() if poses else {
                'position': [0, 0, 0],
                'orientation': [0, 0, 0, 1],
                'confidence': 0.0
            }
    
    def check_convergence(self, poses: List[Dict], threshold: float = 0.01) -> bool:
        """포즈 시퀀스의 수렴성 확인"""
        if len(poses) < 2:
            return False
            
        try:
            # 마지막 두 포즈 간의 변화량 확인
            last_pos = np.array(poses[-1]['position'])
            second_last_pos = np.array(poses[-2]['position'])
            
            position_change = np.linalg.norm(last_pos - second_last_pos)
            
            return position_change < threshold
            
        except Exception:
            return False