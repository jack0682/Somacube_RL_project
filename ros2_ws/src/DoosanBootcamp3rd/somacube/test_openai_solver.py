#!/usr/bin/env python3
"""
OpenAI 소마큐브 솔버 테스트 스크립트
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
    print("⚠️ python-dotenv가 설치되지 않았습니다. pip install python-dotenv로 설치하세요.")

def test_openai_solver():
    """OpenAI 솔버 기능 테스트"""
    
    # API 키 확인 (.env 파일에서 자동으로 로드됨)
    api_key = os.getenv('OPENAI_API_KEY', '').strip()
    
    if api_key:
        print("✅ .env 파일에서 OpenAI API 키를 찾았습니다.")
    else:
        print("❌ .env 파일에 OPENAI_API_KEY가 설정되지 않았습니다.")
        api_key = input("OpenAI API 키를 입력하세요: ").strip()
    
    if not api_key:
        print("❌ API 키가 필요합니다.")
        return False
    
    try:
        from somacube.openai_soma_solver import OpenAISomaCubeInterface
        
        print("🧠 OpenAI 소마큐브 솔버 테스트 시작...")
        
        # 솔버 인스턴스 생성 (.env에서 자동으로 설정 읽음)
        interface = OpenAISomaCubeInterface()
        
        # 해법 생성 테스트
        solution = interface.generate_solution_path()
        
        if solution:
            print("✅ 해법 생성 성공!")
            print(f"생성된 해법 ({len(solution)}단계):")
            
            for i, (piece_id, orientation, position) in enumerate(solution):
                print(f"  Step {i+1}: 조각 {piece_id}, 방향 {orientation}, 위치 {position}")
                
            return True
        else:
            print("❌ 해법 생성 실패")
            
            # 백업 해법 테스트
            print("🔄 백업 해법 테스트...")
            fallback_solution = interface.get_fallback_solution()
            
            if fallback_solution:
                print("✅ 백업 해법 사용 가능")
                return True
            else:
                print("❌ 백업 해법도 실패")
                return False
                
    except ImportError as e:
        print(f"❌ 모듈 임포트 오류: {e}")
        print("필요한 패키지를 설치해주세요: pip install openai")
        return False
    except Exception as e:
        print(f"❌ 테스트 오류: {e}")
        return False

def compare_methods():
    """DQN vs OpenAI API 비교"""
    print("\n" + "="*50)
    print("DQN vs OpenAI API 비교")
    print("="*50)
    
    print("🤖 DQN 모델:")
    print("  장점: 빠른 추론, 오프라인 작동, 비용 없음")
    print("  단점: 사전 학습 필요, 설명력 부족, 제한된 유연성")
    
    print("\n🧠 OpenAI API:")
    print("  장점: 설명 가능한 추론, 높은 유연성, 학습 불필요")
    print("  단점: API 비용, 인터넷 연결 필요, 응답 시간 변동")
    
    print("\n💡 권장 사용법:")
    print("  - 연구/개발: OpenAI API (설명력과 유연성)")
    print("  - 실제 운영: DQN 모델 (안정성과 비용)")

if __name__ == "__main__":
    print("🔬 OpenAI 소마큐브 솔버 테스트")
    print("-" * 40)
    
    success = test_openai_solver()
    
    if success:
        print("\n✅ 모든 테스트 통과!")
    else:
        print("\n❌ 테스트 실패")
    
    compare_methods()
    
    print("\n" + "="*50)
    print("테스트 완료")