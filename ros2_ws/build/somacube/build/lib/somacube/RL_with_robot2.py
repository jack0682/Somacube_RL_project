#!/usr/bin/env python3
# -*- coding: utf-8 -*-"""
"""
통합 소마큐브 조립 스크립트

기존의 분산된 파이썬 스크립트들을 하나의 파일로 통합하고,
사용자 선택에 따라 다양한 모드(해법, 인식, 그랩)를 지원하도록 리팩토링된 버전입니다.

포함된 기능:
- 로봇 제어 및 ROS2 인터페이스
- 소마큐브 퍼즐 정의 및 상태 관리
- 강화학습(DQN) 기반 해법 생성
- OpenAI API(GPT-4-Omni) 기반 동적 해법 생성
- OpenAI API(GPT-4-Omni Vision) 기반 장면 분석 및 객체 인식 (VLM)
- 기존 및 AI 기반 적응형 그랩 최적화 (특이점 회피 포함)
- 전체 조립 프로세스 관리
"""

# =======================================================================
# 0. 모듈 임포트
# =======================================================================
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
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Union
import json
from datetime import datetime
import base64
from io import BytesIO
from PIL import Image
import cv2
from openai import OpenAI

# =======================================================================
# 1. 전역 상수 및 설정
# =======================================================================

# !!! OpenAI API 키를 여기에 직접 입력하세요. !!!
OPENAI_API_KEY = "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"

PACKAGE_NAME = "somacube"
PACKAGE_PATH = get_package_share_directory(PACKAGE_NAME)
CUBE_MODEL_FILENAME = "best_soma_model.pth"
CUBE_MODEL_PATH = os.path.join(PACKAGE_PATH, "resource", CUBE_MODEL_FILENAME)

ROBOT_ID = "dsr01"
ROBOT_MODEL = "m0609"
VELOCITY, ACC = 60, 60
HOME = [0, 0, 90, 0, 90, 0]

STACKING_BASE_X_MIN = 424.850
STACKING_BASE_X_MAX = 499.9
STACKING_BASE_Y_MIN = 3.82
STACKING_BASE_Y_MAX = 78.830
STACKING_BASE_Z = 12.4
BLOCK_SIZE_MM = 25.0

DR_init.__dsr__id = ROBOT_ID
DR_init.__dsr__model = ROBOT_MODEL
rclpy.init()
dsr_node = rclpy.create_node("soma_cube_robot_controller", namespace=ROBOT_ID)
DR_init.__dsr__node = dsr_node

try:
    from DSR_ROBOT2 import movej, movel, get_current_posx, mwait, get_current_posj
    from DR_common2 import posx
except ImportError as e:
    print(f"치명적 오류: DSR_ROBOT2 임포트 실패: {e}")
    sys.exit()

GRIPPER_NAME = "rg2"
TOOLCHANGER_IP = "192.168.1.1"
TOOLCHANGER_PORT = "502"
gripper = RG(GRIPPER_NAME, TOOLCHANGER_IP, TOOLCHANGER_PORT)

# =======================================================================
# 2. OpenAI 연동 시스템 (VLM, Solver, Grasp Optimizer)
# =======================================================================
class OpenAIVisionSystem:
    def __init__(self, api_key: str = OPENAI_API_KEY, model: str = "gpt-4-omni"):
        self.api_key = api_key
        self.model = model
        if not self.api_key or self.api_key == "YOUR_API_KEY_HERE": raise ValueError("OpenAI API 키를 설정해야 합니다.")
        self.client = OpenAI(api_key=self.api_key)
        print(f"🎥 OpenAI Vision 시스템 초기화 완료 (Model: {self.model})")

    def encode_image_base64(self, image_input: Union[str, np.ndarray, Image.Image]) -> str:
        try:
            if isinstance(image_input, str):
                with open(image_input, "rb") as f: return base64.b64encode(f.read()).decode('utf-8')
            elif isinstance(image_input, np.ndarray):
                img = cv2.cvtColor(image_input, cv2.COLOR_BGR2RGB) if len(image_input.shape) == 3 else image_input
                pil_img = Image.fromarray(img)
                buffer = BytesIO()
                pil_img.save(buffer, format="PNG")
                return base64.b64encode(buffer.getvalue()).decode('utf-8')
            elif isinstance(image_input, Image.Image):
                buffer = BytesIO()
                image_input.save(buffer, format="PNG")
                return base64.b64encode(buffer.getvalue()).decode('utf-8')
            raise ValueError("지원하지 않는 이미지 형식")
        except Exception as e:
            print(f"❌ 이미지 인코딩 오류: {e}"); return None

    def analyze_scene_for_soma_cube(self, image_input: Union[str, np.ndarray, Image.Image]) -> Dict:
        base64_image = self.encode_image_base64(image_input)
        if not base64_image: return {"error": "이미지 인코딩 실패"}
        system_prompt = "You are a computer vision expert for robotic Soma Cube assembly. Analyze the image and return a JSON object with detected pieces, their 3D positions, orientations, and grasp points."
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": [{"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}]},
                ],
                temperature=0.1, max_tokens=3000, response_format={"type": "json_object"}
            )
            result = json.loads(response.choices[0].message.content.strip())
            print(f"👁️ VLM 블록 감지: {len(result.get('detected_pieces', []))}개 감지")
            return result
        except Exception as e:
            print(f"❌ VLM 분석 오류: {e}"); return {"error": str(e)}

class OpenAISomaCubeSolver:
    def __init__(self, api_key: str = OPENAI_API_KEY, model: str = "gpt-4-omni", max_retries: int = 3):
        self.api_key = api_key
        self.model = model
        self.max_retries = max_retries
        if not self.api_key or self.api_key == "YOUR_API_KEY_HERE": raise ValueError("OpenAI API 키를 설정해야 합니다.")
        self.client = OpenAI(api_key=self.api_key)
        self.system_prompt = "You are an expert 3D puzzle solver for Soma Cube. Generate a complete solution as a JSON object: {\"solution\": [{\"piece_id\": int, \"orientation\": int, \"position\": [x,y,z]}, ...] }"
        print(f"🧠 OpenAI 솔버 초기화 완료 (Model: {self.model})")

    def solve_soma_cube(self) -> Optional[List[Tuple]]:
        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "system", "content": self.system_prompt}, {"role": "user", "content": "Generate a complete Soma Cube solution."}],
                    temperature=0.3, max_tokens=2000, response_format={"type": "json_object"}
                )
                solution_data = json.loads(response.choices[0].message.content.strip())['solution']
                solution = [(s["piece_id"], s["orientation"], tuple(s["position"])) for s in solution_data]
                if self._validate_solution(solution):
                    print("✅ 유효한 해법 생성 성공!"); return solution
            except Exception as e:
                print(f"❌ API 호출 또는 해법 검증 오류 (시도 {attempt + 1}): {e}")
        return None

    def _validate_solution(self, solution: List[Tuple]) -> bool:
        if len(solution) != 7: return False
        grid = np.zeros((3, 3, 3), dtype=int)
        used_pieces = set()
        for piece_id, orient_idx, pos in solution:
            if piece_id in used_pieces: return False
            used_pieces.add(piece_id)
            if not (0 <= piece_id <= 6 and 0 <= orient_idx < len(ALL_PIECE_ORIENTATIONS[piece_id])): return False
            piece_coords = ALL_PIECE_ORIENTATIONS[piece_id][orient_idx]
            for x, y, z in piece_coords:
                abs_pos = (pos[0] + x, pos[1] + y, pos[2] + z)
                if not all(0 <= c < 3 for c in abs_pos) or grid[abs_pos] != 0: return False
                grid[abs_pos] = piece_id + 1
        return np.all(grid > 0)

class OpenAIGraspOptimizer:
    def __init__(self, api_key: str = OPENAI_API_KEY, model: str = "gpt-4-omni"):
        self.api_key = api_key
        self.model = model
        if not self.api_key or self.api_key == "YOUR_API_KEY_HERE": raise ValueError("OpenAI API 키를 설정해야 합니다.")
        self.client = OpenAI(api_key=self.api_key)
        print(f"🤖 OpenAI 그랩 최적화 시스템 초기화 완료 (Model: {self.model})")

    def choose_best_orientation_ai(self, start_pose: List[float], zyz_base_delta: List[float]) -> List[float]:
        system_prompt = "You are a robot motion planner. Choose the optimal gripper orientation to minimize collision. Return JSON: {\"optimal_pose\": [X,Y,Z,Rx,Ry,Rz]}"
        user_prompt = f"Optimize gripper orientation. Start pose: {start_pose}, Rotation delta: {zyz_base_delta}"
        try:
            response = self.client.chat.completions.create(
                model=self.model, messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
                temperature=0.1, response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content.strip())["optimal_pose"]
        except Exception as e:
            print(f"❌ AI 자세 최적화 오류: {e}, 폴백 사용"); return apply_rotation_manually(start_pose, zyz_base_delta)

    def detect_and_avoid_singularities_ai(self, current_joints: List[float], target_pose: List[float]) -> Dict:
        system_prompt = "You are an expert robotics engineer for singularity avoidance. Analyze the target pose and suggest adjustments. Return JSON: {\"safe_pose\": [X,Y,Z,Rx,Ry,Rz], \"reasoning\": \"...\"}"
        user_prompt = f"Analyze for singularities. Current joints: {current_joints}, Target pose: {target_pose}. Propose a safe pose."
        try:
            response = self.client.chat.completions.create(
                model=self.model, messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
                temperature=0.1, response_format={"type": "json_object"}
            )
            result = json.loads(response.choices[0].message.content.strip())
            print(f"🔍 AI 특이점 분석: {result.get('reasoning', '이유 없음')}"); return result
        except Exception as e:
            print(f"❌ AI 특이점 분석 오류: {e}, 폴백 사용"); return self._fallback_singularity_detection(target_pose)

    def _fallback_singularity_detection(self, target_pose: List[float]) -> Dict:
        safe_pose = target_pose.copy()
        if abs(safe_pose[4] - 90.0) < 1.0: safe_pose[4] = 89.0
        elif abs(safe_pose[4] + 90.0) < 1.0: safe_pose[4] = -89.0
        return {"safe_pose": safe_pose, "reasoning": "Basic singularity detection fallback"}

# =======================================================================
# 3. 로봇 및 조립 관리 시스템
# =======================================================================
BASE_PIECES = {
    0: np.array([[0,0,0], [1,0,0], [0,1,0]]), # V
    1: np.array([[0,0,0], [1,0,0], [2,0,0], [2,1,0]]), # L
    2: np.array([[0,0,0], [1,0,0], [2,0,0], [1,1,0]]), # T
    3: np.array([[0,0,0], [1,0,0], [1,1,0], [2,1,0]]), # Z
    4: np.array([[0,0,0], [0,1,0], [1,1,0], [1,1,1]]), # A
    5: np.array([[0,0,0], [1,0,0], [1,1,0], [1,1,1]]), # B
    6: np.array([[0,0,0], [1,0,0], [0,1,0], [0,0,1]]), # P
}

def get_all_rotations():
    all_rotations = {}
    rotation_matrices = [
        np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0]]), # x
        np.array([[0, 0, 1], [0, 1, 0], [-1, 0, 0]]), # y
        np.array([[0, -1, 0], [1, 0, 0], [0, 0, 1]])  # z
    ]
    for i, piece in BASE_PIECES.items():
        seen = set()
        unique_orientations = []
        q = [piece]
        p_norm = piece - piece.min(axis=0)
        p_tuple = tuple(sorted(map(tuple, p_norm)))
        seen.add(p_tuple)
        unique_orientations.append(piece)
        head = 0
        while head < len(q):
            curr = q[head]; head += 1
            for rot_mat in rotation_matrices:
                new_p = np.dot(curr, rot_mat)
                new_p_norm = new_p - new_p.min(axis=0)
                new_p_tuple = tuple(sorted(map(tuple, new_p_norm)))
                if new_p_tuple not in seen:
                    seen.add(new_p_tuple)
                    unique_orientations.append(new_p)
                    q.append(new_p)
        all_rotations[i] = [p - p.min(axis=0) for p in unique_orientations]
    return all_rotations

ALL_PIECE_ORIENTATIONS = get_all_rotations()

def apply_rotation_manually(start_pose, zyz_delta):
    try:
        r_start = R.from_euler('zyz', start_pose[3:], degrees=True)
        r_delta = R.from_euler('zyz', zyz_delta, degrees=True)
        return start_pose[:3] + (r_start * r_delta).as_euler('zyz', degrees=True).tolist()
    except Exception as e:
        print(f"회전 적용 오류: {e}"); return start_pose

class GraspingSystem:
    def __init__(self, use_openai: bool = False):
        self.use_openai = use_openai
        if self.use_openai:
            try: self.optimizer = OpenAIGraspOptimizer()
            except Exception as e: print(f"❌ OpenAI 그랩 초기화 실패: {e}"); self.use_openai = False

    def choose_best_orientation(self, start_pose: List[float], zyz_base_delta: List[float]) -> List[float]:
        if self.use_openai: return self.optimizer.choose_best_orientation_ai(start_pose, zyz_base_delta)
        pose1 = apply_rotation_manually(start_pose, zyz_base_delta)
        delta2 = zyz_base_delta.copy(); delta2[2] += 90.0
        pose2 = apply_rotation_manually(start_pose, delta2)
        r1 = R.from_euler('zyz', pose1[3:], degrees=True); v1 = r1.apply([1,0,0])
        r2 = R.from_euler('zyz', pose2[3:], degrees=True); v2 = r2.apply([1,0,0])
        return pose1 if abs(v1[2]) <= abs(v2[2]) else pose2

    def correct_pose(self, target_pose: List[float]) -> List[float]:
        if self.use_openai:
            try:
                joints = get_current_posj()
                result = self.optimizer.detect_and_avoid_singularities_ai(joints, target_pose)
                if result and "safe_pose" in result:
                    print("🧠 AI가 제안한 특이점 회피 자세를 적용합니다."); return result["safe_pose"]
            except Exception as e:
                print(f"❌ AI 특이점 회피 중 오류: {e}, 기본 로직으로 대체")
        
        ry, rz_prime = target_pose[4], target_pose[5]
        is_lying = abs(ry - 90) < 15 or abs(ry + 90) < 15
        is_problem = (abs(rz_prime) < 15 or abs(rz_prime - 180) < 15 or abs(rz_prime + 180) < 15)
        if is_lying and is_problem:
            corrected = target_pose.copy(); corrected[5] = 90.0; return corrected
        return target_pose

class RobotController(Node):
    def __init__(self, use_openai_grasping=False, use_vlm_perception=False):
        super().__init__("soma_cube_robot_controller")
        self.use_vlm = use_vlm_perception
        self.grasping_system = GraspingSystem(use_openai=use_openai_grasping)
        if self.use_vlm:
            try: self.vlm_system = OpenAIVisionSystem()
            except Exception as e: self.get_logger().error(f"❌ VLM 초기화 실패: {e}"); self.use_vlm = False
        if not self.use_vlm: self._initialize_depth_service_client()
        self.init_robot()

    def _initialize_depth_service_client(self):
        self.depth_client = self.create_client(SrvDepthPosition, "/get_3d_position")
        if not self.depth_client.wait_for_service(timeout_sec=3.0):
            self.get_logger().error("Depth Position Service 사용 불가")
        else: self.get_logger().info("✅ Depth Position Service 클라이언트 초기화됨")

    def capture_camera_image(self) -> Optional[np.ndarray]:
        self.get_logger().warning("카메라 캡처 기능 미구현. 더미 이미지를 사용합니다.")
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(img, f"{time.time():.2f}", (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2)
        return img

    def get_piece_position(self, piece_id: int) -> Optional[List[float]]:
        if self.use_vlm:
            self.get_logger().info(f"👁️ VLM으로 조각 {piece_id} 위치 검색...")
            img = self.capture_camera_image()
            if img is None: return None
            analysis = self.vlm_system.analyze_scene_for_soma_cube(img)
            if analysis and "detected_pieces" in analysis:
                for p in analysis["detected_pieces"]:
                    if p.get("piece_id") == piece_id:
                        pos_dict = p.get("estimated_3d_position", {})
                        return [pos_dict.get('x'), pos_dict.get('y'), pos_dict.get('z')]
            self.get_logger().error(f"VLM이 조각 {piece_id}을(를) 찾지 못함"); return None
        else:
            self.get_logger().info(f"📷 Depth Service로 조각 {piece_id} 위치 검색...")
            req = SrvDepthPosition.Request(); req.target = str(piece_id)
            future = self.depth_client.call_async(req)
            rclpy.spin_until_future_complete(self, future)
            if future.result() and sum(future.result().depth_position) > 0: return future.result().depth_position.tolist()
            self.get_logger().error(f"Depth Service가 조각 {piece_id}을(를) 찾지 못함"); return None

    def execute_pick_and_place(self, piece_id, rotation, grid_pos):
        cam_coords = self.get_piece_position(piece_id)
        if cam_coords is None or any(c is None for c in cam_coords): 
            self.get_logger().error(f"조각 {piece_id}의 유효한 좌표를 얻지 못했습니다."); return
        
        robot_posx = get_current_posx()[0]
        T_gripper2cam = np.load(os.path.join(PACKAGE_PATH, "resource", "T_gripper2camera.npy"))
        R_base2gripper = R.from_euler("ZYZ", robot_posx[3:], degrees=True).as_matrix()
        T_base2gripper = np.eye(4); T_base2gripper[:3,:3] = R_base2gripper; T_base2gripper[:3,3] = robot_posx[:3]
        td_coord = (T_base2gripper @ T_gripper2cam @ np.append(np.array(cam_coords), 1))[:3]
        
        pick_up_pos = list(td_coord) + robot_posx[3:]
        self.get_logger().info(f"계산된 픽업 위치: {pick_up_pos}")

        movel(pick_up_pos, vel=VELOCITY, acc=ACC); mwait()
        gripper.close_gripper(); time.sleep(1.0)
        movel(posx(pick_up_pos[0], pick_up_pos[1], pick_up_pos[2] + 300, pick_up_pos[3], pick_up_pos[4], pick_up_pos[5]), vel=VELOCITY, acc=ACC)

        place_xyz = self.map_grid_to_physical_coords(grid_pos)
        base_pose = place_xyz + get_current_posx()[0][3:]

        print("Phase 3: 그랩 최적화")
        optimized_pose = self.grasping_system.choose_best_orientation(base_pose, rotation)
        final_target_pose = self.grasping_system.correct_pose(optimized_pose)
        print(f"최종 목표 자세: {final_target_pose}")

        approach_pose = final_target_pose.copy(); approach_pose[2] += 80
        movel(approach_pose, vel=VELOCITY, acc=ACC); mwait()
        movel(final_target_pose, vel=VELOCITY, acc=ACC); mwait()
        gripper.open_gripper(); mwait()
        movel(approach_pose, vel=VELOCITY, acc=ACC); mwait()
        self.init_robot()

    def map_grid_to_physical_coords(self, grid_pos):
        x, y, z = grid_pos
        return [
            STACKING_BASE_X_MIN + (x * BLOCK_SIZE_MM) + (BLOCK_SIZE_MM / 2),
            STACKING_BASE_Y_MIN + (y * BLOCK_SIZE_MM) + (BLOCK_SIZE_MM / 2),
            STACKING_BASE_Z + (z * BLOCK_SIZE_MM) + (BLOCK_SIZE_MM / 2)
        ]

    def init_robot(self):
        movej(HOME, vel=VELOCITY, acc=ACC); gripper.open_gripper(); mwait()

class AssemblyManager:
    def __init__(self, robot_controller):
        self.robot_controller = robot_controller
        self.solution_path = []

    def run(self, solution_path):
        self.solution_path = solution_path
        print(f"=== 소마큐브 전체 조립 시작 ({len(self.solution_path)} 단계) ===")
        for i, (p_id, o_idx, g_pos) in enumerate(self.solution_path):
            print(f"--- 단계 {i + 1}/{len(self.solution_path)}: 조각 {p_id} ---")
            base = BASE_PIECES[p_id]
            rotated = ALL_PIECE_ORIENTATIONS[p_id][o_idx]
            rot_obj = calculate_rotation(base, rotated)
            euler = rot_obj.as_euler('zyz', degrees=True).tolist() if rot_obj else [0,0,0]
            try:
                self.robot_controller.execute_pick_and_place(p_id, euler, g_pos)
                print(f"✅ 단계 {i + 1} 성공")
            except Exception as e: print(f"❌ 단계 {i + 1} 실패: {e}"); return False
        print("🎉 소마큐브 조립 완료!"); return True

def calculate_rotation(base, rotated):
    try: return R.align_vectors(rotated - rotated.mean(axis=0), base - base.mean(axis=0))[0]
    except: return None

class ActionMapper:
    def __init__(self):
        self.action_to_index = {}; self.index_to_action = {}
        idx = 0
        for piece_id in range(7):
            for orient_idx in range(len(ALL_PIECE_ORIENTATIONS[piece_id])):
                for x in range(3):
                    for y in range(3):
                        for z in range(3):
                            action = (piece_id, orient_idx, (x, y, z))
                            self.action_to_index[action] = idx
                            self.index_to_action[idx] = action
                            idx += 1
        self.total_actions = idx

class SomaCubeEnv:
    def __init__(self, action_mapper):
        self.grid_shape = (3, 3, 3); self.action_mapper = action_mapper; self.reset()
    def reset(self):
        self.grid = np.zeros(self.grid_shape, dtype=int); self.pieces_to_place = random.sample(list(range(7)), 7); self.current_piece_idx = self.pieces_to_place.pop(0); self.done = False; return self._get_state()
    def _get_state(self):
        state = np.zeros(27 + 7); state[:27] = self.grid.flatten(); state[27 + self.current_piece_idx] = 1; return state
    def _is_valid_placement(self, piece_coords, pos):
        for x, y, z in piece_coords:
            abs_x, abs_y, abs_z = pos[0] + x, pos[1] + y, pos[2] + z
            if not (0 <= abs_x < 3 and 0 <= abs_y < 3 and 0 <= abs_z < 3) or self.grid[abs_x, abs_y, abs_z] != 0: return False
        return True

class DQN(nn.Module):
    def __init__(self, state_size, action_size):
        super(DQN, self).__init__(); self.network = nn.Sequential(nn.Linear(state_size, 512), nn.ReLU(), nn.Linear(512, 256), nn.ReLU(), nn.Linear(256, action_size))
    def forward(self, x): return self.network(x.float())

# =======================================================================
# 4. 메인 실행 블록
# =======================================================================
def main():
    print("+"*60 + "\n통합 소마큐브 로봇 조립 시스템\n" + "+"*60)

    solver_choice = input("\n🤖 [1/3] 해법 생성 방식 (1: DQN, 2: OpenAI): ").strip()
    perception_choice = input("\n👁️ [2/3] 인식 시스템 (1: Depth Service, 2: VLM): ").strip()
    grasping_choice = input("\n🦾 [3/3] 그랩 시스템 (1: 규칙 기반, 2: OpenAI): ").strip()
    print("="*60)

    use_openai_solver = (solver_choice == "2")
    use_vlm = (perception_choice == "2")
    use_openai_grasping = (grasping_choice == "2")


    try:
        controller = RobotController(use_openai_grasping=use_openai_grasping, use_vlm_perception=use_vlm)
    except ValueError as e:
        print(f"초기화 오류: {e}")
        print("스크립트 상단의 OPENAI_API_KEY 변수에 유효한 키를 입력했는지 확인하세요.")
        return

    solution = None
    if use_openai_solver:
        try: solution = OpenAISomaCubeSolver().solve_soma_cube()
        except Exception as e: print(f"❌ OpenAI 해법 생성 실패: {e}")
    
    if solution is None:
        print("🤖 DQN 모델로 해법 생성 중...")
        action_mapper = ActionMapper()
        env = SomaCubeEnv(action_mapper)
        policy_net = DQN(34, action_mapper.total_actions).to("cpu")
        try:
            policy_net.load_state_dict(torch.load(CUBE_MODEL_PATH, map_location="cpu")),
            policy_net.eval()
            state = env.reset(); solution = []
            while not env.done and len(solution) < 7:
                possible = env.get_possible_actions()
                if not possible: break
                with torch.no_grad():
                    q_vals = policy_net(torch.tensor([state], dtype=torch.float))
                    best_idx = max(possible, key=lambda i: q_vals[0, i].item())
                solution.append(action_mapper.idx_to_action(best_idx))
                state, _, _, _ = env.step(best_idx)
            print("✅ DQN 해법 생성 완료!")
        except FileNotFoundError:
            print(f"❌ 모델 파일 없음: '{CUBE_MODEL_PATH}'")

    if solution:
        print("="*60 + "\n🚀 생성된 해법으로 로봇 조립을 시작합니다.\n" + "="*60)
        for i, step in enumerate(solution): print(f"  - 단계 {i+1}: 조각 {step[0]} @ {step[2]} (방향 {step[1]})")
        if input("\n조립을 시작하시겠습니까? (y/n): ").lower() == 'y':
            AssemblyManager(controller).run(solution)
    else:
        print("\n❌ 해법을 생성하지 못해 조립을 시작할 수 없습니다.")

    print("\n프로그램을 종료합니다.")
    rclpy.shutdown()
    dsr_node.destroy_node()

if __name__ == '__main__':
    main()
