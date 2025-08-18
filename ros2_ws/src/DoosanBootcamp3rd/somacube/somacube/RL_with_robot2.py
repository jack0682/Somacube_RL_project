#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RL_with_robot2.py (Final Synthesized Version for Gazebo Simulation)

Soma Cube assembly script combining a robust refactored structure with intelligent re-grasping logic
for handling complex orientations, ensuring high stability and success rate.
This version is adapted for Gazebo simulation, replacing real hardware interfaces with simulated ones.
"""

import numpy as np
import torch
import torch.nn as nn
import random
from collections import deque, namedtuple
import time
from scipy.spatial.transform import Rotation as R
from od_msg.srv import SrvDepthPosition
import os
import rclpy
from ament_index_python.packages import get_package_share_directory
from rclpy.node import Node
import DR_init
from somacube.onrobot import RG
import sys

# ROS2 메시지 타입 임포트 (시뮬레이션용)
from std_msgs.msg import Float64
from gazebo_msgs.msg import ModelStates

# =======================================================================
# 1. 전역 상수 및 설정
# =======================================================================
PACKAGE_NAME = "somacube"
PACKAGE_PATH = get_package_share_directory(PACKAGE_NAME)
CUBE_MODEL_FILENAME = "best_soma_model.pth"
CUBE_MODEL_PATH = os.path.join(PACKAGE_PATH, "resource", CUBE_MODEL_FILENAME)

ROBOT_ID = "dsr01"
ROBOT_MODEL = "m0609"
VELOCITY, ACC = 60, 60

# 로봇 및 ROS2 초기화
DR_init.__dsr__id = ROBOT_ID
DR_init.__dsr__model = ROBOT_MODEL
rclpy.init()
dsr_node = rclpy.create_node("soma_cube_assembly_controller", namespace=ROBOT_ID)
DR_init.__dsr__node = dsr_node

try:
    from DSR_ROBOT2 import movej, movel, get_current_posx, mwait, get_current_posj
    from DR_common2 import posx, posj
except ImportError as e:
    print(f"치명적 오류: DSR_ROBOT2 임포트 실패: {e}")
    sys.exit()

# --- 동작 관련 상수 정의 ---
HOME = posj(0, 0, 90, 0, 90, 0)
# 재그랩 스테이션 좌표 (백업본에서 가져옴)
REGRASP_STATION_POSE = posx(640, -10.82, 250, 0, 90, 0) 
# 조립 공간 정의 (사용자 제공 좌표 기반)
ASSEMBLY_X_MIN = 424.850
ASSEMBLY_Y_MIN = 3.82
ASSEMBLY_Z_BASE = 12.4
BLOCK_SIZE_MM = 25.0
SAFE_APPROACH_HEIGHT = 100.0 # 안전 접근 높이

# =======================================================================
# 2. 시뮬레이션용 그리퍼 인터페이스
# =======================================================================
class SimulatedRG:
    """가제보 시뮬레이션용 그리퍼 인터페이스 (RG 클래스 대체)"""
    def __init__(self, node: Node, gripper_topic: str = "/gripper_controller/commands"): # 일반적인 토픽명
        self.node = node
        self.publisher = self.node.create_publisher(Float64, gripper_topic, 10)
        self.node.get_logger().info(f"✅ 시뮬레이션 그리퍼 퍼블리셔 초기화: {gripper_topic}")

    def open_gripper(self):
        msg = Float64()
        msg.data = 0.0 # 그리퍼 열림 (0.0 ~ 1.0 범위 가정)
        self.publisher.publish(msg)
        self.node.get_logger().info("   > 시뮬레이션 그리퍼 열림 명령 발행")

    def close_gripper(self):
        msg = Float64()
        msg.data = 1.0 # 그리퍼 닫힘 (0.0 ~ 1.0 범위 가정)
        self.publisher.publish(msg)
        self.node.get_logger().info("   > 시뮬레이션 그리퍼 닫힘 명령 발행")

    def get_status(self): # 실제 그리퍼의 get_status를 흉내냄
        return [False] # 항상 닫힘 완료로 가정 (시뮬레이션 단순화)

# =======================================================================
# 3. 핵심 로봇 제어 클래스 (최종판 - 시뮬레이션용)
# =======================================================================
class RobotController(Node):
    def __init__(self):
        super().__init__("robot_controller_node")
        
        # 시뮬레이션 그리퍼 초기화
        self.gripper = SimulatedRG(self) # 노드 인스턴스 전달

        # 시뮬레이션 인식 (ModelStates 구독)
        self.model_states_sub = self.create_subscription(
            ModelStates,
            '/gazebo/model_states',
            self._model_states_callback,
            10
        )
        self.model_states_data = None
        self.get_logger().info("✅ 로봇 컨트롤러 및 시뮬레이션 인식 초기화 완료")

    def _model_states_callback(self, msg):
        self.model_states_data = msg

    def go_home(self):
        self.get_logger().info("초기 자세로 이동합니다...")
        movej(HOME, vel=VELOCITY, acc=ACC)
        self.gripper.open_gripper()
        mwait()

    def execute_assembly_step(self, piece_id: int, required_rotation: list, grid_position: tuple, physical_grid: np.ndarray) -> bool:
        self.get_logger().info(f"--- 조립 단계 시작: 조각 ID {piece_id} ---")
        
        cam_coords = self._get_piece_position_from_sim(piece_id)
        if not cam_coords:
            self.get_logger().error(f"조각 {piece_id}을(를) 찾지 못해 단계를 중단합니다.")
            return False

        if not self._pick_piece(cam_coords):
            self.get_logger().error(f"조각 {piece_id} 파지에 실패했습니다.")
            return False

        if not self._place_piece(required_rotation, grid_position, physical_grid):
            self.get_logger().error(f"조각 {piece_id} 배치에 실패했습니다.")
            return False
        
        self.get_logger().info(f"--- 조립 단계 성공: 조각 ID {piece_id} ---\
")
        return True

    def _get_piece_position_from_sim(self, piece_id: int) -> Optional[list]:
        """/gazebo/model_states 토픽에서 조각의 3D 좌표를 얻습니다."""
        model_name = f"soma_piece_{piece_id}"
        # ModelStates 메시지가 수신될 때까지 대기
        timeout_sec = 5.0
        start_time = time.time()
        while self.model_states_data is None or model_name not in self.model_states_data.name:
            rclpy.spin_once(self, timeout_sec=0.1) # 콜백 함수 실행을 위해 스핀
            if time.time() - start_time > timeout_sec:
                self.get_logger().error(f"모델 상태 토픽에서 {model_name}을(를) 찾지 못했습니다.")
                return None
        
        try:
            idx = self.model_states_data.name.index(model_name)
            pose = self.model_states_data.pose[idx]
            # Gazebo 모델의 위치는 미터 단위이므로 mm로 변환
            pos_x = pose.position.x * 1000.0
            pos_y = pose.position.y * 1000.0
            pos_z = pose.position.z * 1000.0
            self.get_logger().info(f"   > 시뮬레이션 인식 결과 ({model_name}): [{pos_x:.2f}, {pos_y:.2f}, {pos_z:.2f}]")
            return [pos_x, pos_y, pos_z]
        except ValueError:
            self.get_logger().error(f"모델 상태 토픽에서 {model_name}의 인덱스를 찾을 수 없습니다.")
            return None

    def _pick_piece(self, camera_coords: list) -> bool:
        robot_posx = get_current_posx()[0]
        # 시뮬레이션에서는 T_gripper2cam이 필요 없을 수 있음 (로봇 베이스 기준 좌표를 직접 얻는다고 가정)
        # 여기서는 편의상 0으로 설정하거나, 실제 T_gripper2cam을 로드하여 사용
        # T_gripper2cam = np.load(os.path.join(PACKAGE_PATH, "resource", "T_gripper2cam.npy"))
        # 시뮬레이션에서는 카메라 좌표가 이미 로봇 베이스 기준이라고 가정 (단순화)
        td_coord = np.array(camera_coords) # 이미 로봇 베이스 기준이라고 가정
        
        pick_pose = list(td_coord) + robot_posx[3:]
        pick_pose[2] = max(pick_pose[2] - 5, 2.0)

        approach_pose = pick_pose.copy(); approach_pose[2] += SAFE_APPROACH_HEIGHT
        self.get_logger().info(f"   > 파지 접근: {approach_pose}")
        movel(approach_pose, vel=VELOCITY, acc=ACC); mwait()
        self.get_logger().info(f"   > 파지 실행: {pick_pose}")
        movel(pick_pose, vel=VELOCITY, acc=ACC); mwait()
        self.gripper.close_gripper(); time.sleep(1.0)
        movel(approach_pose, vel=VELOCITY, acc=ACC); mwait()
        return True

    def _place_piece(self, required_rotation: list, grid_position: tuple, physical_grid: np.ndarray) -> bool:
        # 재그랩 필요성 판단 (ZYZ 오일러 각 중 하나라도 45도 이상 변하면 재그랩 수행)
        if any(abs(angle) > 45 for angle in required_rotation):
            self.get_logger().info("   > 복잡한 회전 필요. 재그랩 시퀀스를 실행합니다.")
            if not self._perform_regrasp(required_rotation):
                return False
        # 최종 목표 자세 계산
        target_xyz = self._map_grid_to_physical_coords(grid_position)
        current_orientation = get_current_posx()[0][3:]
        target_pose = target_xyz + current_orientation # 재그랩 후에는 추가 회전이 필요 없음
        safe_target_pose = self._find_safe_pose(target_pose)
        if not safe_target_pose: return False
        # 안전한 접근 경로 계산
        max_z_level = np.max(physical_grid) if np.any(physical_grid) else 0
        safe_approach_z = (max_z_level * BLOCK_SIZE_MM) + ASSEMBLY_Z_BASE + SAFE_APPROACH_HEIGHT
        pre_place_pose = safe_target_pose.copy()
        pre_place_pose[2] = max(pre_place_pose[2] + SAFE_APPROACH_HEIGHT, safe_approach_z)
        # 배치 실행
        self.get_logger().info("   > 최종 배치 위치로 이동...")
        movej(pre_place_pose, vel=VELOCITY, acc=ACC, sol=0); mwait()
        movel(safe_target_pose, vel=VELOCITY, acc=ACC); mwait()
        self.gripper.open_gripper(); time.sleep(1.0)
        self.get_logger().info("   > 안전하게 후퇴...")
        movel(pre_place_pose, vel=VELOCITY, acc=ACC); mwait()
        return True

    def _perform_regrasp(self, required_rotation: list) -> bool:
        self.get_logger().info("     > 재그랩 스테이션으로 이동...")
        current_pose = get_current_posx()[0]
        # 현재 방향을 유지하며 재그랩 스테이션으로 이동
        movej(REGRASP_STATION_POSE[:3] + current_pose[3:], vel=VELOCITY, acc=ACC); mwait()
        # 조각 내려놓기
        movel(posx(REGRASP_STATION_POSE[0], REGRASP_STATION_POSE[1], REGRASP_STATION_POSE[2] + 5, current_pose[3][0], current_pose[3][1], current_pose[3][2]), vel=VELOCITY, acc=ACC); mwait()
        self.gripper.open_gripper(); time.sleep(1.0)
        movel(REGRASP_STATION_POSE, vel=VELOCITY, acc=ACC); mwait()
        # 최종 목표 방향으로 그리퍼 방향 변경
        self.get_logger().info("     > 그리퍼 방향 재정렬...")
        final_orientation_pose = self._apply_rotation(REGRASP_STATION_POSE, required_rotation)
        movej(final_orientation_pose, vel=VELOCITY, acc=ACC); mwait()
        # 재파지
        self.get_logger().info("     > 재파지 실행...")
        movel(posx(final_orientation_pose[0], final_orientation_pose[1], final_orientation_pose[2] + 5, final_orientation_pose[3][0], final_orientation_pose[3][1], final_orientation_pose[3][2]), vel=VELOCITY, acc=ACC); mwait()
        self.gripper.close_gripper(); time.sleep(1.0)
        movel(final_orientation_pose, vel=VELOCITY, acc=ACC); mwait()
        return True

    def _map_grid_to_physical_coords(self, grid_pos: tuple) -> list:
        x, y, z = grid_pos
        target_x = ASSEMBLY_X_MIN + (x * BLOCK_SIZE_MM) + (BLOCK_SIZE_MM / 2)
        target_y = ASSEMBLY_Y_MIN + (y * BLOCK_SIZE_MM) + (BLOCK_SIZE_MM / 2)
        target_z = ASSEMBLY_Z_BASE + (z * BLOCK_SIZE_MM) + (BLOCK_SIZE_MM / 2)
        return [target_x, target_y, target_z]

    def _apply_rotation(self, start_pose: list, zyz_delta: list) -> list:
        try:
            r_start = R.from_euler('zyz', start_pose[3:], degrees=True)
            r_delta = R.from_euler('zyz', zyz_delta, degrees=True)
            r_final = r_start * r_delta
            return start_pose[:3] + r_final.as_euler('zyz', degrees=True).tolist()
        except Exception as e:
            self.get_logger().warning(f"회전 적용 오류: {e}"); return start_pose

    def _find_safe_pose(self, target_pose: list) -> Optional[list]:
        safe_pose = target_pose.copy()
        ry = safe_pose[4]
        if abs(abs(ry) - 90.0) < 2.0:
            self.get_logger().warning(f"특이점 감지: Ry={ry:.1f}°. 자세를 미세 조정합니다.")
            safe_pose[4] = 88.0 if ry > 0 else -88.0
        is_lying_down = abs(abs(safe_pose[4]) - 90) < 15
        is_roll_problematic = (abs(safe_pose[5]) < 15 or abs(abs(safe_pose[5])) > 165)
        if is_lying_down and is_roll_problematic:
            self.get_logger().warning(f"충돌 위험 감지: 그리퍼 롤 각도를 90도로 강제 조정합니다.")
            safe_pose[5] = 90.0
        return safe_pose

# =======================================================================
# 4. 소마큐브 환경 및 DQN 모델
# =======================================================================
BASE_PIECES = {0:np.array([[0,0,0],[1,0,0],[0,1,0]]),1:np.array([[0,0,0],[1,0,0],[2,0,0],[2,1,0]]),2:np.array([[0,0,0],[1,0,0],[2,0,0],[1,1,0]]),3:np.array([[0,0,0],[1,0,0],[1,1,0],[2,1,0]]),4:np.array([[0,0,0],[0,1,0],[1,1,0],[1,1,1]]),5:np.array([[0,0,0],[1,0,0],[1,1,0],[1,1,1]]),6:np.array([[0,0,0],[1,0,0],[0,1,0],[0,0,1]])}

def get_all_rotations():
    all_rots = {}
    mats = [R.from_euler('x', 90, degrees=True).as_matrix(), R.from_euler('y', 90, degrees=True).as_matrix()]
    for i, p in BASE_PIECES.items():
        rots = set()
        q = [p]; visited = {tuple(map(tuple, p))}; head = 0
        while head < len(q):
            curr = q[head]; head += 1
            rots.add(tuple(map(tuple, curr - curr.min(axis=0))))
            for mat in mats:
                new_p = np.dot(curr, mat).astype(int)
                if tuple(map(tuple, new_p)) not in visited: q.append(new_p); visited.add(tuple(map(tuple, new_p)))
        all_rots[i] = [np.array(r) for r in rots]
    return all_rots

ALL_PIECE_ORIENTATIONS = get_all_rotations()

class ActionMapper:
    def __init__(self):
        self.action_to_index={}; self.index_to_action={}; idx=0
        for piece_id in range(7):
            for orient_idx in range(len(ALL_PIECE_ORIENTATIONS[piece_id])):
                for x,y,z in np.ndindex(3,3,3):
                    action=(piece_id,orient_idx,(x,y,z)); self.action_to_index[action]=idx; self.index_to_action[idx]=action; idx+=1
        self.total_actions=idx

class SomaCubeEnv:
    def __init__(self, action_mapper):
        self.grid_shape=(3,3,3); self.action_mapper=action_mapper; self.reset()
    def reset(self):
        self.grid=np.zeros(self.grid_shape,dtype=int); self.pieces_to_place=random.sample(list(range(7)),7); self.current_piece_idx=self.pieces_to_place.pop(0); self.done=False; return self._get_state()
    def _get_state(self):
        state=np.zeros(27+7); state[:27]=self.grid.flatten(); state[27+self.current_piece_idx]=1; return state
    def _is_valid_placement(self, piece_coords, pos):
        for x,y,z in piece_coords:
            abs_pos=(pos[0]+x, pos[1]+y, pos[2]+z)
            if not all(0<=c<3 for c in abs_pos) or self.grid[abs_pos]!=0: return False
        return True
    def step(self, action_idx):
        action=self.action_mapper.index_to_action.get(action_idx)
        if action is None or action[0]!=self.current_piece_idx: return self._get_state(),-10.0,True
        _,orient_idx,pos=action
        piece_coords=ALL_PIECE_ORIENTATIONS[self.current_piece_idx][orient_idx]
        if not self._is_valid_placement(piece_coords,pos): return self._get_state(),-5.0,True
        for x,y,z in piece_coords: self.grid[pos[0]+x,pos[1]+y,pos[2]+z]=self.current_piece_idx+1
        if not self.pieces_to_place: self.done=True; return self._get_state(),100.0,True
        self.current_piece_idx=self.pieces_to_place.pop(0)
        return self._get_state(),1.0,False

class DQN(nn.Module):
    def __init__(self, state_size, action_size):
        super(DQN, self).__init__()
        self.network = nn.Sequential(
            nn.Linear(state_size, 512),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(512, 512),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Linear(256, action_size)
        )
    def forward(self, x):
        return self.network(x.float())

# =======================================================================
# 4. 조립 공정 관리자 및 메인 실행
# =======================================================================
class AssemblyManager:
    def __init__(self, controller: RobotController):
        self.controller = controller
        self.action_mapper = ActionMapper()
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.policy_net = DQN(34, self.action_mapper.total_actions).to(self.device)
        self.physical_grid = np.zeros((3,3,3), dtype=int)
        self._load_model()

    def _load_model(self):
        try:
            self.policy_net.load_state_dict(torch.load(CUBE_MODEL_PATH, map_location=self.device)); self.policy_net.eval()
            print("✅ DQN 모델 로딩 성공.")
        except FileNotFoundError: print(f"❌ 모델 파일을 찾을 수 없습니다: '{CUBE_MODEL_PATH}'."); sys.exit(1)

    def generate_solution(self) -> Optional[list]:
        print("🧠 DQN으로 조립 해법 생성 시작...")
        env = SomaCubeEnv(self.action_mapper)
        state = env.reset(); solution_path = []
        while not env.done:
            with torch.no_grad(): q_values = self.policy_net(torch.tensor([state], device=self.device))
            valid_actions = [a for a in range(self.action_mapper.total_actions) if env.action_mapper.index_to_action[a][0] == env.current_piece_idx]
            if not valid_actions: return None
            best_action_idx = max(valid_actions, key=lambda a: q_values[0, a].item())
            action = env.action_mapper.index_to_action[best_action_idx]
            solution_path.append(action)
            state, _, _, = env.step(best_action_idx)
        print(f"✅ 해법 생성 완료. 총 {len(solution_path)} 단계.")
        return solution_path

    def calculate_rotation(self, piece_id, orient_idx):
        base_coords = BASE_PIECES[piece_id]
        rotated_coords = ALL_PIECE_ORIENTATIONS[piece_id][orient_idx]
        try:
            rotation, _ = R.align_vectors(rotated_coords - rotated_coords.mean(axis=0), base_coords - base_coords.mean(axis=0))
            return rotation.as_euler('zyz', degrees=True).tolist()
        except: return [0,0,0]

    def run_assembly(self):
        solution = self.generate_solution()
        if not solution: print("해법 생성에 실패하여 조립을 시작할 수 없습니다."); return

        print("="*50 + "\n🚀 생성된 해법으로 로봇 조립을 시작합니다.")
        for i, (p_id, o_idx, g_pos) in enumerate(solution): print(f"  - 단계 {i+1}: 조각 {p_id} @ {g_pos} (방향 {o_idx})")
        print("="*50)

        if input("조립을 시작하시겠습니까? (y/n): ").lower() != 'y': print("조립을 취소했습니다."); return

        self.controller.go_home()
        for i, (piece_id, orient_idx, grid_pos) in enumerate(solution):
            rotation = self.calculate_rotation(piece_id, orient_idx)
            success = self.controller.execute_assembly_step(piece_id, rotation, grid_pos, self.physical_grid)
            if not success:
                print(f"!!!!!!!! 조립 실패: 단계 {i+1}에서 중단되었습니다. !!!!!!!!"); break
            # 성공 시, 물리적 그리드 상태 업데이트
            piece_coords = ALL_PIECE_ORIENTATIONS[piece_id][orient_idx]
            for x,y,z in piece_coords:
                self.physical_grid[grid_pos[0]+x, grid_pos[1]+y, grid_pos[2]+z] = piece_id + 1
        else: print("🎉🎉🎉 모든 조립 단계가 성공적으로 완료되었습니다! 🎉🎉🎉")
        self.controller.go_home()

def main():
    try:
        controller = RobotController()
        assembly_manager = AssemblyManager(controller)
        assembly_manager.run_assembly()
    except Exception as e:
        print(f"프로그램 실행 중 심각한 오류 발생: {e}")
    finally:
        print("프로그램을 종료합니다.")
        if rclpy.ok():
            rclpy.shutdown()
            dsr_node.destroy_node()

if __name__ == '__main__':
    main()
