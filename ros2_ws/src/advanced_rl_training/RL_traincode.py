# ===== 소마큐브 완전 리팩토링 시스템 - 근본 문제 해결 =====

import os
import warnings
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import random
from collections import deque
import numpy as np
import time
from datetime import datetime

# CUDA 환경 설정
os.environ['CUDA_LAUNCH_BLOCKING'] = '1'
os.environ['TORCH_USE_CUDA_DSA'] = '1'
warnings.filterwarnings('ignore')

def initialize_gpu_safely():
    """GPU 안전 초기화"""
    try:
        if not torch.cuda.is_available():
            print("⚠️ CUDA 사용 불가, CPU로 진행")
            return torch.device('cpu')
        
        print(f"✅ CUDA 사용 가능: {torch.cuda.get_device_name(0)}")
        device = torch.device('cuda:0')
        torch.cuda.empty_cache()
        
        # 테스트
        test_tensor = torch.zeros(1).to(device)
        _ = test_tensor + 1
        print(f"🎯 GPU 초기화 완료: {device}")
        return device
    except Exception as e:
        print(f"⚠️ GPU 초기화 실패: {e}, CPU 사용")
        return torch.device('cpu')

DEVICE = initialize_gpu_safely()

# ===== 1. 소마큐브 기본 정의 =====
BASE_PIECES = {
    0: np.array([[0,0,0], [1,0,0], [0,1,0]]),  # V (3블록)
    1: np.array([[0,0,0], [1,0,0], [2,0,0], [2,1,0]]),  # L (4블록)
    2: np.array([[0,0,0], [1,0,0], [2,0,0], [1,1,0]]),  # T (4블록)
    3: np.array([[0,0,0], [1,0,0], [1,1,0], [2,1,0]]),  # Z (4블록)
    4: np.array([[0,0,0], [0,1,0], [1,1,0], [1,1,1]]),  # A (4블록)
    5: np.array([[0,0,0], [1,0,0], [1,1,0], [1,1,1]]),  # B (4블록)
    6: np.array([[0,0,0], [1,0,0], [0,1,0], [0,0,1]]),  # P (4블록)
}

PIECE_NAMES = {0: "V", 1: "L", 2: "T", 3: "Z", 4: "A", 5: "B", 6: "P"}

def get_all_rotations_optimized():
    """최적화된 회전 시스템 - 두 번째 코드와 일치하도록 수정"""
    all_rotations = {}
    
    # 기본 X, Y, Z 축 회전 (0, 90, 180, 270도)
    rotation_matrices = []
    
    # X 축 회전
    rotation_matrices.append(np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]]))      # identity
    rotation_matrices.append(np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0]]))     # x90
    rotation_matrices.append(np.array([[1, 0, 0], [0, -1, 0], [0, 0, -1]]))    # x180
    rotation_matrices.append(np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]]))     # x270
    
    # Y 축 회전
    rotation_matrices.append(np.array([[0, 0, 1], [0, 1, 0], [-1, 0, 0]]))     # y90
    rotation_matrices.append(np.array([[-1, 0, 0], [0, 1, 0], [0, 0, -1]]))    # y180
    rotation_matrices.append(np.array([[0, 0, -1], [0, 1, 0], [1, 0, 0]]))     # y270
    
    # Z 축 회전
    rotation_matrices.append(np.array([[0, -1, 0], [1, 0, 0], [0, 0, 1]]))     # z90
    rotation_matrices.append(np.array([[-1, 0, 0], [0, -1, 0], [0, 0, 1]]))    # z180
    rotation_matrices.append(np.array([[0, 1, 0], [-1, 0, 0], [0, 0, 1]]))     # z270
    
    # 추가 복합 회전들 (두 번째 코드와 동일하게)
    additional_rotations = [
        np.array([[0, 0, 1], [1, 0, 0], [0, 1, 0]]),    # x90_z90
        np.array([[0, 0, 1], [-1, 0, 0], [0, -1, 0]]),  # x90_z270
        np.array([[0, 0, -1], [1, 0, 0], [0, -1, 0]]),  # x270_z90
        np.array([[0, 0, -1], [-1, 0, 0], [0, 1, 0]]),  # x270_z270
        np.array([[0, 1, 0], [0, 0, 1], [1, 0, 0]]),    # y90_x90
        np.array([[0, -1, 0], [0, 0, -1], [1, 0, 0]]),  # y90_x270
        np.array([[0, 1, 0], [0, 0, -1], [-1, 0, 0]]),  # y270_x90
        np.array([[0, -1, 0], [0, 0, 1], [-1, 0, 0]]),  # y270_x270
        np.array([[0, 1, 0], [1, 0, 0], [0, 0, -1]]),   
        np.array([[0, -1, 0], [1, 0, 0], [0, 0, 1]]),   
        np.array([[0, 1, 0], [-1, 0, 0], [0, 0, 1]]),   
        np.array([[0, -1, 0], [-1, 0, 0], [0, 0, -1]]), 
        np.array([[1, 0, 0], [0, 0, 1], [0, 1, 0]]),    
        np.array([[1, 0, 0], [0, 0, -1], [0, -1, 0]]),  
    ]
    
    rotation_matrices.extend(additional_rotations)
    
    # 각 조각별로 회전 계산
    for piece_id, piece in BASE_PIECES.items():
        seen_signatures = set()
        unique_orientations = []
        
        for rot_matrix in rotation_matrices:
            try:
                new_p = np.dot(piece, rot_matrix)
                new_p_normalized = new_p - new_p.min(axis=0)
                coords_set = frozenset(tuple(coord) for coord in new_p_normalized)
                
                if coords_set not in seen_signatures:
                    seen_signatures.add(coords_set)
                    p_final = np.round(new_p_normalized).astype(int)
                    unique_orientations.append(p_final)
            except:
                continue
        
        all_rotations[piece_id] = unique_orientations
        print(f"✅ 조각 {PIECE_NAMES[piece_id]}: {len(unique_orientations)}개 회전")
    
    return all_rotations

ALL_PIECE_ORIENTATIONS = get_all_rotations_optimized()

# ===== 2. 적응적 보상 시스템 =====
class AdaptiveRewardCalculator:
    """적응적 보상 계산기 - 커리큘럼에 따라 보상 조정"""
    
    def __init__(self, curriculum_level=1):
        self.curriculum_level = curriculum_level
        
        # 기본 보상 (레벨에 따라 조정)
        self.base_reward = 15.0 + (curriculum_level * 5.0)
        self.connectivity_weight = 4.0
        self.stability_weight = 3.0
        self.progress_weight = 25.0  # 진행도 보상 강화
        self.completion_bonus = 150.0 + (curriculum_level * 50.0)
        self.failure_penalty = -8.0  # 패널티 완화
        
    def calculate_reward(self, env, action, piece_coords, position, is_success=False, is_failure=False):
        """적응적 보상 계산"""
        if is_failure:
            return self.failure_penalty
        
        reward = self.base_reward
        
        # 연결성 보상
        connectivity = self._calculate_connectivity(env, piece_coords, position)
        reward += connectivity * self.connectivity_weight
        
        # 안정성 보상 (바닥 우선)
        stability = self._calculate_stability(env, piece_coords, position)
        reward += stability * self.stability_weight
        
        # 진행도 보상 (강화)
        progress_ratio = len(env.placed_pieces) / len(env.pieces_to_place)
        reward += progress_ratio * self.progress_weight
        
        # 연속 배치 보너스
        if len(env.placed_pieces) >= 2:
            reward += 8.0
        
        # 완료 보너스
        if is_success:
            reward += self.completion_bonus
            # 빠른 완성 추가 보너스
            efficiency_bonus = max(0, 100 - env.step_count) * 2.0
            reward += efficiency_bonus
        
        return reward
    
    def _calculate_connectivity(self, env, piece_coords, position):
        """인접 블록 수 계산"""
        adjacent_count = 0
        directions = [(1,0,0), (-1,0,0), (0,1,0), (0,-1,0), (0,0,1), (0,0,-1)]
        
        for x, y, z in piece_coords:
            abs_x, abs_y, abs_z = position[0] + x, position[1] + y, position[2] + z
            for dx, dy, dz in directions:
                nx, ny, nz = abs_x + dx, abs_y + dy, abs_z + dz
                if (0 <= nx < 3 and 0 <= ny < 3 and 0 <= nz < 3 and 
                    env.grid[nx, ny, nz] != 0):
                    adjacent_count += 1
        
        return min(adjacent_count, 10)
    
    def _calculate_stability(self, env, piece_coords, position):
        """바닥층 우선 배치 보상"""
        ground_blocks = sum(1 for x, y, z in piece_coords if position[2] + z == 0)
        total_blocks = len(piece_coords)
        ground_ratio = ground_blocks / total_blocks
        
        # 바닥층 비율에 따른 보상
        if ground_ratio >= 0.5:
            return ground_ratio * 12.0
        else:
            return ground_ratio * 6.0

# ===== 3. 스마트 소마큐브 환경 =====
class SmartSomaCubeEnv:
    """스마트 소마큐브 환경 - 적응적 난이도 조절"""
    
    def __init__(self, curriculum_level=1, adaptive_difficulty=True):
        self.grid_shape = (3, 3, 3)
        self.curriculum_level = curriculum_level
        self.adaptive_difficulty = adaptive_difficulty
        self.reward_calculator = AdaptiveRewardCalculator(curriculum_level)
        
        # 커리큘럼별 조각 선택
        self.curriculum_pieces = {
            1: [0, 1, 2],  # V, L, T (3조각, 11블록)
            2: [0, 1, 2, 3, 4],  # V, L, T, Z, A (5조각, 19블록)
            3: list(range(7))  # 모든 조각 (7조각, 27블록)
        }
        
        self.reset()
    
    def reset(self):
        """환경 초기화"""
        self.grid = np.zeros(self.grid_shape, dtype=np.int8)
        
        # 커리큘럼에 따른 조각 선택
        available_pieces = self.curriculum_pieces[self.curriculum_level]
        
        # 적응적 난이도: 성공률에 따라 조각 수 조정
        if self.adaptive_difficulty and hasattr(self, 'recent_success_rate'):
            if self.recent_success_rate > 0.8:  # 너무 쉬우면 조각 추가
                num_pieces = min(len(available_pieces), len(available_pieces))
            elif self.recent_success_rate < 0.2:  # 너무 어려우면 조각 감소
                num_pieces = max(2, len(available_pieces) - 1)
            else:
                num_pieces = len(available_pieces)
        else:
            num_pieces = len(available_pieces)
        
        self.pieces_to_place = random.sample(available_pieces, num_pieces)
        self.current_piece_idx = 0
        self.placed_pieces = []
        self.done = False
        self.step_count = 0
        self.max_steps = num_pieces * 50  # 조각당 50스텝
        
        return self._get_state()
    
    def _get_state(self):
        """42차원 상태 벡터"""
        # 그리드 상태 (27차원)
        grid_state = self.grid.flatten().astype(np.float32)
        
        # 현재 조각 정보 (7차원)
        piece_state = np.zeros(7, dtype=np.float32)
        if self.current_piece_idx < len(self.pieces_to_place):
            current_piece = self.pieces_to_place[self.current_piece_idx]
            piece_state[current_piece] = 1.0
        
        # 진행 정보 (4차원)
        progress_state = np.array([
            len(self.placed_pieces) / len(self.pieces_to_place),
            self.current_piece_idx / len(self.pieces_to_place),
            self.step_count / self.max_steps,
            self.curriculum_level / 3
        ], dtype=np.float32)
        
        # 그리드 분석 (4차원)
        context_state = np.array([
            np.sum(self.grid > 0) / 27,
            np.sum(self.grid[:, :, 0] > 0) / 9,  # 바닥층
            np.sum(self.grid[:, :, 1] > 0) / 9,  # 중간층
            np.sum(self.grid[:, :, 2] > 0) / 9,  # 상층
        ], dtype=np.float32)
        
        return np.concatenate([grid_state, piece_state, progress_state, context_state])
    
    def get_valid_actions(self, use_smart_filtering=True):
        """스마트 유효 행동 생성"""
        if self.current_piece_idx >= len(self.pieces_to_place):
            return []
        
        piece_id = self.pieces_to_place[self.current_piece_idx]
        orientations = ALL_PIECE_ORIENTATIONS[piece_id]
        valid_actions = []
        
        for orient_idx, piece_coords in enumerate(orientations):
            for z in range(3):  # 바닥부터
                for x in range(3):
                    for y in range(3):
                        position = (x, y, z)
                        
                        if self._is_valid_placement(piece_coords, position):
                            # 스마트 필터링: 마지막 2조각이 아니면 생존성 검사 생략
                            if (not use_smart_filtering or 
                                self.current_piece_idx >= len(self.pieces_to_place) - 2 or
                                self._quick_viability_check(piece_coords, position)):
                                valid_actions.append((piece_id, orient_idx, position))
        
        # 바닥층 우선 정렬
        def priority_key(action):
            _, orient_idx, position = action
            piece_coords = orientations[orient_idx]
            min_z = min(position[2] + z for x, y, z in piece_coords)
            ground_blocks = sum(1 for x, y, z in piece_coords if position[2] + z == 0)
            connectivity = self._count_adjacent_blocks(piece_coords, position)
            
            return (min_z, -ground_blocks, -connectivity)
        
        valid_actions.sort(key=priority_key)
        return valid_actions
    
    def _quick_viability_check(self, piece_coords, position):
        """빠른 생존성 검사 (마지막 조각만)"""
        remaining_pieces = len(self.pieces_to_place) - self.current_piece_idx - 1
        if remaining_pieces == 0:
            return True
        
        # 남은 공간이 충분한지만 확인
        backup = self.grid.copy()
        piece_id = self.pieces_to_place[self.current_piece_idx]
        for px, py, pz in piece_coords:
            self.grid[position[0]+px, position[1]+py, position[2]+pz] = piece_id + 1
        
        empty_count = np.sum(self.grid == 0)
        required_blocks = sum(len(BASE_PIECES[self.pieces_to_place[i]]) 
                            for i in range(self.current_piece_idx + 1, len(self.pieces_to_place)))
        
        self.grid = backup
        return empty_count >= required_blocks
    
    def _is_valid_placement(self, piece_coords, position):
        """기본 배치 유효성 검사"""
        for x, y, z in piece_coords:
            abs_x, abs_y, abs_z = position[0] + x, position[1] + y, position[2] + z
            
            # 경계 검사
            if not (0 <= abs_x < 3 and 0 <= abs_y < 3 and 0 <= abs_z < 3):
                return False
            
            # 충돌 검사
            if self.grid[abs_x, abs_y, abs_z] != 0:
                return False
            
            # 물리적 지지 검사 (간소화)
            if abs_z > 0:
                has_support = (self.grid[abs_x, abs_y, abs_z - 1] != 0 or
                             any(oz < z and position[0] + ox == abs_x and position[1] + oy == abs_y
                                 for ox, oy, oz in piece_coords))
                if not has_support:
                    return False
        
        return True
    
    def _count_adjacent_blocks(self, piece_coords, position):
        """인접 블록 수 계산"""
        adjacent_count = 0
        directions = [(1,0,0), (-1,0,0), (0,1,0), (0,-1,0), (0,0,1), (0,0,-1)]
        
        for x, y, z in piece_coords:
            abs_x, abs_y, abs_z = position[0] + x, position[1] + y, position[2] + z
            for dx, dy, dz in directions:
                nx, ny, nz = abs_x + dx, abs_y + dy, abs_z + dz
                if (0 <= nx < 3 and 0 <= ny < 3 and 0 <= nz < 3 and 
                    self.grid[nx, ny, nz] != 0):
                    adjacent_count += 1
        
        return adjacent_count
    
    def step(self, action):
        """환경 스텝 실행"""
        self.step_count += 1
        
        if self.step_count >= self.max_steps:
            return self._get_state(), self.reward_calculator.failure_penalty, True, {"timeout": True}
        
        if self.current_piece_idx >= len(self.pieces_to_place):
            return self._get_state(), self.reward_calculator.failure_penalty, True, {"error": "No more pieces"}
        
        piece_id, orient_idx, position = action
        expected_piece = self.pieces_to_place[self.current_piece_idx]
        
        if piece_id != expected_piece:
            return self._get_state(), self.reward_calculator.failure_penalty, True, {"error": "Wrong piece"}
        
        if (piece_id >= len(ALL_PIECE_ORIENTATIONS) or 
            orient_idx >= len(ALL_PIECE_ORIENTATIONS[piece_id])):
            return self._get_state(), self.reward_calculator.failure_penalty, True, {"error": "Invalid orientation"}
        
        piece_coords = ALL_PIECE_ORIENTATIONS[piece_id][orient_idx]
        
        if not self._is_valid_placement(piece_coords, position):
            return self._get_state(), self.reward_calculator.failure_penalty, True, {"error": "Invalid placement"}
        
        # 조각 배치
        for x, y, z in piece_coords:
            abs_x, abs_y, abs_z = position[0] + x, position[1] + y, position[2] + z
            self.grid[abs_x, abs_y, abs_z] = piece_id + 1
        
        self.placed_pieces.append((piece_id, orient_idx, position))
        self.current_piece_idx += 1
        
        # 완료 확인
        is_success = self.current_piece_idx >= len(self.pieces_to_place)
        
        # 보상 계산
        reward = self.reward_calculator.calculate_reward(
            self, action, piece_coords, position, is_success=is_success
        )
        
        if is_success:
            self.done = True
            return self._get_state(), reward, True, {"success": True}
        
        return self._get_state(), reward, False, {}

# ===== 4. 강화된 DQN 모델 =====
class RobustDQN(nn.Module):
    """강화된 DQN - 안정성과 성능 개선"""
    
    def __init__(self, state_size=42, action_size=4536):
        super().__init__()
        self.action_size = action_size
        
        # 더 깊고 안정적인 네트워크
        self.feature_net = nn.Sequential(
            nn.Linear(state_size, 512),
            nn.ReLU(),
            nn.LayerNorm(512),
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.LayerNorm(256),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.ReLU()
        )
        
        # Dueling 구조
        self.value_stream = nn.Sequential(
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 1)
        )
        
        self.advantage_stream = nn.Sequential(
            nn.Linear(64, 64),
            nn.ReLU(),
            nn.Linear(64, action_size)
        )
    
    def forward(self, x):
        if not isinstance(x, torch.Tensor):
            x = torch.FloatTensor(x).to(DEVICE)
        if x.dim() == 1:
            x = x.unsqueeze(0)
        if x.shape[1] != 42:
            batch_size = x.shape[0]
            return torch.zeros(batch_size, self.action_size, device=x.device)
            
        features = self.feature_net(x)
        value = self.value_stream(features)
        advantage = self.advantage_stream(features)
        
        # Dueling 공식
        q_values = value + advantage - advantage.mean(dim=1, keepdim=True)
        return q_values

# ===== 5. 행동 인덱싱 (최적화) =====
PIECE_MAX_ORIENT = 24
POS_PER_GRID = 27
PIECE_SLOT = PIECE_MAX_ORIENT * POS_PER_GRID
NUM_PIECES = 7
ACTION_SIZE = NUM_PIECES * PIECE_SLOT

def encode_position(position):
    x, y, z = position
    return z * 9 + x * 3 + y

def decode_position(pos_index):
    z = pos_index // 9
    rem = pos_index % 9
    x = rem // 3
    y = rem % 3
    return (x, y, z)

def encode_action(piece_id, orient_idx, position):
    pos_idx = encode_position(position)
    return piece_id * PIECE_SLOT + orient_idx * POS_PER_GRID + pos_idx

def decode_action(action_index):
    piece_id = action_index // PIECE_SLOT
    rem = action_index % PIECE_SLOT
    orient_idx = rem // POS_PER_GRID
    pos_idx = rem % POS_PER_GRID
    return piece_id, orient_idx, decode_position(pos_idx)

def build_valid_action_indices(env):
    """유효 행동 인덱스 생성"""
    if env.current_piece_idx >= len(env.pieces_to_place):
        return []
    
    valid_indices = []
    for action_tuple in env.get_valid_actions():
        try:
            idx = encode_action(*action_tuple)
            valid_indices.append(idx)
        except:
            continue
    
    return valid_indices

# ===== 6. 우선순위 경험 재생 =====
class PrioritizedReplayBuffer:
    """우선순위 경험 재생 버퍼"""
    
    def __init__(self, capacity=150_000, alpha=0.6):
        self.capacity = capacity
        self.alpha = alpha
        self.beta = 0.4
        self.beta_increment = 0.001
        
        self.buffer = []
        self.priorities = np.zeros(capacity, dtype=np.float32)
        self.pos = 0
        
    def push(self, state, action, reward, next_state, done, next_valid):
        max_priority = self.priorities.max() if self.buffer else 1.0
        
        experience = (state, action, reward, next_state, done, next_valid)
        if len(self.buffer) < self.capacity:
            self.buffer.append(experience)
        else:
            self.buffer[self.pos] = experience
        
        self.priorities[self.pos] = max_priority
        self.pos = (self.pos + 1) % self.capacity
    
    def sample(self, batch_size):
        if len(self.buffer) == self.capacity:
            priorities = self.priorities
        else:
            priorities = self.priorities[:self.pos]
        
        # 우선순위 기반 샘플링
        probs = priorities ** self.alpha
        probs /= probs.sum()
        
        indices = np.random.choice(len(self.buffer), batch_size, p=probs)
        samples = [self.buffer[idx] for idx in indices]
        
        # 중요도 샘플링 가중치
        self.beta = min(1.0, self.beta + self.beta_increment)
        weights = (len(self.buffer) * probs[indices]) ** (-self.beta)
        weights /= weights.max()
        
        # 배치 분리
        states, actions, rewards, next_states, dones, next_valids = zip(*samples)
        
        return (
            np.array(states, dtype=np.float32),
            np.array(actions, dtype=np.int64),
            np.array(rewards, dtype=np.float32),
            np.array(next_states, dtype=np.float32),
            np.array(dones, dtype=np.bool_),
            next_valids,
            indices,
            weights
        )
    
    def update_priorities(self, indices, td_errors):
        """TD 오차 기반 우선순위 업데이트"""
        for idx, error in zip(indices, td_errors):
            self.priorities[idx] = abs(error) + 1e-6
    
    def __len__(self):
        return len(self.buffer)

# ===== 7. 최종 트레이너 (완전 리팩토링) =====
class UltimateSomaCubeTrainer:
    """궁극의 소마큐브 트레이너 - 모든 문제점 해결"""
    
    def __init__(
        self,
        seed=42,
        gamma=0.99,
        lr=5e-5,  # 더 낮은 학습률
        batch_size=32,  # 더 작은 배치
        epsilon_start=0.95,  # 높은 초기 탐험
        epsilon_end=0.05,
        epsilon_decay_steps=50_000,  # 매우 긴 탐험 기간
        target_update_interval=1000,
        curriculum_level=1,  # Level 1부터 시작
        use_prioritized_replay=True,
    ):
        self.device = DEVICE
        print(f"🎯 궁극 트레이너 초기화: {self.device}")
        
        # 재현성
        random.seed(seed)
        np.random.seed(seed)
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
        
        # 하이퍼파라미터
        self.gamma = gamma
        self.lr = lr
        self.batch_size = batch_size
        self.eps = epsilon_start
        self.eps_start = epsilon_start
        self.eps_end = epsilon_end
        self.eps_decay_steps = epsilon_decay_steps
        self.target_update_interval = target_update_interval
        self.curriculum_level = curriculum_level
        self.use_prioritized_replay = use_prioritized_replay
        
        # 경험 재생 버퍼
        if use_prioritized_replay:
            self.buffer = PrioritizedReplayBuffer(capacity=150_000)
        else:
            self.buffer = deque(maxlen=100_000)
        
        # 모델 초기화
        self.policy_net = RobustDQN(state_size=42, action_size=ACTION_SIZE).to(self.device)
        self.target_net = RobustDQN(state_size=42, action_size=ACTION_SIZE).to(self.device)
        self.target_net.load_state_dict(self.policy_net.state_dict())
        self.target_net.eval()
        
        # 옵티마이저 (더 안정적인 설정)
        self.optimizer = optim.AdamW(
            self.policy_net.parameters(),
            lr=self.lr,
            weight_decay=1e-6,
            eps=1e-8
        )
        
        # 학습률 스케줄러
        self.scheduler = optim.lr_scheduler.ReduceLROnPlateau(
            self.optimizer, mode='max', factor=0.8, patience=1000
        )
        
        # 추적 변수
        self.total_steps = 0
        self.episode_rewards = []
        self.episode_lengths = []
        self.success_count = 0
        self.recent_successes = deque(maxlen=100)
        self.best_success_rate = 0.0
        # --- history containers ---
        self.history = {
            "step": [],
            "episode": [],
            "level": [],
            "reward": [],
            "length": [],
            "success": [],
            "recent_success_rate": [],
            "epsilon": [],
            "lr": [],
            "loss_ma": [],
            "timestamp": [],
        }
        self.loss_ma = 0.0
        self.loss_ma_alpha = 0.02  # EWMA for loss

        print(f"✅ 모델 파라미터: {sum(p.numel() for p in self.policy_net.parameters()):,}")
    
    def _epsilon_decay(self):
        """부드러운 epsilon 감소"""
        progress = min(self.total_steps / self.eps_decay_steps, 1.0)
        self.eps = self.eps_end + (self.eps_start - self.eps_end) * (1 - progress)
    
    def select_action(self, state, env, debug_mode=False):
        """개선된 행동 선택"""
        state_t = torch.tensor(state, dtype=torch.float32, device=self.device).unsqueeze(0)
        valid_actions = env.get_valid_actions()
        
        if debug_mode:
            print(f"유효 행동 수: {len(valid_actions)}")
        
        if len(valid_actions) == 0:
            if debug_mode:
                print("❌ 유효한 행동 없음")
            return None, None, []
        
        # 행동 인덱스 변환
        valid_indices = []
        for action_tuple in valid_actions:
            try:
                idx = encode_action(*action_tuple)
                valid_indices.append(idx)
            except:
                continue
        
        if len(valid_indices) == 0:
            return None, None, []
        
        # Epsilon-greedy
        self._epsilon_decay()
        if random.random() < self.eps:
            # 탐험: 스마트 랜덤 (바닥층 우선)
            ground_actions = []
            for a in valid_actions:
                piece_coords = ALL_PIECE_ORIENTATIONS[a[0]][a[1]]
                position = a[2]  # (x, y, z)
                min_z = min(position[2] + z for x, y, z in piece_coords)
                if min_z == 0:  # 바닥층에 닿는 조각
                    ground_actions.append(a)
            
            chosen_action = random.choice(ground_actions if ground_actions else valid_actions)
            chosen_index = encode_action(*chosen_action)
            
            if debug_mode:
                print(f"🎲 스마트 탐험: {chosen_action}")
        else:
            # 활용: Q값 기반
            with torch.no_grad():
                q_values = self.policy_net(state_t).squeeze(0)
                
                # 마스킹
                mask = torch.full((ACTION_SIZE,), float('-inf'), device=self.device)
                mask[torch.tensor(valid_indices, device=self.device)] = 0.0
                q_masked = q_values + mask
                
                chosen_index = int(torch.argmax(q_masked).item())
                chosen_action = decode_action(chosen_index)
                
                if debug_mode:
                    print(f"🎯 활용: {chosen_action}, Q={q_values[chosen_index].item():.2f}")
        
        return chosen_action, chosen_index, valid_indices
    
    def optimize(self):
        """개선된 최적화"""
        if len(self.buffer) < self.batch_size:
            return 0.0
        
        if self.use_prioritized_replay:
            batch_data = self.buffer.sample(self.batch_size)
            states, actions, rewards, next_states, dones, next_valids, indices, weights = batch_data
            weights_t = torch.tensor(weights, dtype=torch.float32, device=self.device)
        else:
            # 기본 균등 샘플링
            batch = random.sample(list(self.buffer), self.batch_size)
            states, actions, rewards, next_states, dones, next_valids = zip(*batch)
            weights_t = torch.ones(self.batch_size, device=self.device)
            indices = None
        
        # 텐서 변환
        states_t = torch.tensor(states, dtype=torch.float32, device=self.device)
        actions_t = torch.tensor(actions, dtype=torch.int64, device=self.device).unsqueeze(1)
        rewards_t = torch.tensor(rewards, dtype=torch.float32, device=self.device).unsqueeze(1)
        next_states_t = torch.tensor(next_states, dtype=torch.float32, device=self.device)
        dones_t = torch.tensor(dones, dtype=torch.bool, device=self.device).unsqueeze(1)
        
        # 현재 Q값
        q_values = self.policy_net(states_t)
        q_sa = torch.gather(q_values, 1, actions_t)
        
        # Double DQN 타깃 계산
        with torch.no_grad():
            # 다음 상태에서의 최적 행동 (policy network)
            q_next = self.policy_net(next_states_t)
            
            # 각 샘플별로 유효한 행동만 고려
            next_actions = []
            for i, valid_list in enumerate(next_valids):
                if len(valid_list) == 0:
                    next_actions.append(0)
                else:
                    q_row = q_next[i]
                    mask = torch.full((ACTION_SIZE,), float('-inf'), device=self.device)
                    mask[torch.tensor(valid_list, device=self.device)] = 0.0
                    q_masked = q_row + mask
                    next_actions.append(int(torch.argmax(q_masked).item()))
            
            next_actions_t = torch.tensor(next_actions, device=self.device).unsqueeze(1)
            
            # 타깃 네트워크로 Q값 평가
            q_next_target = self.target_net(next_states_t)
            q_next_target_sa = torch.gather(q_next_target, 1, next_actions_t)
            
            # 벨만 방정식
            target = rewards_t + (~dones_t) * (self.gamma * q_next_target_sa)
        
        # 손실 계산 (중요도 샘플링 가중치 적용)
        td_errors = target - q_sa
        loss = (weights_t.unsqueeze(1) * (td_errors ** 2)).mean()
        
        # 역전파
        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.policy_net.parameters(), max_norm=1.0)
        self.optimizer.step()
        
        # 우선순위 업데이트
        if self.use_prioritized_replay and indices is not None:
            td_errors_np = td_errors.detach().cpu().numpy().flatten()
            self.buffer.update_priorities(indices, td_errors_np)
        
        # 타깃 네트워크 업데이트
        if self.total_steps % self.target_update_interval == 0:
            self.target_net.load_state_dict(self.policy_net.state_dict())
        
        self.loss_ma = (1 - self.loss_ma_alpha) * self.loss_ma + self.loss_ma_alpha * float(loss.item())
        return float(loss.item())
    
    def train_curriculum(self, episodes_per_level=2000, success_threshold=0.7, save_path="ultimate_soma"):
        """커리큘럼 학습 - Level 1부터 차근차근"""
        print("🎓 커리큘럼 학습 시작")
        
        for level in range(1, 4):  # Level 1, 2, 3
            print(f"\n🎯 커리큘럼 Level {level} 시작")
            self.curriculum_level = level
            
            level_start_time = time.time()
            level_successes = 0
            level_episodes = 0
            recent_success_rate = 0.0
            
            while level_episodes < episodes_per_level:
                env = SmartSomaCubeEnv(curriculum_level=level)
                env.recent_success_rate = recent_success_rate  # 적응적 난이도
                
                state = env.reset()
                episode_reward = 0.0
                episode_length = 0
                done = False
                
                # 에피소드 실행
                while not done and episode_length < 200:
                    episode_length += 1
                    self.total_steps += 1
                    
                    action_tuple, action_index, valid_indices = self.select_action(state, env)
                    
                    if action_tuple is None:
                        reward = env.reward_calculator.failure_penalty
                        next_state = state
                        done = True
                        next_valid = []
                    else:
                        next_state, reward, done, info = env.step(action_tuple)
                        next_valid = build_valid_action_indices(env) if not done else []
                    
                    episode_reward += reward
                    
                    # 경험 저장
                    if self.use_prioritized_replay:
                        self.buffer.push(state, action_index or 0, reward, next_state, done, next_valid)
                    else:
                        self.buffer.append((state, action_index or 0, reward, next_state, done, next_valid))
                    
                    # 학습
                    if len(self.buffer) >= self.batch_size:
                        loss = self.optimize()
                    
                    state = next_state
                    
                    if done:
                        success = info.get("success", False) if action_tuple else False
                        if success:
                            level_successes += 1
                        
                        self.recent_successes.append(success)
                        # --- log history at episode end ---
                        recent_success_rate = np.mean(list(self.recent_successes)[-50:]) if self.recent_successes else 0.0
                        cur_lr = self.optimizer.param_groups[0]["lr"]

                        self.history["step"].append(self.total_steps)
                        self.history["episode"].append(len(self.episode_rewards))
                        self.history["level"].append(level)
                        self.history["reward"].append(episode_reward)
                        self.history["length"].append(episode_length)
                        self.history["success"].append(int(success))
                        self.history["recent_success_rate"].append(float(recent_success_rate))
                        self.history["epsilon"].append(float(self.eps))
                        self.history["lr"].append(float(cur_lr))
                        self.history["loss_ma"].append(float(self.loss_ma))
                        self.history["timestamp"].append(time.time())
                        # ------------------------------------
                        break
                
                level_episodes += 1
                self.episode_rewards.append(episode_reward)
                self.episode_lengths.append(episode_length)
                
                # 진행 상황 출력
                if level_episodes % 100 == 0:
                    recent_success_rate = np.mean(list(self.recent_successes)[-50:]) if self.recent_successes else 0.0
                    level_success_rate = level_successes / level_episodes
                    
                    print(f"[Level {level}] Episode {level_episodes:4d} | "
                          f"Success: {level_success_rate:.3f} | Recent: {recent_success_rate:.3f} | "
                          f"ε: {self.eps:.3f} | Reward: {episode_reward:.1f}")
                    
                    # 학습률 조정
                    self.scheduler.step(recent_success_rate)
                
                # 레벨 완료 조건 확인
                if level_episodes >= 500 and recent_success_rate >= success_threshold:
                    print(f"✅ Level {level} 완료! 성공률: {recent_success_rate:.3f}")
                    break
            
            # 레벨 완료 저장
            level_time = time.time() - level_start_time
            print(f"⏱️ Level {level} 완료: {level_episodes} episodes, {level_time/60:.1f}분")
            
            # 중간 저장
            self._save_model(f"{save_path}_level{level}.pt")
            
            if level < 3:
                print(f"🔄 Level {level+1}로 승급 준비...")
                time.sleep(1)
        
        print("\n🎉 모든 커리큘럼 완료!")
        self._save_model(f"{save_path}_final.pt")
    
    def evaluate_comprehensive(self, episodes=50):
        """종합 평가"""
        print("\n🔬 종합 평가 시작...")
        
        results = {}
        test_conditions = [
            {"name": "탐욕적 (ε=0)", "epsilon": 0.0},
            {"name": "소량 탐험 (ε=0.05)", "epsilon": 0.05},
            {"name": "중간 탐험 (ε=0.1)", "epsilon": 0.1},
        ]
        
        for condition in test_conditions:
            print(f"\n📊 {condition['name']} 평가...")
            
            original_eps = self.eps
            self.eps = condition['epsilon']
            
            successes = 0
            total_rewards = 0
            total_steps = 0
            
            for ep in range(episodes):
                env = SmartSomaCubeEnv(curriculum_level=self.curriculum_level)
                state = env.reset()
                episode_reward = 0
                steps = 0
                done = False
                
                while not done and steps < 200:
                    steps += 1
                    action_tuple, _, _ = self.select_action(state, env)
                    
                    if action_tuple is None:
                        episode_reward += env.reward_calculator.failure_penalty
                        break
                    
                    next_state, reward, done, info = env.step(action_tuple)
                    episode_reward += reward
                    state = next_state
                    
                    if done and info.get("success", False):
                        successes += 1
                
                total_rewards += episode_reward
                total_steps += steps
            
            success_rate = (successes / episodes) * 100
            avg_reward = total_rewards / episodes
            avg_steps = total_steps / episodes
            
            results[condition['name']] = {
                'success_rate': success_rate,
                'avg_reward': avg_reward,
                'avg_steps': avg_steps
            }
            
            print(f"   성공률: {success_rate:.1f}%")
            print(f"   평균 보상: {avg_reward:.1f}")
            print(f"   평균 스텝: {avg_steps:.1f}")
            
            self.eps = original_eps
        
        return results
    
    def debug_episode(self):
        """디버깅용 에피소드 실행"""
        print("\n🔍 디버깅 에피소드...")
        
        original_eps = self.eps
        self.eps = 0.0  # 완전 탐욕적
        
        env = SmartSomaCubeEnv(curriculum_level=self.curriculum_level)
        state = env.reset()
        
        print(f"조각 순서: {[PIECE_NAMES[p] for p in env.pieces_to_place]}")
        print(f"총 블록 수: {sum(len(BASE_PIECES[p]) for p in env.pieces_to_place)}")
        
        for step in range(25):
            print(f"\n--- 스텝 {step + 1} ---")
            
            if env.current_piece_idx >= len(env.pieces_to_place):
                print("✅ 모든 조각 배치 완료!")
                break
            
            current_piece = env.pieces_to_place[env.current_piece_idx]
            print(f"현재 조각: {PIECE_NAMES[current_piece]}")
            
            action_tuple, action_index, valid_indices = self.select_action(state, env, debug_mode=True)
            
            if action_tuple is None:
                print("❌ 더 이상 배치할 수 없음")
                break
            
            next_state, reward, done, info = env.step(action_tuple)
            print(f"보상: {reward:.1f}, 완료: {done}")
            print(f"그리드 점유율: {np.sum(env.grid > 0)}/27")
            
            if done:
                if info.get("success"):
                    print("🎉 성공적으로 완료!")
                else:
                    print(f"💥 실패: {info}")
                break
            
            state = next_state
        
        self.eps = original_eps
    
    def _save_model(self, path):
        """모델 저장"""
        try:
            save_dict = {
                'policy_net_state': self.policy_net.state_dict(),
                'target_net_state': self.target_net.state_dict(),
                'optimizer_state': self.optimizer.state_dict(),
                'curriculum_level': self.curriculum_level,
                'total_steps': self.total_steps,
                'success_count': self.success_count,
                'best_success_rate': self.best_success_rate,
                'hyperparams': {
                    'gamma': self.gamma,
                    'lr': self.lr,
                    'batch_size': self.batch_size,
                    'eps_start': self.eps_start,
                    'eps_end': self.eps_end,
                    'eps_decay_steps': self.eps_decay_steps,
                },
                'history': self.history,  # <<< 추가
            }
            torch.save(save_dict, path)
            print(f"💾 모델 저장: {path}")
        except Exception as e:
            print(f"⚠️ 저장 실패: {e}")
    
    def load_model(self, path):
        """모델 로드"""
        try:
            checkpoint = torch.load(path, map_location=self.device)
            self.policy_net.load_state_dict(checkpoint['policy_net_state'])
            self.target_net.load_state_dict(checkpoint['target_net_state'])
            self.optimizer.load_state_dict(checkpoint['optimizer_state'])
            self.curriculum_level = checkpoint.get('curriculum_level', 1)
            self.total_steps = checkpoint.get('total_steps', 0)
            self.success_count = checkpoint.get('success_count', 0)
            self.best_success_rate = checkpoint.get('best_success_rate', 0.0)
            # history가 있으면 복구
            if 'history' in checkpoint and isinstance(checkpoint['history'], dict):
                self.history = checkpoint['history']
                if len(self.history.get("loss_ma", [])) > 0:
                    self.loss_ma = self.history["loss_ma"][-1]
            print(f"✅ 모델 로드: {path}")
        except Exception as e:
            print(f"⚠️ 로드 실패: {e}")
    
    def export_history_csv(self, csv_path="training_history.csv"):
        import csv, os, traceback
        try:
            # 상위 디렉터리 자동 생성
            parent = os.path.dirname(csv_path)
            if parent:
                os.makedirs(parent, exist_ok=True)

            keys = list(self.history.keys())
            with open(csv_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(keys)          # 헤더
                n = len(self.history["step"])  # 기록된 에피소드 수
                for i in range(n):
                    writer.writerow([self.history[k][i] for k in keys])

            print(f"📝 히스토리 CSV 저장: {csv_path} (rows={len(self.history['step'])})")
        except Exception as e:
            print("⚠️ CSV 저장 중 오류:", e)
            traceback.print_exc()

# ===== 8. 실행 스크립트 =====
if __name__ == "__main__":
    print("🚀 소마큐브 완전 리팩토링 시스템 시작")
    
    # 트레이너 생성
    trainer = UltimateSomaCubeTrainer(
        seed=42,
        gamma=0.99,
        lr=3e-5,  # 더 낮은 학습률
        batch_size=32,
        epsilon_start=0.95,  # 높은 초기 탐험
        epsilon_end=0.05,
        epsilon_decay_steps=30_000,  # 충분한 탐험 기간
        curriculum_level=1,  # Level 1부터
        use_prioritized_replay=True,
    )
    
    print("\n🔍 기존 모델 확인...")
    try:
        # 기존 모델이 있으면 로드
        trainer.load_model("ultimate_soma_final.pt")
        print("📚 기존 모델에서 이어서 학습")
        
        # 현재 상태 평가
        trainer.evaluate_comprehensive(episodes=30)
        trainer.debug_episode()
        
    except:
        print("🆕 새로운 모델로 시작")
    
    # 메인 학습 실행
    print("\n🎓 커리큘럼 학습 시작...")
    trainer.train_curriculum(
        episodes_per_level=100000,  # 레벨당 충분한 학습
        success_threshold=0.9,    # 90% 성공률 달성 시 승급
        save_path="ultimate_soma"
    )
    
    # 최종 평가
    print("\n🏆 최종 성능 평가...")
    final_results = trainer.evaluate_comprehensive(episodes=100)
    
    print("\n🎯 최종 결과:")
    for condition, result in final_results.items():
        print(f"{condition}: 성공률 {result['success_rate']:.1f}%, "
              f"평균 보상 {result['avg_reward']:.1f}")
    
    print("\n🔍 최종 디버깅...")
    trainer.debug_episode()

    # === CSV 저장 호출 추가 ===
    import os
    from datetime import datetime
    outdir = "logs"
    os.makedirs(outdir, exist_ok=True)
    csv_path = os.path.join(outdir, f"training_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
    trainer.export_history_csv(csv_path)
    print("CSV saved to:", csv_path)

    print("\n✨ 완전 리팩토링 시스템 완료!")