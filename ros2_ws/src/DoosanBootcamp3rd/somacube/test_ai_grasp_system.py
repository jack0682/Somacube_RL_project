#!/usr/bin/env python3
"""
AI 그랩 시스템 테스트 스크립트
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
    
    print("🤖 AI 그랩 최적화 시스템 테스트")
    print("=" * 50)
    
    # API 키 확인
    api_key = os.getenv('OPENAI_API_KEY', '').strip()
    
    if not api_key:
        print("❌ .env 파일에 OPENAI_API_KEY가 설정되지 않았습니다.")
        return False
    
    try:
        from somacube.openai_grasp_optimizer import OpenAIGraspInterface
        
        # 그랩 인터페이스 초기화
        print("🔧 그랩 인터페이스 초기화 중...")
        grasp_interface = OpenAIGraspInterface()
        
        if not grasp_interface.ai_enabled:
            print("❌ AI 그랩 최적화가 비활성화되었습니다.")
            return False
        
        print("✅ AI 그랩 최적화 활성화됨")
        print(f"   적응형 학습: {'✅ 활성화' if grasp_interface.adaptive_enabled else '❌ 비활성화'}")
        
        # 테스트 시나리오들
        test_scenarios = [
            {
                "name": "기본 자세 최적화",
                "start_pose": [400.0, 0.0, 200.0, 0.0, 0.0, 0.0],
                "rotation_delta": [10.0, 15.0, 0.0],
                "expected": "최적 자세 반환"
            },
            {
                "name": "특이점 근처 자세",
                "start_pose": [400.0, 0.0, 200.0, 0.0, 89.5, 0.0],
                "rotation_delta": [0.0, 0.5, 0.0],
                "expected": "특이점 회피 자세"
            },
            {
                "name": "충돌 위험 자세",
                "start_pose": [400.0, 0.0, 200.0, 0.0, 90.0, 180.0],
                "rotation_delta": [0.0, 0.0, 0.0],
                "expected": "충돌 회피 자세"
            }
        ]
        
        success_count = 0
        
        for i, scenario in enumerate(test_scenarios, 1):
            print(f"\n📋 테스트 {i}: {scenario['name']}")
            print(f"   입력 자세: {scenario['start_pose']}")
            print(f"   회전 변화: {scenario['rotation_delta']}")
            
            try:
                # 자세 최적화 테스트
                optimized_pose = grasp_interface.choose_best_orientation(
                    scenario['start_pose'], 
                    scenario['rotation_delta']
                )
                
                print(f"   ✅ 최적화된 자세: {[f'{x:.2f}' for x in optimized_pose]}")
                
                # 충돌 예상 테스트
                collision_expected = grasp_interface.is_gripper_collision_expected(optimized_pose)
                print(f"   🔍 충돌 위험: {'⚠️ 예상됨' if collision_expected else '✅ 안전함'}")
                
                # 충돌 방지 보정 테스트
                if collision_expected:
                    corrected_pose = grasp_interface.correct_colliding_pose(optimized_pose)
                    print(f"   🔧 보정된 자세: {[f'{x:.2f}' for x in corrected_pose]}")
                
                success_count += 1
                
                # 적응형 학습이 활성화된 경우 결과 기록
                if grasp_interface.adaptive_enabled:
                    grasp_interface.record_grasp_result(
                        piece_id=0,  # 테스트용
                        target_pose=scenario['start_pose'],
                        gripper_pose=optimized_pose,
                        success=True,
                        execution_time=2.0  # 가상의 실행 시간
                    )
                
            except Exception as e:
                print(f"   ❌ 테스트 실패: {str(e)}")
        
        # 성능 리포트 테스트
        if grasp_interface.adaptive_enabled:
            print(f"\n📊 적응형 학습 성능 리포트:")
            report = grasp_interface.get_performance_report()
            
            if "overall_metrics" in report:
                metrics = report["overall_metrics"]
                print(f"   총 시도: {metrics.get('total_attempts', 0)}")
                print(f"   성공 횟수: {metrics.get('successful_grasps', 0)}")
                print(f"   충돌 회피율: {metrics.get('collision_avoidance_rate', 0):.2%}")
            
            if "recommendations" in report:
                print("   권장사항:")
                for rec in report["recommendations"]:
                    print(f"     - {rec}")
        
        print(f"\n📈 테스트 결과: {success_count}/{len(test_scenarios)} 성공")
        
        return success_count == len(test_scenarios)
        
    except ImportError as e:
        print(f"❌ 모듈 임포트 오류: {e}")
        print("필요한 패키지를 설치해주세요: pip install openai python-dotenv")
        return False
    except Exception as e:
        print(f"❌ 테스트 오류: {e}")
        return False

def test_singularity_detection():
    """특이점 감지 테스트"""
    
    print("\n🔍 특이점 감지 및 회피 테스트")
    print("=" * 40)
    
    try:
        from somacube.openai_grasp_optimizer import OpenAIGraspOptimizer
        
        optimizer = OpenAIGraspOptimizer()
        
        # 특이점 테스트 케이스들
        test_cases = [
            {
                "name": "손목 특이점 (Ry=90°)",
                "joints": [0, 0, 90, 0, 90.0, 0],
                "target": [400, 0, 200, 0, 90, 0]
            },
            {
                "name": "손목 특이점 (Ry=-90°)", 
                "joints": [0, 0, 90, 0, -90.0, 0],
                "target": [400, 0, 200, 0, -90, 0]
            },
            {
                "name": "안전한 자세",
                "joints": [0, 0, 90, 0, 45.0, 0],
                "target": [400, 0, 200, 0, 45, 0]
            }
        ]
        
        for case in test_cases:
            print(f"\n📐 {case['name']}")
            print(f"   조인트 각도: {case['joints']}")
            
            try:
                result = optimizer.detect_and_avoid_singularities_ai(
                    case['joints'], 
                    case['target']
                )
                
                print(f"   🎯 감지된 특이점: {result.get('singularities_detected', [])}")
                print(f"   ⚠️ 위험도: {result.get('risk_level', 'unknown')}")
                
                if result.get('avoidance_strategy'):
                    strategy = result['avoidance_strategy']
                    print(f"   🔧 회피 방법: {strategy.get('method', 'none')}")
                    
                    if 'adjustments' in strategy:
                        for joint, adj in strategy['adjustments'].items():
                            print(f"     {joint}: {adj['from']}° → {adj['to']}° ({adj['reason']})")
                
                print(f"   💭 추론: {result.get('reasoning', 'No reasoning provided')}")
                
            except Exception as e:
                print(f"   ❌ 특이점 분석 실패: {e}")
        
    except Exception as e:
        print(f"❌ 특이점 테스트 오류: {e}")

def main():
    """메인 테스트 함수"""
    
    print("🧪 OpenAI 그랩 시스템 종합 테스트")
    print("=" * 60)
    
    # 기본 그랩 최적화 테스트
    grasp_success = test_grasp_optimization()
    
    # 특이점 감지 테스트  
    test_singularity_detection()
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("🏁 테스트 완료")
    
    if grasp_success:
        print("✅ 모든 그랩 최적화 테스트 통과!")
    else:
        print("❌ 일부 테스트 실패")
    
    print("\n💡 주요 기능:")
    print("  🧠 AI 기반 그리퍼 자세 최적화")
    print("  🔍 지능형 특이점 감지 및 회피")
    print("  ⚡ 실시간 충돌 위험 평가")  
    print("  📈 적응형 학습을 통한 성능 개선")
    print("  🔄 기존 시스템과의 완벽한 호환성")

if __name__ == "__main__":
    main()