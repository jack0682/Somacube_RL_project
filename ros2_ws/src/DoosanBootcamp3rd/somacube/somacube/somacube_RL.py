import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import random
from collections import deque, namedtuple
import pickle
import os
import glob
from datetime import datetime
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.colors as mcolors
from matplotlib.patches import Rectangle
import time
from scipy.spatial.transform import Rotation as R
import numpy as np

# ===== 기본 정의 =====
BASE_PIECES = {
    0: np.array([[0,0,0], [1,0,0], [0,1,0]]), # V 조각
    1: np.array([[0,0,0], [1,0,0], [2,0,0], [2,1,0]]), # L 조각
    2: np.array([[0,0,0], [1,0,0], [2,0,0], [1,1,0]]), # T 조각
    3: np.array([[0,0,0], [1,0,0], [1,1,0], [2,1,0]]), # Z 조각
    4: np.array([[0,0,0], [0,1,0], [1,1,0], [1,1,1]]), # A 조각
    5: np.array([[0,0,0], [1,0,0], [1,1,0], [1,1,1]]), # B 조각
    6: np.array([[0,0,0], [1,0,0], [0,1,0], [0,0,1]]), # P 조각
}

PIECE_NAMES = {0: "V", 1: "L", 2: "T", 3: "Z", 4: "A", 5: "B", 6: "P"}

PIECE_COLORS = {
    0: '#FF6B6B',  # V - 빨강
    1: '#4ECDC4',  # L - 청록
    2: '#45B7D1',  # T - 파랑
    3: '#FFA07A',  # Z - 연어색
    4: '#98D8C8',  # A - 민트
    5: '#F7DC6F',  # B - 노랑
    6: '#BB8FCE',  # P - 보라
}

# ===== 회전 시스템 =====
def get_all_rotations_with_matrices():
    """회전 행렬 정보도 함께 저장하는 회전 계산 함수"""
    all_rotations = {}
    rotation_matrices_info = {}
    
    rotation_matrices = []
    matrix_descriptions = []
    
    # X, Y, Z 축 각각에 대해 0, 90, 180, 270도 회전
    for axis in ['x', 'y', 'z']:
        for angle in [0, 90, 180, 270]:
            if axis == 'x':
                if angle == 0:
                    rot = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]])
                    desc = "identity"
                elif angle == 90:
                    rot = np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0]])
                    desc = "x90"
                elif angle == 180:
                    rot = np.array([[1, 0, 0], [0, -1, 0], [0, 0, -1]])
                    desc = "x180"
                else:  # 270
                    rot = np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]])
                    desc = "x270"
            elif axis == 'y':
                if angle == 0:
                    rot = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]])
                    desc = "identity"
                elif angle == 90:
                    rot = np.array([[0, 0, 1], [0, 1, 0], [-1, 0, 0]])
                    desc = "y90"
                elif angle == 180:
                    rot = np.array([[-1, 0, 0], [0, 1, 0], [0, 0, -1]])
                    desc = "y180"
                else:  # 270
                    rot = np.array([[0, 0, -1], [0, 1, 0], [1, 0, 0]])
                    desc = "y270"
            else:  # z
                if angle == 0:
                    rot = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]])
                    desc = "identity"
                elif angle == 90:
                    rot = np.array([[0, -1, 0], [1, 0, 0], [0, 0, 1]])
                    desc = "z90"
                elif angle == 180:
                    rot = np.array([[-1, 0, 0], [0, -1, 0], [0, 0, 1]])
                    desc = "z180"
                else:  # 270
                    rot = np.array([[0, 1, 0], [-1, 0, 0], [0, 0, 1]])
                    desc = "z270"
            
            if desc != "identity" or len(rotation_matrices) == 0:
                rotation_matrices.append(rot)
                matrix_descriptions.append(desc)
    
    # 추가적인 회전들
    additional_rotations = [
        (np.array([[0, 0, 1], [1, 0, 0], [0, 1, 0]]), "x90_z90"),
        (np.array([[0, 0, 1], [-1, 0, 0], [0, -1, 0]]), "x90_z270"),
        (np.array([[0, 0, -1], [1, 0, 0], [0, -1, 0]]), "x270_z90"),
        (np.array([[0, 0, -1], [-1, 0, 0], [0, 1, 0]]), "x270_z270"),
        (np.array([[0, 1, 0], [0, 0, 1], [1, 0, 0]]), "y90_x90"),
        (np.array([[0, -1, 0], [0, 0, -1], [1, 0, 0]]), "y90_x270"),
        (np.array([[0, 1, 0], [0, 0, -1], [-1, 0, 0]]), "y270_x90"),
        (np.array([[0, -1, 0], [0, 0, 1], [-1, 0, 0]]), "y270_x270"),
    ]
    
    for rot, desc in additional_rotations:
        rotation_matrices.append(rot)
        matrix_descriptions.append(desc)
    
    # 각 조각별로 회전 계산
    for piece_id, piece in BASE_PIECES.items():
        seen_signatures = set()
        unique_orientations = []
        used_matrices = []
        used_descriptions = []
        
        for i, rot_matrix in enumerate(rotation_matrices):
            new_p = np.dot(piece, rot_matrix)
            new_p_normalized = new_p - new_p.min(axis=0)
            coords_set = frozenset(tuple(coord) for coord in new_p_normalized)
            
            if coords_set not in seen_signatures:
                seen_signatures.add(coords_set)
                p_final = np.round(new_p_normalized).astype(int)
                unique_orientations.append(p_final)
                used_matrices.append(rot_matrix)
                used_descriptions.append(matrix_descriptions[i])
        
        all_rotations[piece_id] = unique_orientations
        rotation_matrices_info[piece_id] = {
            'matrices': used_matrices,
            'descriptions': used_descriptions
        }
    
    return all_rotations, rotation_matrices_info

def get_zyz_angles(piece_id, orientation_index):
    """회전 인덱스를 ZYZ 오일러 각으로 변환"""
    if piece_id not in ROTATION_MATRICES_INFO:
        return [0, 0, 0], "error"
    
    matrices_info = ROTATION_MATRICES_INFO[piece_id]
    if orientation_index >= len(matrices_info['matrices']):
        return [0, 0, 0], "error"
    
    rotation_matrix = matrices_info['matrices'][orientation_index]
    description = matrices_info['descriptions'][orientation_index]
    
    try:
        U, s, Vt = np.linalg.svd(rotation_matrix)
        corrected_matrix = U @ Vt
        
        if np.linalg.det(corrected_matrix) < 0:
            Vt[-1, :] *= -1
            corrected_matrix = U @ Vt
        
        r = R.from_matrix(corrected_matrix)
        zyz_angles = r.as_euler('ZYZ', degrees=True)
        
        return zyz_angles.tolist(), description
        
    except Exception as e:
        print(f"ZYZ 변환 오류 (piece {piece_id}, index {orientation_index}): {e}")
        return [0, 0, 0], "error"

# 전역 변수로 회전 정보 초기화
ALL_PIECE_ORIENTATIONS, ROTATION_MATRICES_INFO = get_all_rotations_with_matrices()

# ===== 시각화 클래스 =====
class SomaCubeVisualizer:
    def __init__(self, grid_shape=(3, 3, 3)):
        self.grid_shape = grid_shape
        self.grid = np.zeros(grid_shape, dtype=int)
        self.placement_history = []
        plt.ion()
        self.fig = plt.figure(figsize=(15, 10))
        
    def clear_grid(self):
        self.grid = np.zeros(self.grid_shape, dtype=int)
        self.placement_history = []
    
    def place_piece(self, piece_coords, position, piece_id):
        """조각 배치 (position은 시각적 원점)"""
        for x, y, z in piece_coords:
            abs_x, abs_y, abs_z = position[0] + x, position[1] + y, position[2] + z
            if 0 <= abs_x < 3 and 0 <= abs_y < 3 and 0 <= abs_z < 3:
                self.grid[abs_x, abs_y, abs_z] = piece_id + 1
        
        self.placement_history.append({
            'piece_id': piece_id,
            'piece_name': PIECE_NAMES[piece_id],
            'visual_position': position,  # 시각적 원점 저장
            'coords': piece_coords
        })
    
    def draw_step_info(self):
        ax = self.fig.add_subplot(223)
        ax.clear()
        ax.axis('off')
        
        info_text = "=== 배치 과정 (시각적 좌표) ===\n\n"
        
        for i, step in enumerate(self.placement_history):
            piece_name = step['piece_name']
            visual_position = step['visual_position']
            coords = step['coords']
            
            # 실제 점유 위치 계산
            actual_positions = []
            for x, y, z in coords:
                abs_x, abs_y, abs_z = visual_position[0] + x, visual_position[1] + y, visual_position[2] + z
                if 0 <= abs_x < 3 and 0 <= abs_y < 3 and 0 <= abs_z < 3:
                    actual_positions.append((abs_x, abs_y, abs_z))
            
            info_text += f"단계 {i + 1}: {piece_name} 조각\n"
            info_text += f"  시각적 원점: {visual_position}\n"
            info_text += f"  점유 위치: {actual_positions}\n"
            
            # 높이 정보 추가
            if actual_positions:
                min_z = min(pos[2] for pos in actual_positions)
                max_z = max(pos[2] for pos in actual_positions)
                if max_z - min_z > 0:
                    info_text += f"  높이: {min_z}~{max_z}층 (세로배치)\n"
                else:
                    info_text += f"  높이: {min_z}층 (평면배치)\n"
            
            info_text += "\n"
        
        if not self.placement_history:
            info_text += "아직 배치된 조각이 없습니다."
        
        ax.text(0.05, 0.95, info_text, transform=ax.transAxes, fontsize=9,
                verticalalignment='top', fontfamily='monospace')
    
    # 나머지 메서드들은 기존과 동일...
    def draw_3d_view(self, title="Soma Cube 3D View", show_grid=True):
        ax = self.fig.add_subplot(221, projection='3d')
        ax.clear()
        
        for piece_id in range(7):
            if np.any(self.grid == piece_id + 1):
                positions = np.where(self.grid == piece_id + 1)
                x, y, z = positions
                
                color = PIECE_COLORS[piece_id]
                ax.scatter(x, y, z, c=color, s=500, alpha=0.8, 
                          marker='s', edgecolors='black', linewidth=2,
                          label=f'{PIECE_NAMES[piece_id]} 조각')
        
        ax.set_xlim(-0.5, 2.5)
        ax.set_ylim(-0.5, 2.5)
        ax.set_zlim(-0.5, 2.5)
        
        if show_grid:
            for i in range(4):
                ax.plot([i-0.5, i-0.5], [-0.5, 2.5], [-0.5, -0.5], 'k-', alpha=0.3)
                ax.plot([i-0.5, i-0.5], [-0.5, -0.5], [-0.5, 2.5], 'k-', alpha=0.3)
                ax.plot([-0.5, 2.5], [i-0.5, i-0.5], [-0.5, -0.5], 'k-', alpha=0.3)
                ax.plot([-0.5, -0.5], [i-0.5, i-0.5], [-0.5, 2.5], 'k-', alpha=0.3)
                ax.plot([-0.5, 2.5], [i-0.5, i-0.5], [2.5, 2.5], 'k-', alpha=0.3)
                ax.plot([2.5, 2.5], [i-0.5, i-0.5], [-0.5, 2.5], 'k-', alpha=0.3)
                ax.plot([-0.5, 2.5], [-0.5, -0.5], [i-0.5, i-0.5], 'k-', alpha=0.3)
                ax.plot([-0.5, 2.5], [2.5, 2.5], [i-0.5, i-0.5], 'k-', alpha=0.3)
                ax.plot([-0.5, -0.5], [-0.5, 2.5], [i-0.5, i-0.5], 'k-', alpha=0.3)
                ax.plot([2.5, 2.5], [-0.5, 2.5], [i-0.5, i-0.5], 'k-', alpha=0.3)
        
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z')
        ax.set_title(title)
        
        if len(self.placement_history) > 0:
            ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    
    def draw_layer_views(self):
        for z in range(3):
            ax = self.fig.add_subplot(2, 3, z + 4)
            ax.clear()
            
            layer = self.grid[:, :, z]
            
            for i in range(4):
                ax.axhline(i - 0.5, color='lightgray', linewidth=0.5)
                ax.axvline(i - 0.5, color='lightgray', linewidth=0.5)
            
            for x in range(3):
                for y in range(3):
                    if layer[x, y] > 0:
                        piece_id = layer[x, y] - 1
                        color = PIECE_COLORS[piece_id]
                        
                        rect = Rectangle((x - 0.4, y - 0.4), 0.8, 0.8, 
                                       facecolor=color, edgecolor='black', 
                                       linewidth=2, alpha=0.8)
                        ax.add_patch(rect)
                        
                        ax.text(x, y, PIECE_NAMES[piece_id], 
                               ha='center', va='center', fontsize=12, fontweight='bold')
            
            ax.set_xlim(-0.5, 2.5)
            ax.set_ylim(-0.5, 2.5)
            ax.set_aspect('equal')
            ax.set_title(f'Z = {z} 층 ({"바닥" if z == 0 else "중간" if z == 1 else "최상"}층)')
            ax.set_xlabel('X')
            ax.set_ylabel('Y')
            ax.set_xticks([0, 1, 2])
            ax.set_yticks([0, 1, 2])
    
    def update_display(self, title="Soma Cube Visualization"):
        self.fig.clear()
        self.draw_3d_view(title)
        self.draw_layer_views()
        self.draw_step_info()
        plt.tight_layout()
        plt.draw()
        plt.pause(0.1)


# ===== 개선된 로봇 접근성 고려 환경 =====
class RobotAccessibleSomaCubeEnv:
    def __init__(self, max_pieces=2, grid_shape=(3, 3, 3)):
        self.grid_shape = grid_shape
        self.max_pieces = max_pieces
        self.reset()
    
    def reset(self):
        self.grid = np.zeros(self.grid_shape, dtype=int)
        all_pieces = list(range(7))
        self.pieces_to_place = random.sample(all_pieces, self.max_pieces)
        self.current_piece_idx = 0
        self.placed_pieces = []
        self.done = False
        self.last_max_z = -1
        self.ground_level_count = 0  # 바닥층에 배치된 조각 수
        return self._get_state()
    
    def _get_state(self):
        state = np.zeros(27 + 7 + 1 + 1)
        state[:27] = self.grid.flatten()
        
        if self.current_piece_idx < len(self.pieces_to_place):
            current_piece = self.pieces_to_place[self.current_piece_idx]
            state[27 + current_piece] = 1
        
        state[34] = len(self.placed_pieces) / self.max_pieces
        state[35] = self.current_piece_idx / self.max_pieces
        
        return state
    

    def _calculate_visual_origin(self, piece_coords, position):
        """수정된 시각적 원점 계산"""
        
        print(f"🔍 시각적 원점 계산 디버그:")
        print(f"  piece_coords: {piece_coords.tolist() if hasattr(piece_coords, 'tolist') else piece_coords}")
        print(f"  position: {position}")
        
        # 모든 실제 점유 위치 계산
        actual_positions = []
        for i, (x, y, z) in enumerate(piece_coords):
            abs_x, abs_y, abs_z = position[0] + x, position[1] + y, position[2] + z
            if 0 <= abs_x < 3 and 0 <= abs_y < 3 and 0 <= abs_z < 3:
                actual_positions.append((abs_x, abs_y, abs_z, i))  # 인덱스도 저장
        
        print(f"  실제 점유 위치들: {[(pos[0], pos[1], pos[2]) for pos in actual_positions]}")
        
        # 원점 블록 [0,0,0] 찾기
        origin_block_actual = None
        for i, (x, y, z) in enumerate(piece_coords):
            if x == 0 and y == 0 and z == 0:
                origin_actual = (position[0] + x, position[1] + y, position[2] + z)
                if 0 <= origin_actual[0] < 3 and 0 <= origin_actual[1] < 3 and 0 <= origin_actual[2] < 3:
                    origin_block_actual = origin_actual
                    print(f"  원점 블록 [0,0,0] → 실제 위치: {origin_actual}")
                break
        
        if origin_block_actual:
            print(f"  ✅ 시각적 원점: {origin_block_actual}")
            return origin_block_actual
        else:
            # fallback: 최소 좌표
            if actual_positions:
                min_x = min(pos[0] for pos in actual_positions)
                min_y = min(pos[1] for pos in actual_positions) 
                min_z = min(pos[2] for pos in actual_positions)
                fallback_origin = (min_x, min_y, min_z)
                print(f"  ⚠️ 원점 블록 없음, fallback 시각적 원점: {fallback_origin}")
                return fallback_origin
            else:
                print(f"  ❌ fallback to position: {position}")
                return position
    
    def _has_clear_vertical_path(self, piece_coords, position):
        """로봇이 위에서 수직으로 내려와서 조각을 배치할 수 있는지 확인"""
        for x, y, z in piece_coords:
            abs_x, abs_y, abs_z = position[0] + x, position[1] + y, position[2] + z
            
            if not (0 <= abs_x < 3 and 0 <= abs_y < 3 and 0 <= abs_z < 3):
                continue
            
            # 해당 위치 위쪽 모든 레벨이 비어있어야 함
            for check_z in range(abs_z + 1, 3):
                if self.grid[abs_x, abs_y, check_z] != 0:
                    return False
        
        return True
    
    def _is_valid_placement(self, piece_coords, position):
        for x, y, z in piece_coords:
            abs_x, abs_y, abs_z = position[0] + x, position[1] + y, position[2] + z
            
            if not (0 <= abs_x < 3 and 0 <= abs_y < 3 and 0 <= abs_z < 3):
                return False
            
            if self.grid[abs_x, abs_y, abs_z] != 0:
                return False
        
        return True
    
    def _is_supported_and_robot_accessible(self, piece_coords, position):
        """조각이 물리적으로 지지되고 로봇이 접근 가능한지 확인"""
        
        # 바닥층에 있으면 항상 지지됨
        min_z = min(position[2] + z for x, y, z in piece_coords)
        if min_z == 0:
            return True
        
        # 공중에 있는 경우, 모든 블록이 아래쪽에 지지체가 있어야 함
        supported_blocks = 0
        total_blocks = len(piece_coords)
        
        for x, y, z in piece_coords:
            abs_x, abs_y, abs_z = position[0] + x, position[1] + y, position[2] + z
            
            # 격자 범위 확인
            if not (0 <= abs_x < 3 and 0 <= abs_y < 3 and 0 <= abs_z < 3):
                continue
                
            # 바닥층이 아니면 바로 아래에 지지체가 있어야 함
            if abs_z > 0:
                if self.grid[abs_x, abs_y, abs_z - 1] != 0:
                    supported_blocks += 1
        
        # 모든 블록이 지지되어야 함 (바닥층 제외)
        non_ground_blocks = sum(1 for x, y, z in piece_coords 
                               if position[2] + z > 0)
        
        return supported_blocks >= non_ground_blocks
    
    def _calculate_robot_friendly_reward(self, piece_coords, position, visual_origin):
        """로봇 친화적 보상 계산 (시각적 원점 기준)"""
        reward = 10.0  # 기본 보상
        
        # 바닥층 강력한 보너스
        min_z = min(position[2] + z for x, y, z in piece_coords)
        max_z = max(position[2] + z for x, y, z in piece_coords)
        
        if min_z == 0:
            reward += 30.0  # 바닥층 보너스
            
            # 바닥층을 먼저 채우는 것에 대한 추가 보너스
            if self.ground_level_count < 3:  # 바닥층 3개 블록을 먼저 채우도록
                reward += 20.0
        else:
            # 공중 배치에 대한 강한 페널티
            reward -= min_z * 25.0
        
        # 수직 경로 확보 보너스
        if self._has_clear_vertical_path(piece_coords, position):
            reward += 8.0
        else:
            reward -= 30.0  # 접근 불가 시 매우 강한 페널티
        
        # 높이별 페널티 강화
        reward -= max_z * 8.0
        
        # 배치 순서 보너스 (낮은 층부터)
        if len(self.placed_pieces) > 0:
            prev_max_heights = []
            for piece_id, orient_idx, prev_pos in self.placed_pieces:
                prev_coords = ALL_PIECE_ORIENTATIONS[piece_id][orient_idx]
                prev_max_z = max(prev_pos[2] + z for x, y, z in prev_coords)
                prev_max_heights.append(prev_max_z)
            
            avg_prev_height = sum(prev_max_heights) / len(prev_max_heights)
            
            if max_z <= avg_prev_height + 0.5:  # 비슷한 높이 또는 더 낮게
                reward += 15.0
            else:
                reward -= 15.0
        
        # 연속된 바닥층 배치 대형 보너스
        if min_z == 0:
            self.ground_level_count += sum(1 for x, y, z in piece_coords if position[2] + z == 0)
            if self.ground_level_count <= 6:  # 바닥층 우선 정책
                reward += 25.0
        
        # 인접성 보너스 (연결된 구조 장려)
        adjacent_count = 0
        for x, y, z in piece_coords:
            abs_x, abs_y, abs_z = position[0] + x, position[1] + y, position[2] + z
            
            for dx, dy, dz in [(-1,0,0), (1,0,0), (0,-1,0), (0,1,0), (0,0,-1), (0,0,1)]:
                nx, ny, nz = abs_x + dx, abs_y + dy, abs_z + dz
                if (0 <= nx < 3 and 0 <= ny < 3 and 0 <= nz < 3 and 
                    self.grid[nx, ny, nz] != 0):
                    adjacent_count += 1
        
        reward += adjacent_count * 2.0
        
        # 좌표 일관성 보너스 (시각적 원점이 명확할 때)
        if visual_origin == position:
            reward += 5.0  # 좌표가 일치하면 보너스
        
        return reward
    
    def get_possible_actions(self):
        """가능한 행동 목록 (바닥층 우선 정렬, 시각적 원점 기준)"""
        if self.current_piece_idx >= len(self.pieces_to_place):
            return []
        
        possible_actions = []
        piece_id = self.pieces_to_place[self.current_piece_idx]
        orientations = ALL_PIECE_ORIENTATIONS[piece_id]
        
        for orient_idx, piece_coords in enumerate(orientations):
            for z in range(3):  # Z 순서로 먼저 반복 (바닥층 우선)
                for x in range(3):
                    for y in range(3):
                        position = (x, y, z)
                        
                        if (self._is_valid_placement(piece_coords, position) and 
                            self._is_supported_and_robot_accessible(piece_coords, position) and
                            self._has_clear_vertical_path(piece_coords, position)):
                            
                            # 시각적 원점 계산
                            visual_origin = self._calculate_visual_origin(piece_coords, position)
                            action = (piece_id, orient_idx, position, visual_origin)
                            possible_actions.append(action)
        
        # 바닥층 우선으로 정렬 (시각적 원점 기준)
        def sort_key(action):
            piece_id, orient_idx, position, visual_origin = action
            piece_coords = orientations[orient_idx]
            min_z = min(position[2] + z for x, y, z in piece_coords)
            avg_z = sum(position[2] + z for x, y, z in piece_coords) / len(piece_coords)
            
            # 바닥층 블록의 개수
            ground_blocks = sum(1 for x, y, z in piece_coords if position[2] + z == 0)
            
            return (min_z, -ground_blocks, avg_z, visual_origin[2], visual_origin[0], visual_origin[1])
        
        possible_actions.sort(key=sort_key)
        return possible_actions
    
    def step(self, action):
        if self.current_piece_idx >= len(self.pieces_to_place):
            return self._get_state(), -10.0, True, {"error": "No more pieces"}
        
        # action이 4개 요소를 가진 경우 (visual_origin 포함)
        if len(action) == 4:
            piece_id, orient_idx, position, visual_origin = action
        else:
            # 기존 3개 요소 action의 경우 visual_origin 계산
            piece_id, orient_idx, position = action
            piece_coords = ALL_PIECE_ORIENTATIONS[piece_id][orient_idx]
            visual_origin = self._calculate_visual_origin(piece_coords, position)
            action = (piece_id, orient_idx, position, visual_origin)
        
        expected_piece = self.pieces_to_place[self.current_piece_idx]
        
        if piece_id != expected_piece:
            return self._get_state(), -10.0, True, {"error": "Wrong piece"}
        
        piece_coords = ALL_PIECE_ORIENTATIONS[piece_id][orient_idx]
        
        # 로봇 접근성 포함 유효성 검사
        if not (self._is_valid_placement(piece_coords, position) and 
                self._is_supported_and_robot_accessible(piece_coords, position) and
                self._has_clear_vertical_path(piece_coords, position)):
            return self._get_state(), -20.0, True, {"error": "Invalid placement or blocked path"}
        
        # ===== 수정: 시각적 원점 기준으로 조각 배치 =====
        for x, y, z in piece_coords:
            abs_x, abs_y, abs_z = position[0] + x, position[1] + y, position[2] + z
            if 0 <= abs_x < 3 and 0 <= abs_y < 3 and 0 <= abs_z < 3:
                self.grid[abs_x, abs_y, abs_z] = piece_id + 1
        
        # 기록할 때는 시각적 원점 사용
        self.placed_pieces.append((piece_id, orient_idx, visual_origin))
        self.current_piece_idx += 1
        
        # 보상 계산 (시각적 원점 전달)
        reward = self._calculate_robot_friendly_reward(piece_coords, position, visual_origin)
        
        # 높이 정보 업데이트
        max_z = max(position[2] + z for x, y, z in piece_coords)
        self.last_max_z = max(self.last_max_z, max_z)
        
        # 완료 확인
        if self.current_piece_idx >= len(self.pieces_to_place):
            reward += 100.0  # 완료 보너스 증가
            
            filled_positions = np.sum(self.grid > 0)
            target_positions = sum(len(BASE_PIECES[p]) for p in self.pieces_to_place)
            if filled_positions == target_positions:
                reward += 50.0  # 정확한 배치 보너스
            
            # 바닥층 우선 배치 완료 보너스
            ground_level_filled = np.sum(self.grid[:, :, 0] > 0)
            if ground_level_filled >= min(9, target_positions):  # 가능한 많이 바닥층에
                reward += 30.0
            
            self.done = True
            return self._get_state(), reward, True, {"success": True, "visual_origin": visual_origin}
        
        return self._get_state(), reward, False, {"visual_origin": visual_origin}

# ===== DQN 모델 =====
class HierarchicalDQN(nn.Module):
    def __init__(self, state_size, max_orientations=30, max_positions=27):
        super(HierarchicalDQN, self).__init__()
        
        self.feature_network = nn.Sequential(
            nn.Linear(state_size, 512),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(256, 128),
            nn.ReLU()
        )
        
        self.orientation_network = nn.Sequential(
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, max_orientations)
        )
        
        self.position_network = nn.Sequential(
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, max_positions)
        )
    
    def forward(self, x):
        features = self.feature_network(x)
        orientation_q = self.orientation_network(features)
        position_q = self.position_network(features)
        return orientation_q, position_q

class ActionMapper:
    def __init__(self):
        self.piece_orientations = {}
        for piece_id in range(7):
            self.piece_orientations[piece_id] = len(ALL_PIECE_ORIENTATIONS[piece_id])
    
    def get_valid_actions_for_piece(self, piece_id, env):
        valid_actions = []
        orientations = ALL_PIECE_ORIENTATIONS[piece_id]
        
        for orient_idx, piece_coords in enumerate(orientations):
            for x in range(3):
                for y in range(3):
                    for z in range(3):
                        position = (x, y, z)
                        
                        if (env._is_valid_placement(piece_coords, position) and 
                            env._is_supported_and_robot_accessible(piece_coords, position) and
                            env._has_clear_vertical_path(piece_coords, position)):
                            valid_actions.append((orient_idx, x * 9 + y * 3 + z))
        
        return valid_actions

# ===== 개선된 트레이너 클래스 =====
class RobotFriendlyTrainer:
    def __init__(self, device='cuda' if torch.cuda.is_available() else 'cpu'):
        self.device = device
        self.action_mapper = ActionMapper()
        
        self.models = {}
        self.target_models = {}
        self.optimizers = {}
        self.replay_buffers = {}
        
        self.learning_rate = 0.0005  # 학습률 약간 낮춤
        self.gamma = 0.99
        self.epsilon_start = 1.0
        self.epsilon_end = 0.01
        self.epsilon_decay = 0.995
        self.batch_size = 32
        self.target_update = 100
        self.memory_size = 10000
        
        self.training_stats = {}
    
    def initialize_level(self, level):
        state_size = 36
        
        model = HierarchicalDQN(state_size).to(self.device)
        target_model = HierarchicalDQN(state_size).to(self.device)
        target_model.load_state_dict(model.state_dict())
        
        optimizer = optim.Adam(model.parameters(), lr=self.learning_rate)
        replay_buffer = deque(maxlen=self.memory_size)
        
        self.models[level] = model
        self.target_models[level] = target_model
        self.optimizers[level] = optimizer
        self.replay_buffers[level] = replay_buffer
        
        self.training_stats[level] = {
            'episode_rewards': [],
            'episode_lengths': [],
            'success_rate': [],
            'epsilon_history': [],
            'robot_friendly_actions': [],
            'ground_level_priority': []
        }
    
    def find_latest_model(self, level, model_dir="models"):
        # 로봇 친화적 모델 우선 검색
        pattern = f"{model_dir}/**/robot_friendly_soma_level_{level}_*.pth"
        model_files = glob.glob(pattern, recursive=True)
        
        if not model_files:
            # 일반 모델 검색
            pattern = f"{model_dir}/**/hierarchical_soma_level_{level}_*.pth"
            model_files = glob.glob(pattern, recursive=True)
        
        if not model_files:
            print(f"⚠️ 레벨 {level} 모델을 찾을 수 없습니다.")
            return None
        
        latest_model = max(model_files, key=os.path.getctime)
        print(f"✅ 발견된 레벨 {level} 모델: {latest_model}")
        return latest_model
    
    def transfer_learning(self, from_level, to_level, episodes=1000):
        print(f"\n=== 🎯 로봇 친화적 전이학습: 레벨 {from_level} → 레벨 {to_level} ===")
        
        # 이전 레벨 모델 로딩
        if from_level not in self.models:
            model_path = self.find_latest_model(from_level)
            if model_path is None:
                print(f"❌ 레벨 {from_level} 모델이 없습니다. 먼저 학습하세요.")
                return False
            
            self.load_model(from_level, model_path)
            print(f"✅ 레벨 {from_level} 모델 로딩 완료")
        
        # 새로운 레벨 초기화
        self.initialize_level(to_level)
        
        # 특징 추출 네트워크 가중치 복사
        print(f"🔄 레벨 {from_level}의 특징 추출 네트워크를 레벨 {to_level}에 복사")
        
        prev_feature_state = self.models[from_level].feature_network.state_dict()
        self.models[to_level].feature_network.load_state_dict(prev_feature_state)
        self.target_models[to_level].feature_network.load_state_dict(prev_feature_state)
        
        print(f"📝 레벨 {to_level}의 출력 네트워크는 새로 초기화됨")
        
        # 학습 시작
        print(f"🎯 레벨 {to_level} 로봇 친화적 학습 시작 (에피소드: {episodes})")
        self.train_level(to_level, episodes)
        
        # 모델 저장
        save_dir = f"models/level_{to_level}_robot_friendly"
        self.save_models(save_dir)
        print(f"💾 로봇 친화적 전이학습 완료! 모델 저장: {save_dir}")
        
        return True
    
    def sequential_training(self, start_level=2, end_level=7, episodes_per_level=1000):
        print(f"\n=== 🚀 로봇 친화적 순차적 전이학습: 레벨 {start_level} → {end_level} ===")
        
        current_level = start_level
        
        # 첫 번째 레벨이 없으면 처음부터 학습
        if current_level not in self.models:
            model_path = self.find_latest_model(current_level)
            if model_path is None:
                print(f"⚠️ 레벨 {current_level} 모델이 없습니다. 처음부터 학습합니다.")
                self.train_level(current_level, episodes_per_level)
                self.save_models(f"models/level_{current_level}_robot_friendly")
            else:
                self.load_model(current_level, model_path)
        
        # 다음 레벨들을 순차적으로 학습
        for next_level in range(current_level + 1, end_level + 1):
            print(f"\n{'='*50}")
            print(f"레벨 {next_level} 로봇 친화적 전이학습 시작")
            print(f"{'='*50}")
            
            success = self.transfer_learning(current_level, next_level, episodes_per_level)
            if not success:
                print(f"❌ 레벨 {next_level} 전이학습 실패")
                break
            
            current_level = next_level
            print(f"✅ 레벨 {current_level} 완료!")
        
        print(f"🎉 로봇 친화적 순차적 학습 완료! (레벨 {start_level} → {current_level})")
    
    def select_action(self, state, level, piece_id, env, epsilon):
        if random.random() < epsilon:
            possible_actions = env.get_possible_actions()
            if not possible_actions:
                return None
            return random.choice(possible_actions)
        else:
            with torch.no_grad():
                state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
                orientation_q, position_q = self.models[level](state_tensor)
                
                possible_actions = env.get_possible_actions()
                if not possible_actions:
                    return None
                
                best_value = float('-inf')
                best_action = None
                
                for action in possible_actions:
                    piece_id, orient_idx, position, visual_origin = action
                    pos_idx = position[0] * 9 + position[1] * 3 + position[2]
                    
                    if orient_idx < orientation_q.shape[1] and pos_idx < position_q.shape[1]:
                        value = orientation_q[0][orient_idx].item() + position_q[0][pos_idx].item()
                        if value > best_value:
                            best_value = value
                            best_action = action
                
                return best_action
    
    def train_level(self, level, num_episodes=1000):
        print(f"\n=== 🤖 레벨 {level} 좌표 통일 로봇 친화적 학습 시작 (조각 {level}개) ===")
        
        if level not in self.models:
            self.initialize_level(level)
        
        # FixedRobotAccessibleSomaCubeEnv 사용
        env = RobotAccessibleSomaCubeEnv(max_pieces=level)
        model = self.models[level]
        target_model = self.target_models[level]
        optimizer = self.optimizers[level]
        replay_buffer = self.replay_buffers[level]
        
        epsilon = self.epsilon_start
        success_count = 0
        robot_friendly_count = 0
        ground_priority_count = 0
        coordinate_consistency_count = 0  # 새로운 메트릭
        
        for episode in range(num_episodes):
            state = env.reset()
            total_reward = 0
            steps = 0
            episode_robot_friendly = 0
            ground_level_actions = 0
            coordinate_consistent_actions = 0
            
            while not env.done and steps < 100:
                if env.current_piece_idx >= len(env.pieces_to_place):
                    break
                
                piece_id = env.pieces_to_place[env.current_piece_idx]
                
                # 로봇 접근 가능한 행동 개수 체크
                possible_actions = env.get_possible_actions()
                if len(possible_actions) > 0:
                    episode_robot_friendly += 1
                    
                    # 바닥층 우선 행동 체크
                    for action in possible_actions[:3]:  # 상위 3개 행동 확인
                        _, _, position, visual_origin = action
                        if position[2] == 0:  # 바닥층
                            ground_level_actions += 1
                            break
                        
                        # 좌표 일관성 체크
                        if position == visual_origin:
                            coordinate_consistent_actions += 1
                
                action = self.select_action(state, level, piece_id, env, epsilon)
                
                if action is None:
                    break
                
                next_state, reward, done, info = env.step(action)
                
                replay_buffer.append((state, action, reward, next_state, done))
                
                state = next_state
                total_reward += reward
                steps += 1
                
                if len(replay_buffer) >= self.batch_size:
                    self._train_step(level)
            
            if env.done and "success" in info:
                success_count += 1
            
            if episode_robot_friendly > 0:
                robot_friendly_count += 1
            
            if ground_level_actions > 0:
                ground_priority_count += 1
                
            if coordinate_consistent_actions > 0:
                coordinate_consistency_count += 1
            
            self.training_stats[level]['episode_rewards'].append(total_reward)
            self.training_stats[level]['episode_lengths'].append(steps)
            self.training_stats[level]['epsilon_history'].append(epsilon)
            self.training_stats[level]['robot_friendly_actions'].append(episode_robot_friendly / max(steps, 1))
            self.training_stats[level]['ground_level_priority'].append(ground_level_actions / max(steps, 1))
            
            if episode % self.target_update == 0:
                target_model.load_state_dict(model.state_dict())
            
            epsilon = max(self.epsilon_end, epsilon * self.epsilon_decay)
            
            if episode % 100 == 0:
                recent_success_rate = success_count / 100 if episode >= 100 else success_count / (episode + 1)
                robot_friendly_rate = robot_friendly_count / 100 if episode >= 100 else robot_friendly_count / (episode + 1)
                ground_priority_rate = ground_priority_count / 100 if episode >= 100 else ground_priority_count / (episode + 1)
                coordinate_rate = coordinate_consistency_count / 100 if episode >= 100 else coordinate_consistency_count / (episode + 1)
                
                self.training_stats[level]['success_rate'].append(recent_success_rate)
                
                avg_reward = np.mean(self.training_stats[level]['episode_rewards'][-100:])
                print(f"Episode {episode}, Avg Reward: {avg_reward:.2f}, "
                      f"Success Rate: {recent_success_rate:.2f}, "
                      f"Robot Friendly: {robot_friendly_rate:.2f}, "
                      f"Ground Priority: {ground_priority_rate:.2f}, "
                      f"Coordinate Consistency: {coordinate_rate:.2f}, "
                      f"Epsilon: {epsilon:.3f}")
                
                if episode >= 100:
                    success_count = 0
                    robot_friendly_count = 0
                    ground_priority_count = 0
                    coordinate_consistency_count = 0
        
        print(f"🤖 레벨 {level} 좌표 통일 로봇 친화적 학습 완료!")
    
    def _train_step(self, level):
        if len(self.replay_buffers[level]) < self.batch_size:
            return
        
        batch = random.sample(self.replay_buffers[level], self.batch_size)
        states, actions, rewards, next_states, dones = zip(*batch)
        
        states = torch.FloatTensor(states).to(self.device)
        rewards = torch.FloatTensor(rewards).to(self.device)
        next_states = torch.FloatTensor(next_states).to(self.device)
        dones = torch.BoolTensor(dones).to(self.device)
        
        orientation_q, position_q = self.models[level](states)
        
        with torch.no_grad():
            next_orientation_q, next_position_q = self.target_models[level](next_states)
            next_q_values = torch.max(next_orientation_q, dim=1)[0] + torch.max(next_position_q, dim=1)[0]
            target_q_values = rewards + (self.gamma * next_q_values * ~dones)
        
        action_orient_indices = []
        action_pos_indices = []
        
        for action in actions:
            piece_id, orient_idx, (x, y, z) = action
            pos_idx = x * 9 + y * 3 + z
            action_orient_indices.append(min(orient_idx, orientation_q.shape[1] - 1))
            action_pos_indices.append(min(pos_idx, position_q.shape[1] - 1))
        
        action_orient_indices = torch.LongTensor(action_orient_indices).to(self.device)
        action_pos_indices = torch.LongTensor(action_pos_indices).to(self.device)
        
        current_orientation_q = orientation_q.gather(1, action_orient_indices.unsqueeze(1)).squeeze()
        current_position_q = position_q.gather(1, action_pos_indices.unsqueeze(1)).squeeze()
        current_q_values = current_orientation_q + current_position_q
        
        loss = F.mse_loss(current_q_values, target_q_values)
        
        self.optimizers[level].zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.models[level].parameters(), 1.0)
        self.optimizers[level].step()
    
    def save_models(self, save_dir="models"):
        os.makedirs(save_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for level in self.models:
            model_path = os.path.join(save_dir, f"robot_friendly_soma_level_{level}_{timestamp}.pth")
            torch.save({
                'model_state_dict': self.models[level].state_dict(),
                'optimizer_state_dict': self.optimizers[level].state_dict(),
                'training_stats': self.training_stats[level],
                'level': level
            }, model_path)
            print(f"💾 레벨 {level} 로봇 친화적 모델 저장: {model_path}")
        
        stats_path = os.path.join(save_dir, f"robot_friendly_training_stats_{timestamp}.pkl")
        with open(stats_path, 'wb') as f:
            pickle.dump(self.training_stats, f)
        print(f"📊 로봇 친화적 훈련 통계 저장: {stats_path}")
    
    def load_model(self, level, model_path):
        if level not in self.models:
            self.initialize_level(level)
        
        checkpoint = torch.load(model_path, map_location=self.device)
        self.models[level].load_state_dict(checkpoint['model_state_dict'])
        self.optimizers[level].load_state_dict(checkpoint['optimizer_state_dict'])
        
        if 'training_stats' in checkpoint:
            self.training_stats[level] = checkpoint['training_stats']
        
        print(f"✅ 레벨 {level} 로봇 친화적 모델 로딩 완료: {model_path}")

# ===== 시각화 및 테스트 함수들 =====
def test_model_with_visualization(trainer, level, num_tests=1, show_rotation_details=True):
    print(f"\n=== 🤖 레벨 {level} 로봇 친화적 모델 테스트 ===")
    
    env = RobotAccessibleSomaCubeEnv(max_pieces=level)
    model = trainer.models[level]
    model.eval()
    
    visualizer = SomaCubeVisualizer()
    
    for test in range(num_tests):
        print(f"\n🧩 테스트 {test + 1} 시작")
        
        state = env.reset()
        visualizer.clear_grid()
        visualizer.update_display(f"테스트 {test + 1} - 시작 상태")
        
        total_reward = 0
        steps = 0
        actions_taken = []
        robot_accessibility_log = []
        ground_level_actions = []
        
        print(f"🎯 사용할 조각들: {[PIECE_NAMES[p] for p in env.pieces_to_place]}")
        input("▶️ 시작하려면 엔터를 누르세요...")
        
        while not env.done and steps < 100:
            if env.current_piece_idx >= len(env.pieces_to_place):
                break
            
            piece_id = env.pieces_to_place[env.current_piece_idx]
            
            # 로봇 접근 가능한 행동 수 확인
            possible_actions = env.get_possible_actions()
            robot_accessibility_log.append(len(possible_actions))
            
            # 바닥층 행동 확인
            ground_actions = [a for a in possible_actions if len(a) >= 4 and a[2][2] == 0]
            ground_level_actions.append(len(ground_actions))
            
            action = trainer.select_action(state, level, piece_id, env, epsilon=0.0)
            
            if action is None:
                print(f"  ❌ 단계 {steps + 1}: 로봇이 접근할 수 있는 행동이 없음")
                break
            
            # 행동 실행
            next_state, reward, done, info = env.step(action)
            actions_taken.append(action)
            
            # ===== 수정된 부분: visual_origin 사용 =====
            if len(action) >= 4:
                # 4개 요소 action: (piece_id, orient_idx, position, visual_origin)
                piece_id, orient_idx, position, visual_origin = action
            else:
                # 3개 요소 action: (piece_id, orient_idx, position)
                piece_id, orient_idx, position = action
                piece_coords = ALL_PIECE_ORIENTATIONS[piece_id][orient_idx]
                visual_origin = env._calculate_visual_origin(piece_coords, position)
            
            piece_coords = ALL_PIECE_ORIENTATIONS[piece_id][orient_idx]
            
            # ===== 중요: 시각화에 visual_origin 사용 =====
            visualizer.place_piece(piece_coords, visual_origin, piece_id)
            
            piece_name = PIECE_NAMES[piece_id]
            
            # ZYZ 회전 정보 계산
            if show_rotation_details:
                zyz_angles, rotation_desc = get_zyz_angles(piece_id, orient_idx)
                zyz_str = f"ZYZ({zyz_angles[0]:.1f}°, {zyz_angles[1]:.1f}°, {zyz_angles[2]:.1f}°)"
            
            title = f"단계 {steps + 1}: {piece_name} 조각 배치 (보상: {reward:.1f})"
            visualizer.update_display(title)
            
            # 실제 점유 위치 계산 (position 기준)
            actual_occupied_positions = []
            for x, y, z in piece_coords:
                abs_x, abs_y, abs_z = position[0] + x, position[1] + y, position[2] + z
                if 0 <= abs_x < 3 and 0 <= abs_y < 3 and 0 <= abs_z < 3:
                    actual_occupied_positions.append((abs_x, abs_y, abs_z))
            
            # 수직 접근 경로 확인
            has_clear_path = env._has_clear_vertical_path(piece_coords, position)
            path_status = "✅ 수직 경로 확보" if has_clear_path else "❌ 수직 경로 차단"
            
            # 바닥층 여부 확인
            min_z = min(position[2] + z for x, y, z in piece_coords)
            ground_status = "🏠 바닥층 배치" if min_z == 0 else f"🏢 {min_z}층 배치"
            
            # 좌표 일관성 확인
            coordinate_status = "✅ 좌표 일치" if position == visual_origin else "⚠️ 좌표 불일치"
            
            # ===== 개선된 출력 =====
            print(f"  🤖 단계 {steps + 1}: {piece_name} 조각 배치")
            print(f"      📍 알고리즘 기준점: {position}")
            print(f"      👁️ 시각적 원점: {visual_origin}")
            print(f"      🎯 실제 점유 위치: {actual_occupied_positions}")
            print(f"      💰 보상: {reward:.1f}")
            print(f"      🛣️ {path_status}")
            print(f"      {ground_status}")
            print(f"      📐 {coordinate_status}")
            print(f"      📊 가능한 행동 수: {len(possible_actions)}개 (바닥층: {len(ground_actions)}개)")
            
            if show_rotation_details:
                print(f"      🔄 회전 정보: {rotation_desc} → {zyz_str}")
                print(f"      🤖 로봇 명령: node.robot_control(input, {piece_id}, {zyz_angles}, {visual_origin})")
            
            # 좌표 불일치 상세 설명
            if position != visual_origin:
                print(f"      💡 설명: 알고리즘은 {position}을 기준으로 계산하지만")
                print(f"              시각화에서는 {visual_origin}에서 조각이 시작됩니다")
            
            state = next_state
            total_reward += reward
            steps += 1
            
            # 다음 단계로 넘어가기 전 대기
            if not done:
                input("▶️ 다음 단계를 보려면 엔터를 누르세요...")
        
        # 결과 표시
        if env.done and "success" in info:
            print(f"  🎉 성공! 총 보상: {total_reward:.1f}")
            visualizer.update_display(f"✅ 테스트 {test + 1} 성공! (보상: {total_reward:.1f})")
        else:
            print(f"  ❌ 실패 (총 보상: {total_reward:.1f})")
            visualizer.update_display(f"❌ 테스트 {test + 1} 실패 (보상: {total_reward:.1f})")
        
        # 로봇 접근성 통계
        avg_accessibility = np.mean(robot_accessibility_log) if robot_accessibility_log else 0
        avg_ground_actions = np.mean(ground_level_actions) if ground_level_actions else 0
        print(f"  📊 평균 로봇 접근 가능 행동 수: {avg_accessibility:.1f}개")
        print(f"  🏠 평균 바닥층 행동 수: {avg_ground_actions:.1f}개")
        
        # 바닥층 우선 배치 검증 (position 기준)
        ground_first_count = 0
        coordinate_consistent_count = 0
        for action in actions_taken:
            if len(action) >= 4:
                piece_id, orient_idx, position, visual_origin = action
                if position == visual_origin:
                    coordinate_consistent_count += 1
            else:
                piece_id, orient_idx, position = action
            
            piece_coords = ALL_PIECE_ORIENTATIONS[piece_id][orient_idx]
            min_z = min(position[2] + z for x, y, z in piece_coords)
            if min_z == 0:
                ground_first_count += 1
        
        ground_priority_rate = ground_first_count / len(actions_taken) if actions_taken else 0
        coordinate_consistency_rate = coordinate_consistent_count / len(actions_taken) if actions_taken else 0
        
        print(f"  🏠 바닥층 우선 배치율: {ground_priority_rate:.2%}")
        print(f"  📐 좌표 일관성율: {coordinate_consistency_rate:.2%}")
        
        # 전체 로봇 제어 명령 요약 (visual_origin 사용)
        if show_rotation_details and actions_taken:
            print(f"\n🤖 로봇 제어 스크립트:")
            print("="*60)
            for i, action in enumerate(actions_taken):
                if len(action) >= 4:
                    piece_id, orient_idx, position, visual_origin = action
                else:
                    piece_id, orient_idx, position = action
                    piece_coords = ALL_PIECE_ORIENTATIONS[piece_id][orient_idx]
                    visual_origin = env._calculate_visual_origin(piece_coords, position)
                
                piece_name = PIECE_NAMES[piece_id]
                zyz_angles, rotation_desc = get_zyz_angles(piece_id, orient_idx)
                piece_coords = ALL_PIECE_ORIENTATIONS[piece_id][orient_idx]
                min_z = min(position[2] + z for x, y, z in piece_coords)
                level_info = f"(바닥층)" if min_z == 0 else f"({min_z}층)"
                
                coord_info = f"알고리즘:{position}" if position != visual_origin else f"좌표:{visual_origin}"
                
                print(f"# 단계 {i+1}: {piece_name} 조각 {level_info} ({rotation_desc}) - {coord_info}")
                print(f"node.robot_control(user_input, {piece_id}, {zyz_angles}, {visual_origin})")
                print()
            print("="*60)
        
        if test < num_tests - 1:
            input("▶️ 다음 테스트를 시작하려면 엔터를 누르세요...")
    
    input("🏁 테스트 완료! 창을 닫으려면 엔터를 누르세요...")
    plt.close()

# ===== 메인 함수 =====
def main():
    print("=== 🤖 로봇 친화적 계층적 소마큐브 강화학습 시스템 ===")
    print("1. 특정 레벨 로봇 친화적 학습")
    print("2. 로봇 친화적 전이학습")
    print("3. 순차적 로봇 친화적 전이학습")
    print("4. 모델 테스트 (콘솔만)")
    print("5. 로봇 친화적 3D 시각화 테스트")
    print("6. 로봇 접근성 분석")
    print("7. 모델 로딩")
    print("8. 종료")
    
    trainer = RobotFriendlyTrainer()
    
    while True:
        try:
            choice = input("\n🎮 원하는 작업을 선택하세요 (1-8): ")
            
            if choice == "1":
                # 특정 레벨 로봇 친화적 학습
                level = int(input("📚 학습할 레벨을 입력하세요 (2-7): "))
                episodes = int(input("📊 에피소드 수를 입력하세요 (기본 1000): ") or "1000")
                trainer.train_level(level, episodes)
                trainer.save_models(f"models/level_{level}_robot_friendly")
                
            elif choice == "2":
                # 로봇 친화적 전이학습
                from_level = int(input("🎯 기반이 될 레벨을 입력하세요 (2-6): "))
                to_level = int(input("🚀 학습할 레벨을 입력하세요 (3-7): "))
                episodes = int(input("📊 에피소드 수 (기본 1000): ") or "1000")
                
                if to_level <= from_level:
                    print("❌ 학습할 레벨이 기반 레벨보다 커야 합니다.")
                else:
                    trainer.transfer_learning(from_level, to_level, episodes)
            
            elif choice == "3":
                # 순차적 로봇 친화적 전이학습
                start_level = int(input("🎯 시작 레벨 (기본 2): ") or "2")
                end_level = int(input("🏁 끝 레벨 (기본 7): ") or "7")
                episodes = int(input("📊 레벨당 에피소드 수 (기본 1000): ") or "1000")
                
                trainer.sequential_training(start_level, end_level, episodes)
                
            elif choice == "4":
                # 모델 테스트 (콘솔만)
                level = int(input("🧪 테스트할 레벨을 입력하세요 (2-7): "))
                
                if level in trainer.models:
                    num_tests = int(input("🔢 테스트 횟수 (기본 5): ") or "5")
                    
                    env = RobotAccessibleSomaCubeEnv(max_pieces=level)
                    model = trainer.models[level]
                    model.eval()
                    
                    success_count = 0
                    total_robot_actions = 0
                    total_ground_actions = 0
                    
                    for test in range(num_tests):
                        state = env.reset()
                        total_reward = 0
                        steps = 0
                        robot_accessible_actions = 0
                        ground_level_actions = 0
                        
                        print(f"\n🧩 테스트 {test + 1}: {[PIECE_NAMES[p] for p in env.pieces_to_place]}")
                        
                        while not env.done and steps < 100:
                            if env.current_piece_idx >= len(env.pieces_to_place):
                                break
                            
                            piece_id = env.pieces_to_place[env.current_piece_idx]
                            possible_actions = env.get_possible_actions()
                            robot_accessible_actions += len(possible_actions)
                            
                            # 바닥층 행동 수 계산
                            ground_actions = [a for a in possible_actions if a[2][2] == 0]
                            ground_level_actions += len(ground_actions)
                            
                            action = trainer.select_action(state, level, piece_id, env, epsilon=0.0)
                            
                            if action is None:
                                print(f"    ❌ 로봇 접근 불가")
                                break
                            
                            piece_name = PIECE_NAMES[piece_id]
                            orient_idx = action[1]
                            position = action[2]
                            
                            # ZYZ 회전 정보
                            zyz_angles, rotation_desc = get_zyz_angles(piece_id, orient_idx)
                            
                            # 바닥층 여부 확인
                            piece_coords = ALL_PIECE_ORIENTATIONS[piece_id][orient_idx]
                            min_z = min(position[2] + z for x, y, z in piece_coords)
                            level_info = "🏠바닥층" if min_z == 0 else f"🏢{min_z}층"
                            
                            print(f"  단계 {steps + 1}: {piece_name} 조각을 위치 {position}에 회전 {orient_idx}로 배치 {level_info}")
                            print(f"    🔄 회전: {rotation_desc} → ZYZ{zyz_angles}")
                            print(f"    🤖 가능한 행동: {len(possible_actions)}개 (바닥층: {len(ground_actions)}개)")
                            
                            next_state, reward, done, info = env.step(action)
                            state = next_state
                            total_reward += reward
                            steps += 1
                        
                        if env.done and "success" in info:
                            success_count += 1
                        
                        avg_robot_actions = robot_accessible_actions / max(steps, 1)
                        avg_ground_actions = ground_level_actions / max(steps, 1)
                        total_robot_actions += avg_robot_actions
                        total_ground_actions += avg_ground_actions
                        
                        result = "✅ 성공" if env.done and "success" in info else "❌ 실패"
                        print(f"  {result} (보상: {total_reward:.1f}, 평균 로봇 행동: {avg_robot_actions:.1f}, 평균 바닥층 행동: {avg_ground_actions:.1f})")
                    
                    print(f"\n📊 최종 결과:")
                    print(f"   성공률: {success_count}/{num_tests} ({success_count/num_tests:.2%})")
                    print(f"   평균 로봇 접근 가능 행동: {total_robot_actions/num_tests:.1f}개")
                    print(f"   평균 바닥층 행동: {total_ground_actions/num_tests:.1f}개")
                else:
                    print("❌ 해당 레벨의 모델이 없습니다. 먼저 학습하거나 모델을 로딩하세요.")
                
            elif choice == "5":
                # 로봇 친화적 3D 시각화 테스트
                level = int(input("🤖 시각화 테스트할 레벨을 입력하세요 (2-7): "))
                
                if level in trainer.models:
                    num_tests = int(input("🔢 테스트 횟수 (기본 1): ") or "1")
                    show_rotation = input("🔄 회전 정보 표시? (y/n, 기본 y): ").lower() != 'n'
                    test_model_with_visualization(trainer, level, num_tests, show_rotation)
                else:
                    print("❌ 해당 레벨의 모델이 없습니다.")
                
            elif choice == "6":
                # 로봇 접근성 분석
                level = int(input("🔍 분석할 레벨을 입력하세요 (2-7): "))
                
                env = RobotAccessibleSomaCubeEnv(max_pieces=level)
                state = env.reset()
                
                print(f"\n🤖 레벨 {level} 로봇 접근성 분석:")
                print(f"📦 사용할 조각들: {[PIECE_NAMES[p] for p in env.pieces_to_place]}")
                
                total_possible = 0
                total_robot_accessible = 0
                total_ground_level = 0
                
                for piece_idx, piece_id in enumerate(env.pieces_to_place):
                    orientations = ALL_PIECE_ORIENTATIONS[piece_id]
                    piece_possible = 0
                    piece_robot_accessible = 0
                    piece_ground_level = 0
                    
                    for orient_idx, piece_coords in enumerate(orientations):
                        for x in range(3):
                            for y in range(3):
                                for z in range(3):
                                    position = (x, y, z)
                                    
                                    # 기본 유효성
                                    if (env._is_valid_placement(piece_coords, position) and 
                                        env._is_supported_and_robot_accessible(piece_coords, position)):
                                        piece_possible += 1
                                        total_possible += 1
                                        
                                        # 로봇 접근성
                                        if env._has_clear_vertical_path(piece_coords, position):
                                            piece_robot_accessible += 1
                                            total_robot_accessible += 1
                                            
                                            # 바닥층 여부
                                            min_z = min(position[2] + pz for px, py, pz in piece_coords)
                                            if min_z == 0:
                                                piece_ground_level += 1
                                                total_ground_level += 1
                    
                    accessibility_rate = piece_robot_accessible / max(piece_possible, 1)
                    ground_rate = piece_ground_level / max(piece_robot_accessible, 1)
                    print(f"  {PIECE_NAMES[piece_id]} 조각: {piece_robot_accessible}/{piece_possible} ({accessibility_rate:.2%}) | 바닥층: {piece_ground_level}개 ({ground_rate:.2%})")
                
                overall_rate = total_robot_accessible / max(total_possible, 1)
                ground_overall_rate = total_ground_level / max(total_robot_accessible, 1)
                print(f"\n📊 전체 로봇 접근성: {total_robot_accessible}/{total_possible} ({overall_rate:.2%})")
                print(f"🏠 전체 바닥층 비율: {total_ground_level}/{total_robot_accessible} ({ground_overall_rate:.2%})")
                
            elif choice == "7":
                # 모델 로딩
                level = int(input("📂 로딩할 레벨을 입력하세요 (2-7): "))
                model_path = input("📁 모델 파일 경로 (엔터시 자동 검색): ")
                
                if not model_path:
                    model_path = trainer.find_latest_model(level)
                    if model_path is None:
                        continue
                
                trainer.load_model(level, model_path)
                print(f"✅ 레벨 {level} 모델 로딩 완료!")
                
            elif choice == "8":
                print("👋 프로그램을 종료합니다.")
                break
                
            else:
                print("❌ 1-8 사이의 숫자를 입력하세요.")
                
        except KeyboardInterrupt:
            print("\n⚠️ 프로그램 중단")
            break
        except ValueError:
            print("❌ 올바른 숫자를 입력하세요.")
        except Exception as e:
            print(f"💥 오류 발생: {e}")
            import traceback
            traceback.print_exc()

# ===== 추가 유틸리티 함수들 =====
def demonstrate_robot_constraints():
    """로봇 제약 조건 시연"""
    print("=== 🤖 로봇 제약 조건 시연 ===")
    
    env = RobotAccessibleSomaCubeEnv(max_pieces=2)
    visualizer = SomaCubeVisualizer()
    
    print("❌ 문제가 되는 배치 예시:")
    
    # 첫 번째 조각을 (1,1,1)에 배치
    test_piece_1 = BASE_PIECES[3]  # Z 조각
    position_1 = (1, 1, 1)
    
    visualizer.clear_grid()
    visualizer.place_piece(test_piece_1, position_1, 3)
    
    # 두 번째 조각을 같은 XY 위치 아래에 배치하려고 시도
    test_piece_2 = BASE_PIECES[1]  # L 조각  
    position_2 = (1, 1, 0)
    
    # 수직 경로 확인
    for x, y, z in test_piece_2:
        abs_x, abs_y, abs_z = position_2[0] + x, position_2[1] + y, position_2[2] + z
        for check_z in range(abs_z + 1, 3):
            if visualizer.grid[abs_x, abs_y, check_z] != 0:
                print(f"  🚫 ({abs_x},{abs_y},{abs_z}) 위치에 조각을 놓으려면")
                print(f"     위에서 내려와야 하는데 ({abs_x},{abs_y},{check_z})에 장애물!")
    
    print("\n✅ 올바른 배치 예시:")
    print("  - 바닥층부터 차례대로 배치")
    print("  - 수직 경로가 확보된 위치에만 배치")
    print("  - 같은 XY 좌표에는 하나의 조각만")

def test_rotation_system():
    """회전 시스템 테스트"""
    print("=== 🔄 회전 시스템 테스트 ===")
    
    for piece_id in range(7):
        piece_name = PIECE_NAMES[piece_id]
        orientations = ALL_PIECE_ORIENTATIONS[piece_id]
        
        print(f"\n🧩 {piece_name} 조각 ({piece_id}): {len(orientations)}개 회전 상태")
        
        for i in range(min(3, len(orientations))):  # 처음 3개만 보여줌
            zyz_angles, rotation_desc = get_zyz_angles(piece_id, i)
            coords = orientations[i]
            
            print(f"  인덱스 {i}: {rotation_desc}")
            print(f"    ZYZ: {zyz_angles}")
            print(f"    좌표: {coords.tolist()}")
            print(f"    🤖 로봇 명령: node.robot_control(input, {piece_id}, {zyz_angles}, (x, y, z))")
        
        if len(orientations) > 3:
            print(f"  ... (총 {len(orientations)}개 중 3개만 표시)")

def analyze_piece_accessibility():
    """조각별 로봇 접근성 분석"""
    print("=== 🔍 조각별 로봇 접근성 상세 분석 ===")
    
    for piece_id in range(7):
        piece_name = PIECE_NAMES[piece_id]
        orientations = ALL_PIECE_ORIENTATIONS[piece_id]
        
        print(f"\n🧩 {piece_name} 조각 분석:")
        
        total_positions = 0
        accessible_positions = 0
        ground_level_positions = 0
        
        for orient_idx, piece_coords in enumerate(orientations):
            orient_total = 0
            orient_accessible = 0
            orient_ground = 0
            
            for x in range(3):
                for y in range(3):
                    for z in range(3):
                        # 기본 배치 가능한지 확인 (빈 그리드 가정)
                        valid = True
                        for px, py, pz in piece_coords:
                            abs_x, abs_y, abs_z = x + px, y + py, z + pz
                            if not (0 <= abs_x < 3 and 0 <= abs_y < 3 and 0 <= abs_z < 3):
                                valid = False
                                break
                        
                        if valid:
                            orient_total += 1
                            total_positions += 1
                            
                            # 수직 접근 가능한지 확인 (빈 그리드에서는 모든 위치 접근 가능)
                            orient_accessible += 1
                            accessible_positions += 1
                            
                            # 바닥층 여부 확인
                            min_z = min(z + pz for px, py, pz in piece_coords)
                            if min_z == 0:
                                orient_ground += 1
                                ground_level_positions += 1
            
            if orient_total > 0:
                accessibility_rate = orient_accessible / orient_total
                ground_rate = orient_ground / orient_accessible if orient_accessible > 0 else 0
                print(f"  회전 {orient_idx}: {orient_accessible}/{orient_total} 위치 접근 가능 ({accessibility_rate:.2%}) | 바닥층: {orient_ground}개 ({ground_rate:.2%})")
        
        accessibility_rate = accessible_positions / max(total_positions, 1)
        ground_rate = ground_level_positions / max(accessible_positions, 1)
        print(f"  📊 전체 접근성: {accessible_positions}/{total_positions} ({accessibility_rate:.2%})")
        print(f"  🏠 바닥층 비율: {ground_level_positions}/{accessible_positions} ({ground_rate:.2%})")

def verify_ground_first_policy():
    """바닥층 우선 정책 검증"""
    print("=== 🏠 바닥층 우선 정책 검증 ===")
    
    env = RobotAccessibleSomaCubeEnv(max_pieces=3)
    
    for test in range(5):
        print(f"\n🧪 테스트 {test + 1}:")
        env.reset()
        
        for piece_idx in range(len(env.pieces_to_place)):
            piece_id = env.pieces_to_place[piece_idx]
            possible_actions = env.get_possible_actions()
            
            if not possible_actions:
                break
            
            # 상위 5개 행동의 바닥층 비율 확인
            top_actions = possible_actions[:5]
            ground_actions = [a for a in top_actions if a[2][2] == 0]
            
            ground_ratio = len(ground_actions) / len(top_actions)
            print(f"  {PIECE_NAMES[piece_id]} 조각: 상위 5개 행동 중 {len(ground_actions)}개가 바닥층 ({ground_ratio:.2%})")
            
            # 첫 번째 행동 실행
            if possible_actions:
                action = possible_actions[0]
                env.step(action)

# ===== 메인 실행부 =====
if __name__ == "__main__":
    print("🎮 실행 모드를 선택하세요:")
    print("1. 메인 시스템 실행")
    print("2. 로봇 제약 조건 시연")
    print("3. 회전 시스템 테스트")
    print("4. 조각별 접근성 분석")
    print("5. 바닥층 우선 정책 검증")
    
    try:
        mode = input("모드 선택 (1-5): ")
        
        if mode == "1":
            main()
        elif mode == "2":
            demonstrate_robot_constraints()
        elif mode == "3":
            test_rotation_system()
        elif mode == "4":
            analyze_piece_accessibility()
        elif mode == "5":
            verify_ground_first_policy()
        else:
            print("기본 모드로 실행합니다.")
            main()
            
    except KeyboardInterrupt:
        print("\n👋 프로그램을 종료합니다.")
    except Exception as e:
        print(f"💥 오류 발생: {e}")
        import traceback
        traceback.print_exc()