#!/usr/bin/env python3
"""
OpenAI 그랩 최적화 시스템 테스트 스크립트
"""

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'somacube'))

# .env 파일 지원
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ .env 파일 로드됨")
except ImportError:
    print("⚠️ python-dotenv가 설치되지 않았습니다.")

def test_grasp_optimization():
    """그랩 최적화 기능 테스트"""
    
    api_key = os.getenv('OPENAI_API_KEY', '').strip()
    
    if not api_key:
        print("❌ .env 파일에 OPENAI_API_KEY가 설정되지 않았습니다.")
        return False
    
    try:
        from somacube.openai_grasp_optimizer import OpenAIGraspInterface
        
        print("🤖 OpenAI 그랩 최적화 테스트 시작...")
        
        # 그랩 인터페이스 생성
        grasp_interface = OpenAIGraspInterface()
        
        if not grasp_interface.ai_enabled:
            print("❌ AI 그랩 최적화가 활성화되지 않았습니다.")
            return False
        
        print("✅ AI 그랩 시스템 초기화 성공")
        
        # 테스트 데이터
        test_start_pose = [450.0, 0.0, 100.0, 0.0, 0.0, 0.0]
        test_rotation_delta = [0.0, 15.0, 0.0]
        
        print("\n🧠 그리퍼 자세 최적화 테스트...")
        optimized_pose = grasp_interface.choose_best_orientation(test_start_pose, test_rotation_delta)
        
        print(f"   입력 자세: {test_start_pose}")
        print(f"   회전 변화: {test_rotation_delta}")
        print(f"   최적화된 자세: {optimized_pose}")
        
        # 충돌 감지 테스트
        print("\n🔍 충돌 감지 테스트...")
        collision_risk = grasp_interface.is_gripper_collision_expected(optimized_pose)
        print(f"   충돌 위험: {'⚠️ 높음' if collision_risk else '✅ 낮음'}")
        
        # 충돌 보정 테스트
        if collision_risk:
            print("\n🛠️ 충돌 보정 테스트...")
            corrected_pose = grasp_interface.correct_colliding_pose(optimized_pose)
            print(f"   보정된 자세: {corrected_pose}")
        
        # 적응형 전략 테스트
        print("\n🎓 적응형 그랩 전략 테스트...")
        piece_info = {
            "type": "soma_cube_piece",
            "id": 1,
            "size": [25, 25, 25],
            "shape": "L-piece"
        }
        target_position = [450.0, 100.0, 50.0]
        
        adaptive_strategy = grasp_interface.get_adaptive_strategy_with_history(piece_info, target_position)
        
        print(f"   조각 정보: {piece_info}")
        print(f"   목표 위치: {target_position}")
        print(f"   전략 신뢰도: {adaptive_strategy.get('confidence', 'N/A')}")
        if 'motion_plan' in adaptive_strategy:
            motion_plan = adaptive_strategy['motion_plan']
            print(f"   접근 자세: {motion_plan.get('approach_pose', 'N/A')}")
            print(f"   그랩 자세: {motion_plan.get('grasp_pose', 'N/A')}")
        
        # 피드백 학습 테스트
        print("\n📚 피드백 학습 테스트...")
        
        # 성공 사례 학습
        success_attempt = {
            "piece_info": piece_info,
            "motion_plan": adaptive_strategy.get('motion_plan', {}),
            "execution_time": 3.5
        }
        grasp_interface.learn_from_execution_feedback(success_attempt, True, None)
        
        # 실패 사례 학습
        failure_attempt = {
            "piece_info": piece_info,
            "motion_plan": {"approach_direction": "side_approach"},
            "execution_time": 2.1
        }
        grasp_interface.learn_from_execution_feedback(failure_attempt, False, "Joint singularity encountered")
        
        # 실패 분석 테스트
        print("\n🔬 실패 분석 테스트...")
        analysis_result = grasp_interface.diagnose_failure_and_improve(failure_attempt, "Joint singularity at J5=90°")
        
        if "failure_analysis" in analysis_result:
            failure_analysis = analysis_result["failure_analysis"]
            print(f"   실패 원인: {failure_analysis.get('primary_cause', 'Unknown')}")
            print(f"   심각도: {failure_analysis.get('severity', 'Unknown')}")
        
        if "improvement_recommendations" in analysis_result:
            recommendations = analysis_result["improvement_recommendations"]
            immediate_fixes = recommendations.get("immediate_fixes", [])
            print(f"   즉시 개선안: {len(immediate_fixes)}개 제안")
            for fix in immediate_fixes[:2]:  # 처음 2개만 출력
                print(f"     - {fix.get('parameter', 'N/A')}: {fix.get('suggested', 'N/A')} ({fix.get('reason', 'N/A')})")
        
        print("\n✅ 모든 그랩 최적화 테스트 완료!")
        return True
        
    except ImportError as e:
        print(f"❌ 모듈 임포트 오류: {e}")
        return False
    except Exception as e:
        print(f"❌ 테스트 오류: {e}")
        return False

def test_performance_comparison():
    """성능 비교 테스트"""
    print("\n" + "="*60)
    print("OpenAI vs 기존 시스템 성능 비교")
    print("="*60)
    
    print("\n🤖 기존 시스템:")
    print("  ✅ 장점: 빠른 실행 속도, 오프라인 작동, 비용 없음")
    print("  ❌ 단점: 제한된 추론 능력, 설명력 부족, 고정된 로직")
    
    print("\n🧠 OpenAI AI 시스템:")
    print("  ✅ 장점: 고급 추론, 설명 가능성, 적응형 학습, 실시간 개선")
    print("  ❌ 단점: API 비용, 인터넷 필요, 응답 시간 변동")
    
    print("\n💡 권장 사용 시나리오:")
    print("  🔬 연구/개발: OpenAI AI 시스템 (고급 추론과 학습 능력)")
    print("  🏭 생산 환경: 하이브리드 시스템 (AI로 학습, 기존 시스템으로 실행)")
    print("  🚨 응급 상황: 기존 시스템 (안정성과 일관성)")

if __name__ == "__main__":
    print("🔬 OpenAI 그랩 최적화 시스템 종합 테스트")
    print("-" * 50)
    
    success = test_grasp_optimization()
    
    if success:
        print("\n🎉 모든 테스트 성공!")
        test_performance_comparison()
    else:
        print("\n💥 테스트 실패")
    
    print("\n" + "="*60)
    print("테스트 완료 - 이제 실제 로봇에서 테스트해보세요!")
    print("사용법: ros2 run somacube RL_with_robot2")
    print("="*60)