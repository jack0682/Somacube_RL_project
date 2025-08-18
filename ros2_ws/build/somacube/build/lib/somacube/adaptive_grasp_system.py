#!/usr/bin/env python3
"""
적응형 그랩 시스템
실행 결과를 기반으로 OpenAI 그랩 전략을 실시간 개선
"""

import os
import json
import time
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class GraspAttempt:
    """그랩 시도 기록"""
    timestamp: str
    piece_id: int
    target_pose: List[float]
    gripper_pose: List[float] 
    success: bool
    failure_reason: Optional[str]
    execution_time: float
    ai_strategy: Dict
    collision_detected: bool
    singularity_encountered: bool

class AdaptiveGraspSystem:
    """
    실시간 학습을 통한 적응형 그랩 시스템
    """
    
    def __init__(self, openai_grasp_optimizer):
        """
        초기화
        
        Args:
            openai_grasp_optimizer: OpenAIGraspOptimizer 인스턴스
        """
        self.optimizer = openai_grasp_optimizer
        self.grasp_history: List[GraspAttempt] = []
        self.performance_metrics = {
            "total_attempts": 0,
            "successful_grasps": 0,
            "collision_avoidance_rate": 0.0,
            "singularity_avoidance_rate": 0.0,
            "average_execution_time": 0.0
        }
        
        # 학습된 패턴들
        self.learned_patterns = {
            "successful_approaches": {},  # piece_id -> best strategies
            "failure_patterns": {},       # failure_reason -> avoidance strategies
            "problematic_poses": [],      # 문제가 되는 자세들
            "optimal_orientations": {}    # piece_id -> preferred orientations
        }
        
        print("🔄 적응형 그랩 시스템 초기화 완료")
    
    def record_grasp_attempt(self, piece_id: int, target_pose: List[float], 
                           gripper_pose: List[float], success: bool,
                           failure_reason: Optional[str] = None,
                           execution_time: float = 0.0,
                           ai_strategy: Dict = None,
                           collision_detected: bool = False,
                           singularity_encountered: bool = False) -> None:
        """
        그랩 시도 결과 기록
        """
        attempt = GraspAttempt(
            timestamp=datetime.now().isoformat(),
            piece_id=piece_id,
            target_pose=target_pose.copy(),
            gripper_pose=gripper_pose.copy(),
            success=success,
            failure_reason=failure_reason,
            execution_time=execution_time,
            ai_strategy=ai_strategy or {},
            collision_detected=collision_detected,
            singularity_encountered=singularity_encountered
        )
        
        self.grasp_history.append(attempt)
        self._update_metrics()
        self._update_learned_patterns(attempt)
        
        print(f"📊 그랩 시도 기록: {'✅ 성공' if success else '❌ 실패'}")
        if failure_reason:
            print(f"   실패 원인: {failure_reason}")
    
    def get_adaptive_strategy(self, piece_id: int, target_pose: List[float]) -> Dict:
        """
        학습된 패턴을 기반으로 적응형 그랩 전략 생성
        """
        base_strategy = {
            "use_learned_pattern": False,
            "confidence_boost": 0.0,
            "recommended_approach": "standard",
            "avoid_patterns": [],
            "preferred_orientation": None
        }
        
        # 성공한 접근법이 있는지 확인
        if piece_id in self.learned_patterns["successful_approaches"]:
            successful_strategies = self.learned_patterns["successful_approaches"][piece_id]
            if successful_strategies:
                best_strategy = max(successful_strategies, key=lambda x: x["success_rate"])
                base_strategy.update({
                    "use_learned_pattern": True,
                    "confidence_boost": best_strategy["success_rate"] * 0.2,
                    "recommended_approach": best_strategy["approach_type"],
                    "preferred_orientation": best_strategy.get("orientation")
                })
        
        # 피해야 할 패턴들 확인
        problematic_areas = self._find_problematic_areas_near(target_pose)
        if problematic_areas:
            base_strategy["avoid_patterns"] = problematic_areas
        
        return base_strategy
    
    def improve_strategy_with_feedback(self, piece_id: int, failed_strategy: Dict,
                                     failure_reason: str) -> Dict:
        """
        실패 피드백을 기반으로 전략 개선
        """
        improvement_prompt = f"""Based on the following failure, suggest an improved grasp strategy:

Failed Strategy: {failed_strategy}
Failure Reason: {failure_reason}
Piece ID: {piece_id}

Historical Performance:
- Total attempts: {self.performance_metrics['total_attempts']}
- Success rate: {self._calculate_success_rate():.2%}
- Common failure patterns: {self._get_common_failure_patterns()}

Please suggest specific improvements:
1. Alternative approach angles
2. Different gripper orientations  
3. Modified safety margins
4. Adjusted motion planning

Return improved strategy in JSON format."""

        try:
            response = self.optimizer.client.chat.completions.create(
                model=self.optimizer.model,
                messages=[
                    {"role": "system", "content": "You are an expert robotics engineer specializing in adaptive grasp planning."},
                    {"role": "user", "content": improvement_prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            response_text = response.choices[0].message.content.strip()
            improved_strategy = self._parse_improvement_response(response_text)
            
            if improved_strategy:
                print(f"🔧 AI 기반 전략 개선 완료")
                return improved_strategy
            else:
                print("⚠️ 전략 개선 파싱 실패")
                return self._generate_fallback_improvement(failure_reason)
                
        except Exception as e:
            print(f"❌ AI 전략 개선 오류: {e}")
            return self._generate_fallback_improvement(failure_reason)
    
    def get_performance_report(self) -> Dict:
        """성능 리포트 생성"""
        if not self.grasp_history:
            return {"message": "No grasp attempts recorded yet"}
        
        recent_attempts = self.grasp_history[-10:]  # 최근 10개
        
        report = {
            "overall_metrics": self.performance_metrics.copy(),
            "recent_performance": {
                "attempts": len(recent_attempts),
                "success_rate": sum(1 for a in recent_attempts if a.success) / len(recent_attempts),
                "avg_time": sum(a.execution_time for a in recent_attempts) / len(recent_attempts)
            },
            "learning_insights": {
                "successful_patterns": len(self.learned_patterns["successful_approaches"]),
                "identified_failures": len(self.learned_patterns["failure_patterns"]),
                "problematic_poses": len(self.learned_patterns["problematic_poses"])
            },
            "recommendations": self._generate_recommendations()
        }
        
        return report
    
    def _update_metrics(self) -> None:
        """성능 메트릭 업데이트"""
        total = len(self.grasp_history)
        successful = sum(1 for attempt in self.grasp_history if attempt.success)
        
        self.performance_metrics.update({
            "total_attempts": total,
            "successful_grasps": successful,
            "collision_avoidance_rate": self._calculate_collision_avoidance_rate(),
            "singularity_avoidance_rate": self._calculate_singularity_avoidance_rate(),
            "average_execution_time": self._calculate_average_execution_time()
        })
    
    def _update_learned_patterns(self, attempt: GraspAttempt) -> None:
        """학습된 패턴 업데이트"""
        piece_id = attempt.piece_id
        
        if attempt.success:
            # 성공한 접근법 저장
            if piece_id not in self.learned_patterns["successful_approaches"]:
                self.learned_patterns["successful_approaches"][piece_id] = []
            
            strategy_info = {
                "target_pose": attempt.target_pose,
                "gripper_pose": attempt.gripper_pose,
                "approach_type": attempt.ai_strategy.get("approach_strategy", {}).get("direction", "unknown"),
                "orientation": attempt.gripper_pose[3:],
                "success_rate": 1.0,  # 초기값, 나중에 업데이트
                "execution_time": attempt.execution_time
            }
            
            self.learned_patterns["successful_approaches"][piece_id].append(strategy_info)
            
        else:
            # 실패 패턴 저장
            if attempt.failure_reason:
                if attempt.failure_reason not in self.learned_patterns["failure_patterns"]:
                    self.learned_patterns["failure_patterns"][attempt.failure_reason] = []
                
                failure_info = {
                    "target_pose": attempt.target_pose,
                    "gripper_pose": attempt.gripper_pose,
                    "collision_detected": attempt.collision_detected,
                    "singularity_encountered": attempt.singularity_encountered
                }
                
                self.learned_patterns["failure_patterns"][attempt.failure_reason].append(failure_info)
    
    def _calculate_success_rate(self) -> float:
        """성공률 계산"""
        if not self.grasp_history:
            return 0.0
        return self.performance_metrics["successful_grasps"] / self.performance_metrics["total_attempts"]
    
    def _calculate_collision_avoidance_rate(self) -> float:
        """충돌 회피율 계산"""
        if not self.grasp_history:
            return 0.0
        total = len(self.grasp_history)
        collisions = sum(1 for attempt in self.grasp_history if attempt.collision_detected)
        return (total - collisions) / total
    
    def _calculate_singularity_avoidance_rate(self) -> float:
        """특이점 회피율 계산"""
        if not self.grasp_history:
            return 0.0
        total = len(self.grasp_history)
        singularities = sum(1 for attempt in self.grasp_history if attempt.singularity_encountered)
        return (total - singularities) / total
    
    def _calculate_average_execution_time(self) -> float:
        """평균 실행 시간 계산"""
        if not self.grasp_history:
            return 0.0
        total_time = sum(attempt.execution_time for attempt in self.grasp_history)
        return total_time / len(self.grasp_history)
    
    def _find_problematic_areas_near(self, target_pose: List[float], threshold: float = 50.0) -> List[Dict]:
        """목표 위치 근처의 문제가 되는 영역 찾기"""
        problematic = []
        
        for pose in self.learned_patterns["problematic_poses"]:
            # 거리 계산 (간단한 유클리드 거리)
            distance = sum((a - b) ** 2 for a, b in zip(target_pose[:3], pose[:3])) ** 0.5
            
            if distance <= threshold:
                problematic.append({
                    "pose": pose,
                    "distance": distance,
                    "type": "collision_prone"
                })
        
        return problematic
    
    def _get_common_failure_patterns(self) -> List[str]:
        """일반적인 실패 패턴 조회"""
        failure_counts = {}
        
        for attempt in self.grasp_history:
            if not attempt.success and attempt.failure_reason:
                reason = attempt.failure_reason
                failure_counts[reason] = failure_counts.get(reason, 0) + 1
        
        # 빈도 순으로 정렬
        sorted_failures = sorted(failure_counts.items(), key=lambda x: x[1], reverse=True)
        return [reason for reason, count in sorted_failures[:3]]  # 상위 3개
    
    def _parse_improvement_response(self, response_text: str) -> Optional[Dict]:
        """개선 전략 응답 파싱"""
        try:
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx == -1 or end_idx == 0:
                return None
            
            json_text = response_text[start_idx:end_idx]
            return json.loads(json_text)
            
        except (json.JSONDecodeError, ValueError):
            return None
    
    def _generate_fallback_improvement(self, failure_reason: str) -> Dict:
        """폴백 개선 전략"""
        improvements = {
            "collision": {
                "approach_angle_adjustment": 10.0,
                "safety_margin_increase": 5.0,
                "alternative_orientation": True
            },
            "singularity": {
                "joint_adjustment": 2.0,
                "alternative_path": True,
                "safety_check_enhanced": True
            },
            "timeout": {
                "motion_speed_increase": 20,
                "path_optimization": True
            }
        }
        
        return improvements.get(failure_reason, {"general_improvement": True})
    
    def _generate_recommendations(self) -> List[str]:
        """성능 기반 권장사항 생성"""
        recommendations = []
        
        success_rate = self._calculate_success_rate()
        collision_rate = 1 - self.performance_metrics["collision_avoidance_rate"]
        
        if success_rate < 0.8:
            recommendations.append("전체 성공률이 낮습니다. 그랩 전략을 재검토하세요.")
        
        if collision_rate > 0.2:
            recommendations.append("충돌 발생률이 높습니다. 안전 여유 거리를 증가시키세요.")
        
        if self.performance_metrics["average_execution_time"] > 30.0:
            recommendations.append("평균 실행 시간이 깁니다. 모션 경로를 최적화하세요.")
        
        if not recommendations:
            recommendations.append("시스템이 잘 작동하고 있습니다!")
        
        return recommendations