import torch
import torch.nn as nn
import numpy as np
import glob
import os
from scipy.spatial.transform import Rotation as R
import random

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

# ===== 회전 시스템 =====
def get_all_rotations_with_matrices():
    all_rotations = {}
    rotation_matrices_info = {}
    
    rotation_matrices = []
    matrix_descriptions = []
    
    # 기본 회전들
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
                else:
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
                else:
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
                else:
                    rot = np.array([[0, 1, 0], [-1, 0, 0], [0, 0, 1]])
                    desc = "z270"
            
            if desc != "identity" or len(rotation_matrices) == 0:
                rotation_matrices.append(rot)
                matrix_descriptions.append(desc)
    
    # 추가 회전들
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
        return [0, 0, 0], "error"

# 전역 변수로 회전 정보 초기화
ALL_PIECE_ORIENTATIONS, ROTATION_MATRICES_INFO = get_all_rotations_with_matrices()

# ===== 간단한 환경 =====
class SimpleRobotEnv:
    def __init__(self, max_pieces=2):
        self.max_pieces = max_pieces
        self.reset()
    
    def reset(self):
        self.grid = np.zeros((3, 3, 3), dtype=int)
        all_pieces = list(range(7))
        self.pieces_to_place = random.sample(all_pieces, self.max_pieces)
        self.current_piece_idx = 0
        self.placed_pieces = []
        self.done = False
        return self._get_state()
    
    def _get_state(self):
        state = np.zeros(36)
        state[:27] = self.grid.flatten()
        
        if self.current_piece_idx < len(self.pieces_to_place):
            current_piece = self.pieces_to_place[self.current_piece_idx]
            state[27 + current_piece] = 1
        
        state[34] = len(self.placed_pieces) / self.max_pieces
        state[35] = self.current_piece_idx / self.max_pieces
        return state
    
    def _has_clear_vertical_path(self, piece_coords, position):
        for x, y, z in piece_coords:
            abs_x, abs_y, abs_z = position[0] + x, position[1] + y, position[2] + z
            if not (0 <= abs_x < 3 and 0 <= abs_y < 3 and 0 <= abs_z < 3):
                continue
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
    
    def _is_supported(self, piece_coords, position):
        for x, y, z in piece_coords:
            abs_z = position[2] + z
            if abs_z == 0:
                return True
            if abs_z > 0:
                abs_x, abs_y = position[0] + x, position[1] + y
                if 0 <= abs_x < 3 and 0 <= abs_y < 3:
                    if self.grid[abs_x, abs_y, abs_z - 1] != 0:
                        return True
        return False
    
    def get_possible_actions(self):
        if self.current_piece_idx >= len(self.pieces_to_place):
            return []
        
        possible_actions = []
        piece_id = self.pieces_to_place[self.current_piece_idx]
        orientations = ALL_PIECE_ORIENTATIONS[piece_id]
        
        for orient_idx, piece_coords in enumerate(orientations):
            for z in range(3):
                for x in range(3):
                    for y in range(3):
                        position = (x, y, z)
                        if (self._is_valid_placement(piece_coords, position) and 
                            self._is_supported(piece_coords, position) and
                            self._has_clear_vertical_path(piece_coords, position)):
                            action = (piece_id, orient_idx, position)
                            possible_actions.append(action)
        
        # 바닥층 우선 정렬
        def sort_key(action):
            piece_id, orient_idx, position = action
            piece_coords = orientations[orient_idx]
            min_z = min(position[2] + z for x, y, z in piece_coords)
            ground_blocks = sum(1 for x, y, z in piece_coords if position[2] + z == 0)
            return (min_z, -ground_blocks, position[2])
        
        possible_actions.sort(key=sort_key)
        return possible_actions
    
    def step(self, action):
        piece_id, orient_idx, position = action
        piece_coords = ALL_PIECE_ORIENTATIONS[piece_id][orient_idx]
        
        for x, y, z in piece_coords:
            abs_x, abs_y, abs_z = position[0] + x, position[1] + y, position[2] + z
            self.grid[abs_x, abs_y, abs_z] = piece_id + 1
        
        self.placed_pieces.append((piece_id, orient_idx, position))
        self.current_piece_idx += 1
        
        if self.current_piece_idx >= len(self.pieces_to_place):
            self.done = True
            return self._get_state(), True, {"success": True}
        
        return self._get_state(), False, {}

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

# ===== 모델 경로 설정 =====
# PACKAGE_PATH = os.path.dirname(os.path.abspath(__file__))  # 현재 스크립트 위치
# CUBE_MODEL_FILENAME = "best_soma_model.pth"
# CUBE_MODEL_PATH = os.path.join(PACKAGE_PATH, "resource", CUBE_MODEL_FILENAME)
CUBE_MODEL_PATH = "/home/jsj2204/SomaCube/restart/models/level_5_robot_friendly/robot_friendly_soma_level_5_20250814_151950.pth"
# ===== 로봇 테스터 =====
class RobotTester:
    def __init__(self, device='cpu'):
        self.device = device
        self.model = None
        self.loaded_level = None
        
        # 지정된 모델 파일 로딩
        self._load_specified_model()
    
    def _load_specified_model(self):
        """지정된 경로의 모델 로딩"""
        if not os.path.exists(CUBE_MODEL_PATH):
            print(f"❌ 모델 파일을 찾을 수 없습니다: {CUBE_MODEL_PATH}")
            print(f"📁 다음 경로에 '{CUBE_MODEL_FILENAME}' 파일을 배치하세요:")
            print(f"   {os.path.dirname(CUBE_MODEL_PATH)}")
            return
        
        try:
            # PyTorch 2.6+ 호환성을 위해 weights_only=False 명시
            checkpoint = torch.load(CUBE_MODEL_PATH, map_location=self.device, weights_only=False)
            
            # 레벨 정보 추출 (없으면 기본값 2)
            self.loaded_level = checkpoint.get('level', 2)
            
            self.model = HierarchicalDQN(36).to(self.device)
            self.model.load_state_dict(checkpoint['model_state_dict'])
            self.model.eval()
            
            print(f"✅ 모델 로딩 완료: {CUBE_MODEL_PATH}")
            print(f"📊 레벨: {self.loaded_level}")
            
        except Exception as e:
            print(f"❌ 모델 로딩 실패: {e}")
            print(f"💡 모델 파일이 올바른 형식인지 확인하세요.")
    
    def _auto_load_model(self):
        """자동으로 최신 모델 로딩 (사용 안 함)"""
        pass
    
    def _find_latest_model(self, level, model_dir="models"):
        """최신 모델 찾기 (사용 안 함)"""
        return None
    
    def _load_model(self, model_path, level):
        """모델 로딩 (사용 안 함)"""
        return False
    
    def _get_valid_actions_for_piece(self, piece_id, env):
        valid_actions = []
        orientations = ALL_PIECE_ORIENTATIONS[piece_id]
        
        for orient_idx, piece_coords in enumerate(orientations):
            for x in range(3):
                for y in range(3):
                    for z in range(3):
                        position = (x, y, z)
                        if (env._is_valid_placement(piece_coords, position) and 
                            env._is_supported(piece_coords, position) and
                            env._has_clear_vertical_path(piece_coords, position)):
                            valid_actions.append((orient_idx, x * 9 + y * 3 + z))
        return valid_actions
    
    def _select_action(self, state, piece_id, env):
        if self.model is None:
            return None
            
        with torch.no_grad():
            state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
            orientation_q, position_q = self.model(state_tensor)
            
            valid_actions = self._get_valid_actions_for_piece(piece_id, env)
            if not valid_actions:
                return None
            
            best_value = float('-inf')
            best_action = None
            
            for orient_idx, pos_idx in valid_actions:
                if orient_idx < orientation_q.shape[1] and pos_idx < position_q.shape[1]:
                    value = orientation_q[0][orient_idx].item() + position_q[0][pos_idx].item()
                    if value > best_value:
                        best_value = value
                        best_action = (orient_idx, pos_idx)
            
            if best_action is None:
                return None
            
            orient_idx, pos_idx = best_action
        
        x = pos_idx // 9
        y = (pos_idx % 9) // 3
        z = pos_idx % 3
        
        return (piece_id, orient_idx, (x, y, z))
    
    def test_robot_control(self, num_tests=1):
        """로봇 제어 테스트"""
        if self.model is None:
            print("❌ 모델이 로딩되지 않았습니다.")
            return
        
        print(f"🤖 소마큐브 로봇 제어 테스트 시작 (레벨 {self.loaded_level}, {num_tests}회)")
        print("="*60)
        
        env = SimpleRobotEnv(max_pieces=self.loaded_level)
        success_count = 0
        
        for test in range(num_tests):
            state = env.reset()
            
            print(f"\n🧩 테스트 {test + 1}:")
            print(f"   사용할 조각들: {[PIECE_NAMES[p] for p in env.pieces_to_place]}")
            
            robot_commands = []
            steps = 0
            
            while not env.done and steps < 20:
                if env.current_piece_idx >= len(env.pieces_to_place):
                    break
                
                piece_id = env.pieces_to_place[env.current_piece_idx]
                action = self._select_action(state, piece_id, env)
                
                if action is None:
                    print(f"   ❌ 단계 {steps + 1}: 가능한 행동이 없음")
                    break
                
                # 행동 실행
                next_state, done, info = env.step(action)
                
                # 로봇 제어 명령 생성
                piece_id, orient_idx, position = action
                piece_name = PIECE_NAMES[piece_id]
                piece_coords = ALL_PIECE_ORIENTATIONS[piece_id][orient_idx]
                zyz_angles, rotation_desc = get_zyz_angles(piece_id, orient_idx)
                
                # 바닥층 여부 확인
                min_z = min(position[2] + z for x, y, z in piece_coords)
                level_info = "바닥층" if min_z == 0 else f"{min_z}층"
                
                command = f"node.robot_control(user_input, {piece_id}, {zyz_angles}, {position})"
                robot_commands.append(command)
                
                print(f"   🔧 단계 {steps + 1}: {piece_name} 조각 → 위치 {position} ({level_info})")
                print(f"       회전: {rotation_desc} → ZYZ{zyz_angles}")
                print(f"       명령: {command}")
                
                state = next_state
                steps += 1
            
            success = env.done and "success" in info
            if success:
                success_count += 1
            
            status = "✅ 성공" if success else "❌ 실패"
            print(f"   {status} ({steps}단계)")
            
            if success and num_tests == 1:
                print(f"\n🤖 로봇 제어 스크립트:")
                print("="*50)
                for i, cmd in enumerate(robot_commands):
                    print(f"# 단계 {i+1}")
                    print(cmd)
                print("="*50)
        
        print(f"\n📊 최종 결과: {success_count}/{num_tests} 성공 ({success_count/num_tests:.1%})")

# ===== 메인 실행 =====
def main():
    tester = RobotTester()
    
    if tester.model is None:
        print("프로그램을 종료합니다.")
        return
    
    try:
        num_tests = int(input(f"🔢 테스트 횟수를 입력하세요 (기본 1): ") or "1")
        tester.test_robot_control(num_tests)
        
    except KeyboardInterrupt:
        print("\n👋 프로그램 종료")
    except ValueError:
        print("❌ 올바른 숫자를 입력하세요.")
        tester.test_robot_control(1)
    except Exception as e:
        print(f"💥 오류 발생: {e}")

if __name__ == "__main__":
    main()