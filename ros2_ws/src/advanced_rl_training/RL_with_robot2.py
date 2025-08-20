import numpy as np
import torch
import torch.nn as nn
import random
from collections import deque, namedtuple
import time
from scipy.spatial.transform import Rotation as R 
from scipy.spatial.transform import Rotation
from od_msg.srv import SrvDepthPosition
import os
import rclpy
from ament_index_python.packages import get_package_share_directory
from rclpy.node import Node
import DR_init
from somacube.onrobot import RG
import sys

PACKAGE_NAME = "somacube"
PACKAGE_PATH = get_package_share_directory(PACKAGE_NAME)

CUBE_MODEL_FILENAME = "best_soma_model.pth"

CUBE_MODEL_PATH = os.path.join(PACKAGE_PATH, "resource", CUBE_MODEL_FILENAME)


# for single robot
ROBOT_ID = "dsr01"
ROBOT_MODEL = "m0609"
VELOCITY, ACC = 60, 60
BUCKET_POS = [445.5, -242.6, 174.4, 156.4, 180.0, -112.5]


tool_dict = {1: "1", 2: "2", 3: "3", 4: "4", 5: "5", 6: "6", 7: "7"}

DR_init.__dsr__id = ROBOT_ID
DR_init.__dsr__model = ROBOT_MODEL

rclpy.init()
dsr_node = rclpy.create_node("rokey_simple_move", namespace=ROBOT_ID)
DR_init.__dsr__node = dsr_node

try:
    from DSR_ROBOT2 import movej, movel, get_current_posx, mwait,\
                           trans, wait, DR_BASE, amovel, amovej, \
                        get_current_solution_space, get_current_posj,\
                        movejx
    from DR_common2 import posx, posj
except ImportError as e:
    print(f"Error importing DSR_ROBOT2: {e}")
    sys.exit()

########### Gripper Setup. Do not modify this area ############

GRIPPER_NAME = "rg2"
TOOLCHANGER_IP = "192.168.1.1"
TOOLCHANGER_PORT = "502"
gripper = RG(GRIPPER_NAME, TOOLCHANGER_IP, TOOLCHANGER_PORT)


########### Robot Controller ############


re_grap_pos = [624.960, 119.680, -22.780, 68.28, -179.3, 67.66]
HOME = [0, 0, 90, 0, 90, 0]
def up_pos(set_pos, axis, val):
        pos = set_pos.copy()
        pos[axis] += val
        return posx(pos)


def choose_best_orientation(start_pose, zyz_base_delta):
    """
    AI가 제안한 회전(zyz_base_delta)을 기반으로 두 개의 후보 자세를 만듭니다.
    1. 원래 자세
    2. 툴 롤을 90도 추가한 자세
    그 중 '손 날'이 더 수평에 가까운(안전한) 자세를 선택하여 반환합니다.
    """
    # 후보 1: AI가 제안한 원래 목표 자세 계산
    pose1 = apply_rotation_manually(start_pose, zyz_base_delta)

    # 후보 2: 툴 롤(Rz')을 90도 추가한 목표 자세 계산
    correction_delta = zyz_base_delta.copy()
    correction_delta[2] += 90.0
    pose2 = apply_rotation_manually(start_pose, correction_delta)
    
    # "손 날"의 방향을 나타내는 그리퍼의 X축([1,0,0])이 베이스 기준에서 어떤 방향인지 계산
    r1 = R.from_euler('zyz', pose1[3:], degrees=True)
    gripper_x_vector1 = r1.apply([1, 0, 0])
    
    r2 = R.from_euler('zyz', pose2[3:], degrees=True)
    gripper_x_vector2 = r2.apply([1, 0, 0])
    
    # "손 날"의 Z값(수직 성분)의 절대값이 작을수록 더 수평에 가깝고 안전함
    score1 = abs(gripper_x_vector1[2])
    score2 = abs(gripper_x_vector2[2])

    # 더 안전한(점수가 낮은) 자세를 최종 선택
    if score1 <= score2:
        print(f"Choosing original orientation (score: {score1:.2f})")
        return pose1
    else:
        print(f"Choosing 90-deg corrected orientation (score: {score2:.2f})")
        return pose2


def apply_rotation_manually(start_pose, zyz_delta):
    """
    개선된 회전 적용 함수 - 더 안정적인 ZYZ 변환
    """
    try:
        # 1. 시작 자세의 오일러 각을 회전 객체로 변환
        start_euler = start_pose[3:]
        r_start = R.from_euler('zyz', start_euler, degrees=True)

        # 2. 적용할 회전 변화량을 회전 객체로 변환
        r_delta = R.from_euler('zyz', zyz_delta, degrees=True)

        # 3. 두 회전을 곱하여 최종 회전 객체를 계산
        r_final = r_start * r_delta

        # 4. 최종 회전 객체를 다시 ZYZ 오일러 각으로 변환
        final_euler = r_final.as_euler('zyz', degrees=True)
        
        # 5. 각도 정규화 (-180 ~ 180도)
        # final_euler = [(angle + 180) % 360 - 180 for angle in final_euler]

        # 6. 원래의 위치(x, y, z)와 새로운 오일러 각을 합쳐 최종 자세 반환
        final_pose = start_pose[:3] + final_euler.tolist()
        
        return final_pose
        
    except Exception as e:
        print(f"Rotation application error: {e}")
        return start_pose  # 오류 시 원래 자세 반환


def correct_colliding_pose(target_pose):
    """
    주어진 목표 자세가 충돌을 유발하는지 확인하고,
    문제가 있다면 툴 롤(Rz')을 90도로 강제 수정하여 반환합니다.
    """
    # is_gripper_collision_expected 함수는 이전에 정의한 것을 그대로 사용합니다.
    if is_gripper_collision_expected(target_pose):
        print("Collision pose detected. Forcing a 90-degree tool roll.")
        
        corrected_pose = target_pose.copy()
        
        # 마지막 Z'축 회전값을 90도로 강제 설정하여 '손날'을 눕힘
        corrected_pose[5] = 90.0
        
        return corrected_pose
    else:
        # 충돌 조건이 아니면 원래 자세 그대로 반환
        return target_pose

def is_gripper_collision_expected(pose):
    """
    주어진 자세(pose)가 '손날이 서는' 충돌을 유발할지 판단하는 함수.
    """
    ry = pose[4]
    rz_prime = pose[5]
    
    is_lying_down = abs(ry - 90) < 15 or abs(ry + 90) < 15
    is_roll_problematic = (abs(rz_prime) < 15 or abs(rz_prime - 180) < 15 or abs(rz_prime + 180) < 15)
    
    if is_lying_down and is_roll_problematic:
        return True # 충돌 위험 있음
    
    return False # 안전함


class RobotController(Node):
    def __init__(self):
        super().__init__("somacube")
        self.init_robot()
        self.depth_client = self.create_client(SrvDepthPosition, "/get_3d_position")
        while not self.depth_client.wait_for_service(timeout_sec=3.0):
            self.get_logger().info("Waiting for depth position service...")
        self.depth_request = SrvDepthPosition.Request()
        # self.robot_control()

    def get_robot_pose_matrix(self, x, y, z, rx, ry, rz):
        R = Rotation.from_euler("ZYZ", [rx, ry, rz], degrees=True).as_matrix()
        T = np.eye(4)
        T[:3, :3] = R
        T[:3, 3] = [x, y, z]
        return T

    def transform_to_base(self, camera_coords, gripper2cam_path, robot_pos):
        """
        Converts 3D coordinates from the camera coordinate system
        to the robot's base coordinate system.
        """
        gripper2cam = np.load(gripper2cam_path)
        coord = np.append(np.array(camera_coords), 1)  # Homogeneous coordinate

        x, y, z, rx, ry, rz = robot_pos
        base2gripper = self.get_robot_pose_matrix(x, y, z, rx, ry, rz)

        # 좌표 변환 (그리퍼 → 베이스)
        base2cam = base2gripper @ gripper2cam
        td_coord = np.dot(base2cam, coord)

        return td_coord[:3]

    def robot_control(self, input_data, peice_id, roation, pos):
        user_input = input_data
        peice_id  += 1
        if user_input.lower() == "q":
            self.get_logger().info("Quit the program...")
            sys.exit()

        if user_input:
            # try:
            #     user_input_int = int(user_input)
            #     user_input = tool_dict.get(user_input_int, user_input)
            # except ValueError:
            #     pass  # 변환 불가능하면 원래 문자열 유지
            self.depth_request.target = str(peice_id)
            self.get_logger().info("call depth position service with yolo")
            depth_future = self.depth_client.call_async(self.depth_request)
            rclpy.spin_until_future_complete(self, depth_future)

            if depth_future.result():
                result = depth_future.result().depth_position.tolist()
                self.get_logger().info(f"Received depth position: {result}")
                if sum(result) == 0:
                    print("No target position")
                    return

                gripper2cam_path = os.path.join(
                    PACKAGE_PATH, "resource", "T_gripper2camera.npy"
                )
                robot_posx = get_current_posx()[0]
                td_coord = self.transform_to_base(result, gripper2cam_path, robot_posx)

                if td_coord[2] and sum(td_coord) != 0:
                    td_coord[2] += -5  # DEPTH_OFFSET
                    td_coord[2] = max(td_coord[2], 2)  # MIN_DEPTH: float = 2.0

                target_pos = list(td_coord[:3]) + robot_posx[3:]

                self.get_logger().info(f"target position: {target_pos}")
                self.somacube_target(target_pos, roation, pos)
                self.init_robot()
        self.init_robot()
        


    def init_robot(self):
        # JReady = [0, 0, 90, 0, 90, 0]
        JReady = [-14.74, 6.47, 57.94, -0.03, 115.59, -14.74]
        movej(JReady, vel=VELOCITY, acc=ACC)
        gripper.open_gripper()
        mwait()

    def somacube_target(self, target_pos, rotaion, pos):
        
        RE_GRAB_POS = [640, -10.82, 250]
        RE_GRAB_POS_UP = [640, -10.82, 300.00]
        ROTATION_POS = [471.050, -254.770, 203.250]
        # target_pos[3] -= 10


        print(target_pos)
        movel(target_pos, vel=VELOCITY, acc=ACC)
        mwait()
        gripper.close_gripper()
        # mwait(2.0)
        while gripper.get_status()[0]:
            time.sleep(0.5)
        # print("잡다")
        # target_pos_up = trans(target_pos, [0, 0, 200, 0, 0, 0]).tolist()
        # 잡고 올림
        target_pos_up = up_pos(target_pos, 2, 300)
        movel(target_pos_up, vel=VELOCITY, acc=ACC)

        current_pose, _= get_current_posx()
        re_pos = RE_GRAB_POS_UP + list(current_pose[3:])
        
        movel(re_pos, vel=VELOCITY, acc=ACC)
        print(target_pos_up)
        target_pos_rotation = apply_rotation_manually(re_pos, rotaion)
        print("좌표 변환")

        # # 충돌 방지루틴

        print(f"재그랩 전 : {target_pos_rotation}")
        # movel(target_pos_rotation, vel=VELOCITY, acc=ACC)
        # movejx(target_pos_rotation, vel=VELOCITY, acc=ACC, sol=6)
        wait(1)
        current_sol = get_current_solution_space()
        current_x, _ = get_current_posx()
        current_j = get_current_posj()
        print(f"현재 sol : {current_sol}")
        print(f"현재 x : {current_x}")
        print(f"현재 j : {current_j}")
        # wait(1)
        
        re_grap_pos = RE_GRAB_POS + list(current_x[3:])

        # 솔루션 스페이스 전환 팔꿈치 아래 향할 때
        # if current_sol == 2:
        #     movejx(target_pos_rotation, vel=VELOCITY, acc=ACC, sol = 6)



        if (is_gripper_collision_expected(target_pos_rotation)):
            is_singular = False
            ry_val = target_pos_rotation[4]
            # 특이점 회피
            if abs(ry_val - 90.0) < 0.1 or abs(ry_val + 90.0) < 0.1:
                print(f"Singularity detected at Ry={ry_val:.2f}°. Adjusting to avoid it.")
                target_pos_rotation[4] = 89.9 # 또는 90.1
                is_singular = True

            if is_singular:
                movejx(target_pos_rotation, vel=VELOCITY, acc=ACC, sol=0)
                mwait()
                is_singular = True

            print("재그랩")
            current_j = get_current_posj()
            current_j[5] += 90 # 조인트 6 번에 90도 더함 
            
            movej(current_j, vel=VELOCITY, acc=ACC)
            wait(0.1)
            print("내려버려~")
            movel(up_pos(get_current_posx()[0], 2, -50), vel=VELOCITY, acc=ACC)

            mwait()
            gripper.open_gripper()
            while gripper.get_status()[0]:
                time.sleep(0.5)
            
            ######## 다시 돌리는 작업############
            # print("다시 돌려잇~")
            # movel(up_pos(get_current_posx()[0], 2, 50), vel=VELOCITY, acc=ACC)
            # current_x, _ = get_current_posx()
            
            # gogogo = apply_rotation_manually(current_x, [0,0,-90])
            # movel(gogogo, acc=ACC, vel=VELOCITY)
            # movel(up_pos(get_current_posx()[0], 2, -50), vel=VELOCITY, acc=ACC)
            # mwait()
            # gripper.close_gripper()
            # # mwait(2.0)
            # while gripper.get_status()[0]:
            #     time.sleep(0.5)
            # gogogo2 = apply_rotation_manually(current_x, [0,90,0])
            # movel(gogogo2, acc=ACC, vel=VELOCITY)
            # mwait()
            # gripper.open_gripper()
            # while gripper.get_status()[0]:
            #     time.sleep(0.5)
            
            # movej(HOME, vel=VELOCITY, acc=ACC)
            return
        
        # # current_pose, _= get_current_posx()
        # # re_grap_pos = RE_GRAB_POS + list(current_pose[3:])
        
        movel(target_pos_rotation, vel=VELOCITY, acc=ACC)
        print("내려버려~")
        movel(up_pos(get_current_posx()[0], 2, -70), vel=VELOCITY, acc=ACC)


        gripper.open_gripper()
        mwait()
        while gripper.get_status()[0]:
            time.sleep(0.5)
        movel(up_pos(get_current_posx()[0], 2, 70), vel=VELOCITY, acc=ACC)    
        
        movej(HOME, vel=VELOCITY, acc=ACC)


######################################################################
# 1. 소마 큐브 조각 및 회전 정의
######################################################################
BASE_PIECES = {
    0: np.array([[0,0,0], [1,0,0], [0,1,0]]), # V 조각
    1: np.array([[0,0,0], [1,0,0], [2,0,0], [2,1,0]]), # L 조각
    2: np.array([[0,0,0], [1,0,0], [2,0,0], [1,1,0]]), # T 조각
    3: np.array([[0,0,0], [1,0,0], [1,1,0], [2,1,0]]), # Z 조각
    4: np.array([[0,0,0], [0,1,0], [1,1,0], [1,1,1]]), # A 조각 (오른손)
    5: np.array([[0,0,0], [1,0,0], [1,1,0], [1,1,1]]), # B 조각 (왼손)
    6: np.array([[0,0,0], [1,0,0], [0,1,0], [0,0,1]]), # P 조각
}

def get_all_rotations():
    all_rotations = {}
    rotation_matrices = [
        np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0]]), # x축
        np.array([[0, 0, 1], [0, 1, 0], [-1, 0, 0]]), # y축
        np.array([[0, -1, 0], [1, 0, 0], [0, 0, 1]])  # z축
    ]
    for i, piece in BASE_PIECES.items():
        seen_normalized_tuples = set()
        unique_orientations_np = []
        queue = [piece]
        p_norm = piece - piece.min(axis=0)
        p_tuple = tuple(sorted(map(tuple, p_norm)))
        seen_normalized_tuples.add(p_tuple)
        unique_orientations_np.append(piece)
        head = 0
        while head < len(queue):
            current_piece = queue[head]; head += 1
            for rot_matrix in rotation_matrices:
                new_p = np.dot(current_piece, rot_matrix)
                new_p_normalized = new_p - new_p.min(axis=0)
                new_p_tuple = tuple(sorted(map(tuple, new_p_normalized)))
                if new_p_tuple not in seen_normalized_tuples:
                    seen_normalized_tuples.add(new_p_tuple)
                    unique_orientations_np.append(new_p)
                    queue.append(new_p)
        final_rotations = [p - p.min(axis=0) for p in unique_orientations_np]
        all_rotations[i] = final_rotations
    return all_rotations

ALL_PIECE_ORIENTATIONS = get_all_rotations()

######################################################################
# 2. 행동 매핑 시스템
######################################################################
class ActionMapper:
    def __init__(self):
        self.action_to_index = {}; self.index_to_action = {}
        index = 0
        for piece_id in range(7):
            for orient_idx in range(len(ALL_PIECE_ORIENTATIONS[piece_id])):
                for x in range(3):
                    for y in range(3):
                        for z in range(3):
                            action = (piece_id, orient_idx, (x, y, z))
                            self.action_to_index[action] = index
                            self.index_to_action[index] = action
                            index += 1
        self.total_actions = index
    def action_to_idx(self, action): return self.action_to_index.get(action, -1)
    def idx_to_action(self, idx): return self.index_to_action.get(idx, None)

######################################################################
# 3. 강화학습 환경
######################################################################
class SomaCubeEnv:
    def __init__(self, action_mapper):
        self.grid_shape = (3, 3, 3); self.action_mapper = action_mapper; self.reset()
    def reset(self):
        self.grid = np.zeros(self.grid_shape, dtype=int); self.pieces_to_place = random.sample(list(range(7)), 7); self.current_piece_idx = self.pieces_to_place.pop(0); self.done = False; return self._get_state()
    def _get_state(self):
        state = np.zeros(27 + 7); state[:27] = self.grid.flatten(); state[27 + self.current_piece_idx] = 1; return state
    def _is_valid_placement(self, piece_coords, position):
        for x, y, z in piece_coords:
            abs_x, abs_y, abs_z = position[0] + x, position[1] + y, position[2] + z
            if not (0 <= abs_x < 3 and 0 <= abs_y < 3 and 0 <= abs_z < 3) or self.grid[abs_x, abs_y, abs_z] != 0: return False
        return True
    def _is_supported(self, piece_coords, position):
        for x, y, z in piece_coords:
            abs_z = position[2] + z
            if abs_z == 0: return True
            if abs_z > 0 and self.grid[position[0] + x, position[1] + y, abs_z - 1] != 0: return True
        return False
    def get_possible_actions(self):
        possible_action_indices = []
        orientations = ALL_PIECE_ORIENTATIONS[self.current_piece_idx]
        for orient_idx, piece_coords in enumerate(orientations):
            for x in range(3):
                for y in range(3):
                    for z in range(3):
                        if self._is_valid_placement(piece_coords, (x, y, z)) and self._is_supported(piece_coords, (x, y, z)):
                            action = (self.current_piece_idx, orient_idx, (x, y, z))
                            action_idx = self.action_mapper.action_to_idx(action)
                            if action_idx != -1: possible_action_indices.append(action_idx)
        return possible_action_indices
    def step(self, action_idx):
        action = self.action_mapper.idx_to_action(action_idx)
        if action is None or action[0] != self.current_piece_idx: return self._get_state(), -5.0, True, {"error": "Invalid action"}
        piece_id, orient_idx, position = action
        piece_coords = ALL_PIECE_ORIENTATIONS[self.current_piece_idx][orient_idx]
        if not self._is_valid_placement(piece_coords, position) or not self._is_supported(piece_coords, position): return self._get_state(), -5.0, True, {"error": "Invalid placement"}
        for x, y, z in piece_coords: self.grid[position[0] + x, position[1] + y, position[2] + z] = self.current_piece_idx + 1
        if not self.pieces_to_place: return self._get_state(), 100.0, True, {"success": True}
        self.current_piece_idx = self.pieces_to_place.pop(0)
        if not self.get_possible_actions(): return self._get_state(), -10.0, True, {"error": "Stuck"}
        return self._get_state(), 1.0, False, {}

######################################################################
# 4. DQN 신경망
######################################################################
class DQN(nn.Module):
    def __init__(self, state_size, action_size):
        super(DQN, self).__init__(); self.network = nn.Sequential(nn.Linear(state_size, 512), nn.ReLU(), nn.Dropout(0.2), nn.Linear(512, 512), nn.ReLU(), nn.Dropout(0.2), nn.Linear(512, 256), nn.ReLU(), nn.Linear(256, action_size))
    def forward(self, x): return self.network(x.float())
######################################################################
# 5. 회전 계산 함수 (수정된 버전)
######################################################################

def calculate_rotation(base_coords, rotated_coords):
    """회전 객체 반환"""
    base_centered = base_coords - np.mean(base_coords, axis=0)
    rotated_centered = rotated_coords - np.mean(rotated_coords, axis=0)
    
    try:
        rotation, rmsd = R.align_vectors(rotated_centered, base_centered)
        angle_rad = np.linalg.norm(rotation.as_rotvec())
        if angle_rad < 1e-6:
            return None
        return rotation
    except Exception as e:
        print(f"Rotation calculation error: {e}")
        return None
######################################################################
# 6. 테스트 실행 (수정된 버전)
######################################################################


def main():
    
    # --- setup ---
    node = RobotController()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    action_mapper = ActionMapper()
    env = SomaCubeEnv(action_mapper)
    state_size, action_size = 34, action_mapper.total_actions
    policy_net = DQN(state_size, action_size).to(device)
    
    print(f"🤖 Loading trained model from '{CUBE_MODEL_PATH}'")
    try:
        policy_net.load_state_dict(torch.load(CUBE_MODEL_PATH, map_location=device))
    except FileNotFoundError:
        print(f"Error: Model file not found at '{CUBE_MODEL_PATH}'. Please run training script first."); exit()

    policy_net.eval()
    print("Model loaded successfully. Starting test..."); print("-" * 60)

    ##################테스트 스타트###################
    user_input = input("start: ")
    user_input_int = int(user_input)
    while user_input_int == 1:
        
        test_successes = 0

        state = env.reset()
        done = False; step_count = 0; total_reward = 0; solution_path = []

        while not done and step_count < 100:
            possible_actions = env.get_possible_actions()
            if not possible_actions: break
            with torch.no_grad():
                state_tensor = torch.tensor([state], device=device, dtype=torch.float)
                q_values = policy_net(state_tensor)[0]
                best_action_idx = max(possible_actions, key=lambda idx: q_values[idx].item())
            
            solution_path.append(action_mapper.idx_to_action(best_action_idx))
            state, reward, done, info = env.step(best_action_idx)
            total_reward += reward; step_count += 1
        
        if done and "success" in info:
            test_successes += 1
            print(f"✅ Test : SUCCESS")
            print(f"   Reward: {total_reward:.1f}, Steps: {step_count}")
        else:
            print(f"❌ Test : FAILED")
            print(f"   Reward: {total_reward:.1f}, Steps: {step_count}, Reason: {info.get('error', 'Max steps reached')}")
        
        if solution_path:
            print(f"   Placement Path Attempted:")
            for i, step in enumerate(solution_path):
                if step is None:
                    print(f"   - Step {i+1}: Invalid action occurred.")
                    continue
                
                piece_id, orient_idx, pos = step
                print(f"   - Step {i+1}: Place piece {piece_id} at {pos}.")

                base_coords = BASE_PIECES[piece_id]
                rotated_coords = ALL_PIECE_ORIENTATIONS[piece_id][orient_idx]
                
                # 회전 객체 계산
                rotation = calculate_rotation(base_coords, rotated_coords)
                
                if rotation is None:
                    print("     (🔄 Rotation: No rotation)")
                else:
                    # 축-각도 정보 계산 및 출력 (참고용)
                    rot_vec = rotation.as_rotvec()
                    axis = rot_vec / np.linalg.norm(rot_vec)
                    angle_deg = np.rad2deg(np.linalg.norm(rot_vec))
                    axis_angle_str = f"Axis {np.round(axis, 2)} by {angle_deg:.1f}°"
                    
                    # 오일러 각 정보 계산 및 출력 (로봇 적용용)
                    # euler_angles_xyz = rotation.as_euler('xyz', degrees=True)
                    # euler_str = f"Euler(XYZ): X {euler_angles_xyz[0]:.1f}°, Y {euler_angles_xyz[1]:.1f}°, Z {euler_angles_xyz[2]:.1f}°"
                    euler_angles_zyz = rotation.as_euler('zyz', degrees=True)
                    euler_str = f"Euler(ZYZ): Z {euler_angles_zyz[0]:.1f}°, Y {euler_angles_zyz[1]:.1f}°, Z {euler_angles_zyz[2]:.1f}°"
                    
                    print(f"     (🔄 Rotation: {axis_angle_str})")
                    print(f"     (➡️ 로봇 명령: {euler_str})")

                    node.robot_control(user_input, piece_id, euler_angles_zyz, pos)
        
            print("-" * 60)


    rclpy.shutdown()
    node.destroy_node()
    
if __name__ == '__main__':
    main()
