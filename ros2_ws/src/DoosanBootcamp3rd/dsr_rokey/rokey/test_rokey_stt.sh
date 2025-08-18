#!/bin/bash

# ROKEY Korean STT Package Test Script
# 한국어 STT 패키지 테스트 스크립트

echo "=================================================================="
echo "🧪 ROKEY 한국어 STT 패키지 테스트 도구"
echo "🧪 ROKEY Korean Speech-to-Text Package Test Tool"
echo "=================================================================="

# 기본 변수
CHECK_ONLY=false
FULL_TEST=false

# 인자 처리
while [[ $# -gt 0 ]]; do
    case $1 in
        --check-only)
            CHECK_ONLY=true
            shift
            ;;
        --full)
            FULL_TEST=true
            shift
            ;;
        -h|--help)
            echo "사용법/Usage:"
            echo "  $0                    # 기본 테스트/Basic test"
            echo "  $0 --check-only       # 환경 확인만/Environment check only"
            echo "  $0 --full             # 전체 테스트/Full test"
            exit 0
            ;;
        *)
            echo "❌ 알 수 없는 옵션/Unknown option: $1"
            exit 1
            ;;
    esac
done

# 환경 확인 함수
check_environment() {
    echo "🔍 환경 확인 중.../Checking environment..."
    
    # Python 버전 확인
    if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)" 2>/dev/null; then
        echo "❌ Python 3.8+ 필요/Python 3.8+ required"
        return 1
    fi
    echo "✅ Python 버전 확인/Python version check"
    
    # ROS2 환경 확인
    if [ -z "$ROS_DISTRO" ]; then
        echo "⚠️  ROS2 환경 미설정/ROS2 environment not set"
        echo "   source /opt/ros/humble/setup.bash"
    else
        echo "✅ ROS2 환경 ($ROS_DISTRO) 확인/ROS2 environment check"
    fi
    
    # .env 파일 확인
    if [ ! -f ".env" ]; then
        echo "❌ .env 파일 없음/.env file missing"
        echo "   ./install_rokey_stt.sh 를 먼저 실행하세요"
        return 1
    fi
    echo "✅ .env 파일 확인/.env file check"
    
    # OpenAI API 키 확인
    if grep -q "your_openai_api_key" .env; then
        echo "⚠️  OpenAI API 키 미설정/OpenAI API key not configured"
        echo "   .env 파일에서 API 키를 설정하세요"
    else
        echo "✅ OpenAI API 키 설정됨/OpenAI API key configured"
    fi
    
    # 패키지 설치 확인
    if ! command -v rokey-stt &> /dev/null; then
        echo "❌ rokey-stt 명령어 없음/rokey-stt command not found"
        echo "   ./install_rokey_stt.sh 를 먼저 실행하세요"
        return 1
    fi
    echo "✅ rokey-stt 명령어 확인/rokey-stt command check"
    
    return 0
}

# 마이크 테스트 함수
test_microphone() {
    echo ""
    echo "🎤 마이크 테스트/Microphone test..."
    
    # 마이크 장치 확인
    if command -v arecord &> /dev/null; then
        echo "📊 사용 가능한 마이크 장치/Available microphone devices:"
        arecord -l | grep -E "card|device" || echo "   마이크 장치를 찾을 수 없음/No microphone devices found"
    fi
    
    # 오디오 권한 확인
    if [ ! -r /dev/snd/controlC0 ] 2>/dev/null; then
        echo "⚠️  오디오 장치 접근 권한 확인 필요/Audio device permission check needed"
        echo "   사용자가 audio 그룹에 속해있는지 확인하세요"
    else
        echo "✅ 오디오 장치 접근 권한/Audio device access permission"
    fi
}

# Python 모듈 테스트
test_dependencies() {
    echo ""
    echo "📦 의존성 모듈 테스트/Dependencies test..."
    
    local modules=("openai" "rclpy" "std_msgs" "pyaudio")
    local all_ok=true
    
    for module in "${modules[@]}"; do
        if python3 -c "import $module" 2>/dev/null; then
            echo "✅ $module 모듈 사용 가능/$module module available"
        else
            echo "❌ $module 모듈 없음/$module module missing"
            all_ok=false
        fi
    done
    
    if [ "$all_ok" = true ]; then
        echo "✅ 모든 의존성 모듈 확인/All dependencies available"
    else
        echo "❌ 일부 의존성 모듈 누락/Some dependencies missing"
        echo "   pip install -e . 를 다시 실행해보세요"
    fi
}

# 실제 STT 테스트
run_stt_test() {
    echo ""
    echo "🎯 STT 기능 테스트/STT functionality test..."
    echo "⚠️  이 테스트는 실제 OpenAI API를 사용합니다"
    echo "⚠️  This test uses actual OpenAI API"
    
    read -p "계속하시겠습니까?/Continue? (y/n): " continue_test
    if [[ ! $continue_test =~ ^[Yy]$ ]]; then
        echo "테스트 중단됨/Test cancelled"
        return 0
    fi
    
    echo ""
    echo "🎙️  STT 테스트를 시작합니다..."
    echo "🎙️  Starting STT test..."
    echo "   마이크에 '시작해'라고 말해보세요"
    echo "   Say '시작해' into the microphone"
    echo "   (Ctrl+C로 중단/Press Ctrl+C to stop)"
    echo ""
    
    # 백그라운드에서 rokey-test 실행
    timeout 30s rokey-test 2>/dev/null &
    test_pid=$!
    
    echo "✅ STT 테스트 실행 중... (30초 후 자동 종료)"
    echo "✅ STT test running... (auto-stop after 30 seconds)"
    
    wait $test_pid
    echo ""
    echo "🏁 STT 테스트 완료/STT test completed"
}

# 메인 실행
main() {
    # 올바른 디렉토리 확인
    if [ ! -f "setup.py" ]; then
        echo "❌ 패키지 루트 디렉토리에서 실행하세요"
        echo "❌ Please run from package root directory"
        exit 1
    fi
    
    # 환경 확인
    if ! check_environment; then
        echo ""
        echo "❌ 환경 확인 실패/Environment check failed"
        echo "   ./install_rokey_stt.sh 를 먼저 실행하세요"
        exit 1
    fi
    
    if [ "$CHECK_ONLY" = true ]; then
        echo ""
        echo "🎉 환경 확인 완료!/Environment check completed!"
        return 0
    fi
    
    # 마이크 테스트
    test_microphone
    
    # 의존성 테스트
    test_dependencies
    
    # 전체 테스트인 경우 STT 테스트도 실행
    if [ "$FULL_TEST" = true ]; then
        run_stt_test
    fi
    
    echo ""
    echo "=================================================================="
    echo "🎉 ROKEY STT 패키지 테스트 완료!"
    echo "🎉 ROKEY STT Package Test Completed!"
    echo "=================================================================="
    echo ""
    echo "📋 빠른 사용법/Quick Usage:"
    echo "   rokey-test              # 통합 테스트 실행"
    echo "   rokey-stt               # STT만 실행"  
    echo "   rokey-trigger           # 신호 구독자만 실행"
    echo ""
    echo "🔧 문제 해결/Troubleshooting:"
    echo "   1. API 키 확인: .env 파일에서 OPENAI_API_KEY 설정"
    echo "   2. 마이크 권한: sudo usermod -a -G audio $USER"
    echo "   3. 재설치: ./install_rokey_stt.sh"
}

# 스크립트 실행
main "$@"