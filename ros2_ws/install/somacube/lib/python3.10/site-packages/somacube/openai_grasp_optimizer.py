#!/usr/bin/env python3
"""
OpenAI API 기반 그랩 방법 추론 시스템
기존 그랩 최적화 로직을 OpenAI GPT 모델로 대체
"""

import os
import json
import numpy as np
from typing import List, Tuple, Dict, Optional, Union
from openai import OpenAI
import time

# .env 파일 지원
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

class OpenAIGraspOptimizer:
    """
    OpenAI API를 사용하여 로봇 그랩 방법을 최적화하는 클래스
    """
    
    def __init__(self, api_key: str = None, model: str = None):
        """
        초기화
        
        Args:
            api_key: OpenAI API 키
            model: 사용할 GPT 모델
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY', '')
        self.model = model or os.getenv('OPENAI_MODEL', 'gpt-4o')
        
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        self.client = OpenAI(api_key=self.api_key)
        
        # 로봇 특이점 정보
        self.singularity_zones = {
            "wrist_singularity": {"joint": 4, "dangerous_angles": [90.0, -90.0], "tolerance": 0.1},
            "shoulder_singularity": {"joint": 1, "dangerous_angles": [0.0, 180.0], "tolerance": 5.0},
            "elbow_singularity": {"joint": 2, "dangerous_angles": [0.0], "tolerance": 2.0},
        }
        
        # 그리퍼 물리적 제약조건
        self.gripper_constraints = {
            "min_approach_angle": -45.0,  # 최소 접근 각도
            "max_approach_angle": 45.0,   # 최대 접근 각도
            "collision_threshold": 15.0,  # 충돌 위험 임계값
            "safety_margin": 10.0,        # 안전 여유 각도
        }
        
        # 실시간 학습을 위한 피드백 저장
        self.feedback_history = []
        self.success_patterns = {}
        self.failure_patterns = {}
        
        print(f"🤖 OpenAI 그랩 최적화 시스템 초기화 완료 (Model: {self.model})")
    
    def choose_best_orientation_ai(self, start_pose: List[float], zyz_base_delta: List[float]) -> List[float]:
        """
        OpenAI를 사용하여 최적의 그리퍼 자세 선택
        기존 choose_best_orientation 함수와 동일한 형식으로 반환
        
        Args:
            start_pose: 현재 로봇 자세 [X, Y, Z, Rx, Ry, Rz]
            zyz_base_delta: AI가 제안한 회전 변화량 [dRx, dRy, dRz]
            
        Returns:
            최적화된 로봇 자세 [X, Y, Z, Rx, Ry, Rz]
        """
        
        system_prompt = """You are an expert robot motion planner specializing in gripper orientation optimization.

TASK: Choose the optimal gripper orientation to minimize collision risk and maximize grasp stability.

INPUT FORMAT:
- start_pose: [X, Y, Z, Rx, Ry, Rz] - Current robot pose in mm and degrees
- rotation_delta: [dRx, dRy, dRz] - Proposed rotation changes in ZYZ Euler angles (degrees)

ROBOT CONSTRAINTS:
- Gripper has "blade" orientation that must avoid vertical alignment
- Tool roll (Rz) can be adjusted ±90° for collision avoidance
- Wrist singularities occur near Ry = ±90°
- Horizontal blade orientation is safer than vertical

OPTIMIZATION CRITERIA:
1. Minimize gripper blade's vertical component (Z-axis alignment)
2. Avoid singularity zones (especially Ry ≈ ±90°)
3. Ensure stable grasp approach
4. Consider collision avoidance

OUTPUT FORMAT (JSON):
{
  "optimal_pose": [X, Y, Z, Rx, Ry, Rz],
  "safety_score": 0.85,
  "reasoning": "Selected orientation minimizes vertical blade alignment...",
  "alternative_tested": [X, Y, Z, Rx, Ry, Rz+90],
  "collision_risk": "low"
}

IMPORTANT: Return ONLY valid JSON. Ensure all angles are in degrees."""

        user_prompt = f"""Optimize gripper orientation for safe grasping:

Current robot pose: {start_pose}
Proposed rotation delta: {zyz_base_delta}

Please:
1. Calculate target pose by applying rotation delta
2. Consider tool roll +90° alternative
3. Evaluate safety scores for both options
4. Select the safer orientation
5. Avoid singularities (especially Ry near ±90°)

Return the optimal pose in the exact JSON format specified."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,  # 일관성 위해 낮은 온도
                max_tokens=1500
            )
            
            response_text = response.choices[0].message.content.strip()
            result = self._parse_orientation_response(response_text)
            
            if result and "optimal_pose" in result:
                print(f"🧠 AI 그리퍼 자세 최적화: {result.get('reasoning', 'No reasoning provided')}")
                print(f"   안전 점수: {result.get('safety_score', 'N/A')}")
                return result["optimal_pose"]
            else:
                print("⚠️ AI 응답 파싱 실패, 기본 계산 사용")
                return self._fallback_orientation_choice(start_pose, zyz_base_delta)
                
        except Exception as e:
            print(f"❌ AI 자세 최적화 오류: {str(e)}")
            return self._fallback_orientation_choice(start_pose, zyz_base_delta)
    
    def detect_and_avoid_singularities_ai(self, current_joints: List[float], target_pose: List[float]) -> Dict:
        """
        OpenAI를 사용하여 특이점 감지 및 회피 전략 생성
        
        Args:
            current_joints: 현재 조인트 각도 [J1, J2, J3, J4, J5, J6] (degrees)
            target_pose: 목표 자세 [X, Y, Z, Rx, Ry, Rz]
            
        Returns:
            특이점 회피 전략 딕셔너리
        """
        
        system_prompt = """You are an expert robotics engineer specializing in singularity avoidance for 6-DOF robot arms.

SINGULARITY ZONES TO AVOID:
1. Wrist Singularity: J5 (Ry) ≈ ±90° (±0.1°)
2. Shoulder Singularity: J2 ≈ 0° or 180° (±5°)  
3. Elbow Singularity: J3 ≈ 0° (±2°)

AVOIDANCE STRATEGIES:
- Wrist: Adjust to 89.9° or -89.9° instead of exact ±90°
- Add small offsets to avoid exact singularity angles
- Use alternative joint configurations if possible
- Prefer gradual adjustments over large jumps

OUTPUT FORMAT (JSON):
{
  "singularities_detected": ["wrist", "shoulder"],
  "risk_level": "high",
  "avoidance_strategy": {
    "method": "joint_adjustment",
    "adjustments": {
      "J5": {"from": 90.0, "to": 89.9, "reason": "wrist_singularity"}
    }
  },
  "safe_joints": [J1, J2, J3, J4, J5, J6],
  "alternative_pose": [X, Y, Z, Rx, Ry, Rz],
  "reasoning": "Detected wrist singularity, adjusted J5 to 89.9°"
}

Return ONLY valid JSON."""

        user_prompt = f"""Analyze robot configuration for singularities:

Current joint angles: {current_joints}
Target pose: {target_pose}

Please:
1. Check each joint for singularity proximity
2. Identify risk level (low/medium/high)
3. Propose specific avoidance adjustments
4. Provide safe joint angles
5. Suggest alternative pose if needed

Focus on maintaining target position while avoiding singularities."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=2000
            )
            
            response_text = response.choices[0].message.content.strip()
            result = self._parse_singularity_response(response_text)
            
            if result:
                print(f"🔍 AI 특이점 분석: {result.get('reasoning', 'No reasoning')}")
                print(f"   위험도: {result.get('risk_level', 'unknown')}")
                return result
            else:
                print("⚠️ AI 특이점 분석 실패, 기본 분석 사용")
                return self._fallback_singularity_detection(current_joints, target_pose)
                
        except Exception as e:
            print(f"❌ AI 특이점 분석 오류: {str(e)}")
            return self._fallback_singularity_detection(current_joints, target_pose)
    
    def optimize_grasp_approach_ai(self, piece_info: Dict, target_position: List[float], 
                                 surrounding_objects: List[Dict] = None) -> Dict:
        """
        OpenAI를 사용하여 종합적인 그랩 접근 전략 최적화
        
        Args:
            piece_info: 조각 정보 (크기, 형태, 무게중심 등)
            target_position: 목표 위치 [X, Y, Z]
            surrounding_objects: 주변 물체 정보 (충돌 회피용)
            
        Returns:
            최적화된 그랩 전략
        """
        
        system_prompt = """You are an expert robot grasp planner for 3D object manipulation.

GRASP OPTIMIZATION FACTORS:
1. Object geometry and center of mass
2. Approach angle and gripper clearance
3. Collision avoidance with surroundings
4. Grasp stability and force distribution
5. Motion efficiency and smoothness

SOMA CUBE PIECES:
- Small cubic blocks (25mm each)
- Various shapes: L, T, Z, V pieces
- Require precise alignment for assembly
- Need stable grasp for accurate placement

OUTPUT FORMAT (JSON):
{
  "approach_strategy": {
    "direction": "top-down",
    "angle_offset": [0, 0, 15],
    "clearance_height": 50.0
  },
  "gripper_config": {
    "opening_width": 30.0,
    "force_limit": 50.0,
    "contact_points": 2
  },
  "motion_plan": {
    "approach_pose": [X, Y, Z, Rx, Ry, Rz],
    "grasp_pose": [X, Y, Z, Rx, Ry, Rz],
    "lift_pose": [X, Y, Z, Rx, Ry, Rz]
  },
  "safety_checks": {
    "collision_free": true,
    "singularity_free": true,
    "stable_grasp": true
  },
  "confidence": 0.92,
  "reasoning": "Top-down approach minimizes collision risk..."
}

Return ONLY valid JSON."""

        surrounding_info = surrounding_objects or []
        
        user_prompt = f"""Plan optimal grasp strategy:

Piece Information: {piece_info}
Target Position: {target_position}
Surrounding Objects: {surrounding_info}

Requirements:
1. Safe approach without collisions
2. Stable grasp for precise placement
3. Efficient motion path
4. Avoid robot singularities
5. Consider piece geometry

Please provide comprehensive grasp strategy."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,
                max_tokens=2500
            )
            
            response_text = response.choices[0].message.content.strip()
            result = self._parse_grasp_strategy_response(response_text)
            
            if result:
                print(f"🎯 AI 그랩 전략: {result.get('reasoning', 'No reasoning')}")
                print(f"   신뢰도: {result.get('confidence', 'N/A')}")
                return result
            else:
                print("⚠️ AI 그랩 전략 실패, 기본 전략 사용")
                return self._fallback_grasp_strategy(piece_info, target_position)
                
        except Exception as e:
            print(f"❌ AI 그랩 전략 오류: {str(e)}")
            return self._fallback_grasp_strategy(piece_info, target_position)
    
    def _parse_orientation_response(self, response_text: str) -> Optional[Dict]:
        """OpenAI 자세 최적화 응답 파싱"""
        try:
            # JSON 부분 추출
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx == -1 or end_idx == 0:
                return None
            
            json_text = response_text[start_idx:end_idx]
            return json.loads(json_text)
            
        except (json.JSONDecodeError, ValueError) as e:
            print(f"자세 최적화 응답 파싱 오류: {e}")
            return None
    
    def _parse_singularity_response(self, response_text: str) -> Optional[Dict]:
        """OpenAI 특이점 분석 응답 파싱"""
        try:
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx == -1 or end_idx == 0:
                return None
            
            json_text = response_text[start_idx:end_idx]
            return json.loads(json_text)
            
        except (json.JSONDecodeError, ValueError) as e:
            print(f"특이점 분석 응답 파싱 오류: {e}")
            return None
    
    def _parse_grasp_strategy_response(self, response_text: str) -> Optional[Dict]:
        """OpenAI 그랩 전략 응답 파싱"""
        try:
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx == -1 or end_idx == 0:
                return None
            
            json_text = response_text[start_idx:end_idx]
            return json.loads(json_text)
            
        except (json.JSONDecodeError, ValueError) as e:
            print(f"그랩 전략 응답 파싱 오류: {e}")
            return None
    
    def _fallback_orientation_choice(self, start_pose: List[float], zyz_delta: List[float]) -> List[float]:
        """AI 실패시 기본 자세 최적화"""
        # 기본적으로 원래 자세에 회전 적용
        result_pose = start_pose.copy()
        
        # 간단한 ZYZ 회전 적용 (실제로는 더 복잡한 변환 필요)
        result_pose[3] += zyz_delta[0]  # Rx
        result_pose[4] += zyz_delta[1]  # Ry  
        result_pose[5] += zyz_delta[2]  # Rz
        
        # 특이점 회피를 위한 간단한 조정
        if abs(result_pose[4] - 90.0) < 0.1:
            result_pose[4] = 89.9
        elif abs(result_pose[4] + 90.0) < 0.1:
            result_pose[4] = -89.9
            
        return result_pose
    
    def _fallback_singularity_detection(self, joints: List[float], target_pose: List[float]) -> Dict:
        """AI 실패시 기본 특이점 감지"""
        detected_singularities = []
        adjustments = {}
        
        # J5 (Ry) 특이점 확인
        if abs(joints[4] - 90.0) < 0.1:
            detected_singularities.append("wrist")
            adjustments["J5"] = {"from": joints[4], "to": 89.9, "reason": "wrist_singularity"}
        elif abs(joints[4] + 90.0) < 0.1:
            detected_singularities.append("wrist")
            adjustments["J5"] = {"from": joints[4], "to": -89.9, "reason": "wrist_singularity"}
        
        return {
            "singularities_detected": detected_singularities,
            "risk_level": "medium" if detected_singularities else "low",
            "avoidance_strategy": {"method": "joint_adjustment", "adjustments": adjustments},
            "safe_joints": joints.copy(),
            "reasoning": "Basic singularity detection fallback"
        }
    
    def _fallback_grasp_strategy(self, piece_info: Dict, target_position: List[float]) -> Dict:
        """AI 실패시 기본 그랩 전략"""
        return {
            "approach_strategy": {
                "direction": "top-down",
                "angle_offset": [0, 0, 0],
                "clearance_height": 50.0
            },
            "motion_plan": {
                "approach_pose": target_position + [0, 0, 0],
                "grasp_pose": target_position + [0, 0, 0],
                "lift_pose": [target_position[0], target_position[1], target_position[2] + 50] + [0, 0, 0]
            },
            "confidence": 0.5,
            "reasoning": "Basic fallback grasp strategy"
        }
    
    def get_adaptive_strategy_with_history(self, piece_info: Dict, target_position: List[float]) -> Dict:
        """과거 피드백을 반영한 적응형 그랩 전략 생성"""
        recent_feedback = self._analyze_recent_patterns()
        
        system_prompt = """You are an adaptive robot grasp planner that learns from execution feedback.

OUTPUT FORMAT (JSON):
{
  "adaptive_strategy": {"based_on_history": true, "learned_adjustments": ["avoid_vertical_approach"]},
  "motion_plan": {
    "approach_pose": [X, Y, Z, Rx, Ry, Rz],
    "grasp_pose": [X, Y, Z, Rx, Ry, Rz],
    "lift_pose": [X, Y, Z, Rx, Ry, Rz]
  },
  "confidence": 0.92,
  "learning_insights": "Based on experience..."
}"""

        user_prompt = f"""Plan adaptive grasp strategy:
Piece: {piece_info}
Target: {target_position}
Experience: {recent_feedback}"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=1500
            )
            
            result = self._parse_grasp_strategy_response(response.choices[0].message.content.strip())
            return result if result else self.optimize_grasp_approach_ai(piece_info, target_position)
                
        except Exception as e:
            print(f"❌ 적응형 전략 생성 오류: {str(e)}")
            return self.optimize_grasp_approach_ai(piece_info, target_position)
    
    def diagnose_failure_and_suggest_improvements(self, failed_attempt: Dict, error_details: str) -> Dict:
        """실패한 시도를 분석하고 개선 방안 제시"""
        system_prompt = """Analyze robot grasp failures and suggest improvements.

OUTPUT FORMAT (JSON):
{
  "failure_analysis": {"primary_cause": "joint_singularity", "severity": "high"},
  "improvement_recommendations": {
    "immediate_fixes": [{"parameter": "approach_angle", "suggested": 75, "reason": "avoid_singularity"}]
  },
  "confidence": 0.88,
  "reasoning": "Analysis details..."
}"""

        user_prompt = f"""Analyze failure:
Attempt: {failed_attempt}
Error: {error_details}"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,
                max_tokens=1500
            )
            
            result = self._parse_failure_analysis_response(response.choices[0].message.content.strip())
            return result if result else {"error": "Failed to parse analysis"}
                
        except Exception as e:
            print(f"❌ 실패 분석 오류: {str(e)}")
            return {"error": str(e)}
    
    def _update_success_patterns(self, attempt_data: Dict):
        """성공 패턴 업데이트"""
        if "motion_plan" in attempt_data:
            approach_type = attempt_data["motion_plan"].get("approach_direction", "unknown")
            if approach_type not in self.success_patterns:
                self.success_patterns[approach_type] = {"count": 0}
            self.success_patterns[approach_type]["count"] += 1
    
    def _update_failure_patterns(self, attempt_data: Dict, error_msg: str):
        """실패 패턴 업데이트"""
        if "motion_plan" in attempt_data:
            approach_type = attempt_data["motion_plan"].get("approach_direction", "unknown")
            if approach_type not in self.failure_patterns:
                self.failure_patterns[approach_type] = {"count": 0, "errors": []}
            self.failure_patterns[approach_type]["count"] += 1
            self.failure_patterns[approach_type]["errors"].append(error_msg)
    
    def _analyze_recent_patterns(self) -> str:
        """최근 패턴 분석"""
        if not self.feedback_history:
            return "No historical data available."
        
        recent_feedback = self.feedback_history[-20:]
        success_count = sum(1 for f in recent_feedback if f["success"])
        total_count = len(recent_feedback)
        
        return f"Recent Performance: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)"
    
    def _parse_failure_analysis_response(self, response_text: str) -> Optional[Dict]:
        """실패 분석 응답 파싱"""
        try:
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx == -1 or end_idx == 0:
                return None
            
            json_text = response_text[start_idx:end_idx]
            return json.loads(json_text)
            
        except (json.JSONDecodeError, ValueError) as e:
            print(f"실패 분석 응답 파싱 오류: {e}")
            return None


class OpenAIGraspInterface:
    """
    기존 그랩 함수들을 OpenAI 기반으로 대체하는 인터페이스
    """
    
    def __init__(self, api_key: str = None, enable_adaptive_learning: bool = True):
        """초기화"""
        try:
            self.optimizer = OpenAIGraspOptimizer(api_key=api_key)
            self.ai_enabled = True
            
            # 적응형 학습 시스템 초기화
            if enable_adaptive_learning:
                try:
                    from .adaptive_grasp_system import AdaptiveGraspSystem
                    self.adaptive_system = AdaptiveGraspSystem(self.optimizer)
                    self.adaptive_enabled = True
                    print("🧠 적응형 학습 시스템 활성화됨")
                except Exception as e:
                    print(f"⚠️ 적응형 학습 시스템 초기화 실패: {e}")
                    self.adaptive_enabled = False
            else:
                self.adaptive_enabled = False
                
        except Exception as e:
            print(f"⚠️ OpenAI 그랩 최적화 초기화 실패: {e}")
            self.ai_enabled = False
            self.adaptive_enabled = False
    
    def choose_best_orientation(self, start_pose: List[float], zyz_base_delta: List[float]) -> List[float]:
        """
        기존 choose_best_orientation 함수와 동일한 인터페이스
        OpenAI 기반 또는 폴백 처리
        """
        if self.ai_enabled:
            return self.optimizer.choose_best_orientation_ai(start_pose, zyz_base_delta)
        else:
            return self._original_choose_best_orientation(start_pose, zyz_base_delta)
    
    def correct_colliding_pose(self, target_pose: List[float]) -> List[float]:
        """
        기존 correct_colliding_pose 함수와 동일한 인터페이스
        OpenAI 기반 충돌 회피 + 특이점 회피
        """
        if self.ai_enabled:
            # 현재 조인트 각도는 실제 환경에서 가져와야 함
            dummy_joints = [0, 0, 90, 0, target_pose[4], 0]  # 임시
            
            singularity_result = self.optimizer.detect_and_avoid_singularities_ai(dummy_joints, target_pose)
            
            if "alternative_pose" in singularity_result:
                return singularity_result["alternative_pose"]
            elif "safe_joints" in singularity_result:
                # 조인트 각도를 자세로 변환 (실제로는 역기구학 필요)
                return target_pose  # 임시
        
        return self._original_correct_colliding_pose(target_pose)
    
    def is_gripper_collision_expected(self, pose: List[float]) -> bool:
        """
        기존 is_gripper_collision_expected 함수와 동일한 인터페이스
        OpenAI 기반 충돌 위험 판단
        """
        if self.ai_enabled:
            try:
                # 간단한 충돌 위험 판단을 AI에게 요청
                piece_info = {"type": "soma_cube", "size": [25, 25, 25]}
                strategy = self.optimizer.optimize_grasp_approach_ai(piece_info, pose[:3])
                
                safety_checks = strategy.get("safety_checks", {})
                return not safety_checks.get("collision_free", True)
            except:
                pass
        
        return self._original_is_gripper_collision_expected(pose)
    
    def _original_choose_best_orientation(self, start_pose: List[float], zyz_delta: List[float]) -> List[float]:
        """원래 함수의 간단한 구현"""
        result_pose = start_pose.copy()
        result_pose[3] += zyz_delta[0]
        result_pose[4] += zyz_delta[1]  
        result_pose[5] += zyz_delta[2]
        return result_pose
    
    def _original_correct_colliding_pose(self, target_pose: List[float]) -> List[float]:
        """원래 함수의 간단한 구현"""
        corrected_pose = target_pose.copy()
        if self._original_is_gripper_collision_expected(target_pose):
            corrected_pose[5] = 90.0  # 툴 롤을 90도로 설정
        return corrected_pose
    
    def _original_is_gripper_collision_expected(self, pose: List[float]) -> bool:
        """원래 함수의 간단한 구현"""
        ry = pose[4]
        rz_prime = pose[5]
        
        is_lying_down = abs(ry - 90) < 15 or abs(ry + 90) < 15
        is_roll_problematic = (abs(rz_prime) < 15 or abs(rz_prime - 180) < 15 or abs(rz_prime + 180) < 15)
        
        return is_lying_down and is_roll_problematic
    
    def learn_from_execution_feedback(self, attempt_data: Dict, success: bool, error_msg: str = None):
        """
        실행 결과를 바탕으로 실시간 학습
        
        Args:
            attempt_data: 시도한 그랩 데이터 (자세, 전략 등)
            success: 성공 여부
            error_msg: 실패시 오류 메시지
        """
        feedback_entry = {
            "timestamp": time.time(),
            "attempt_data": attempt_data,
            "success": success,
            "error_msg": error_msg
        }
        
        self.optimizer.feedback_history.append(feedback_entry)
        
        # 최근 피드백만 유지 (메모리 관리)
        if len(self.optimizer.feedback_history) > 100:
            self.optimizer.feedback_history = self.optimizer.feedback_history[-100:]
        
        # 패턴 업데이트
        if success:
            self._update_success_patterns(attempt_data)
        else:
            self._update_failure_patterns(attempt_data, error_msg)
            
        print(f"📚 피드백 학습: {'✅ 성공' if success else '❌ 실패'} - 총 {len(self.optimizer.feedback_history)}개 기록")
    
    def get_adaptive_strategy_with_history(self, piece_info: Dict, target_position: List[float]) -> Dict:
        """
        과거 피드백을 반영한 적응형 그랩 전략 생성
        """
        if not self.ai_enabled:
            return self._fallback_grasp_strategy(piece_info, target_position)
            
        return self.optimizer.get_adaptive_strategy_with_history(piece_info, target_position)
    
    def diagnose_failure_and_improve(self, failed_attempt: Dict, error_details: str) -> Dict:
        """
        실패 분석 및 개선 방안 제시
        """
        if not self.ai_enabled:
            return {"error": "AI not enabled"}
            
        return self.optimizer.diagnose_failure_and_suggest_improvements(failed_attempt, error_details)
    
    def _update_success_patterns(self, attempt_data: Dict):
        """성공 패턴 업데이트"""
        if hasattr(self, 'optimizer'):
            self.optimizer._update_success_patterns(attempt_data)
    
    def _update_failure_patterns(self, attempt_data: Dict, error_msg: str):
        """실패 패턴 업데이트"""
        if hasattr(self, 'optimizer'):
            self.optimizer._update_failure_patterns(attempt_data, error_msg)
    
    def record_grasp_result(self, piece_id: int, target_pose: List[float], 
                           gripper_pose: List[float], success: bool,
                           failure_reason: str = None, execution_time: float = 0.0,
                           collision_detected: bool = False,
                           singularity_encountered: bool = False) -> None:
        """
        그랩 결과를 적응형 학습 시스템에 기록
        """
        if self.adaptive_enabled:
            self.adaptive_system.record_grasp_attempt(
                piece_id=piece_id,
                target_pose=target_pose,
                gripper_pose=gripper_pose,
                success=success,
                failure_reason=failure_reason,
                execution_time=execution_time,
                ai_strategy={},  # 실제 전략 정보 전달 필요
                collision_detected=collision_detected,
                singularity_encountered=singularity_encountered
            )
    
    def get_adaptive_strategy_advice(self, piece_id: int, target_pose: List[float]) -> Dict:
        """
        학습된 패턴을 기반으로 적응형 전략 조언 제공
        """
        if self.adaptive_enabled:
            return self.adaptive_system.get_adaptive_strategy(piece_id, target_pose)
        return {"use_learned_pattern": False}
    
    def get_performance_report(self) -> Dict:
        """
        그랩 시스템 성능 리포트 조회
        """
        if self.adaptive_enabled:
            return self.adaptive_system.get_performance_report()
        return {"message": "Adaptive learning not enabled"}