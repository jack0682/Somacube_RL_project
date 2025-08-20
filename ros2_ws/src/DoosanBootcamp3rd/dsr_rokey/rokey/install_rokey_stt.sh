#!/bin/bash

# ROKEY Korean STT Package Installation Script
# 한국어 STT 패키지 설치 스크립트

echo "=================================================================="
echo "🎤 ROKEY 한국어 STT 패키지 설치 도구"
echo "🎤 ROKEY Korean Speech-to-Text Package Installer"
echo "=================================================================="

# 올바른 디렉토리 확인
if [ ! -f "setup.py" ]; then
    echo "❌ 오류: 패키지 루트 디렉토리에서 이 스크립트를 실행하세요"
    echo "❌ Error: Please run this script from the package root directory"
    echo "   예상 위치/Expected location: /home/jack/ros2_ws/src/DoosanBootcamp3rd/dsr_rokey/rokey/"
    exit 1
fi

# Python 버전 확인
python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "🐍 Python 버전/version: $python_version"

if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
    echo "❌ 오류: Python 3.8 이상이 필요합니다"
    echo "❌ Error: Python 3.8 or higher is required"
    exit 1
fi

echo "✅ Python 버전 확인 완료/Python version check passed"

# ROS2 환경 확인
if [ -z "$ROS_DISTRO" ]; then
    echo "⚠️  경고: ROS2 환경이 설정되지 않았습니다"
    echo "⚠️  Warning: ROS2 environment not detected"
    echo "   ROS2 환경을 먼저 설정하세요: source /opt/ros/humble/setup.bash"
    echo "   Please source ROS2 environment first: source /opt/ros/humble/setup.bash"
fi

echo ""
echo "💡 설치 옵션/Installation Options:"
echo "1. 전역 설치 (sudo 필요)/Global installation (requires sudo)"
echo "2. 가상환경 설치 (권장)/Virtual environment installation (recommended)"
echo "3. 개발자 모드 설치/Development mode installation"
echo ""

read -p "설치 방식 선택/Choose installation type (1/2/3): " choice

case $choice in
    1)
        echo "🔧 전역 설치 중.../Installing globally..."
        sudo pip3 install -e .
        install_success=$?
        ;;
    2)
        echo "🔧 가상환경 설정 중.../Setting up virtual environment..."
        
        # 기존 가상환경 제거 확인
        if [ -d "venv" ]; then
            echo "⚠️  기존 가상환경 발견/Existing virtual environment found"
            read -p "기존 가상환경을 삭제하고 새로 만드시겠습니까?/Remove and recreate? (y/n): " remove_venv
            if [[ $remove_venv =~ ^[Yy]$ ]]; then
                rm -rf venv
                echo "🗑️  기존 가상환경 삭제됨/Removed existing virtual environment"
            fi
        fi
        
        python3 -m venv venv
        source venv/bin/activate
        echo "📦 의존성 설치 중.../Installing dependencies..."
        pip install --upgrade pip
        pip install -e .
        install_success=$?
        
        if [ $install_success -eq 0 ]; then
            echo ""
            echo "✅ 설치 완료!/Installation complete!"
            echo "🔧 패키지 사용 전 가상환경을 활성화하세요:"
            echo "🔧 To use the package, activate the virtual environment first:"
            echo "   source $(pwd)/venv/bin/activate"
        fi
        ;;
    3)
        echo "🔧 개발자 모드로 설치 중.../Installing in development mode..."
        pip3 install -e .
        install_success=$?
        ;;
    *)
        echo "❌ 잘못된 선택입니다. 종료합니다./Invalid choice. Exiting."
        exit 1
        ;;
esac

if [ $install_success -ne 0 ]; then
    echo "❌ 설치 실패!/Installation failed!"
    exit 1
fi

echo ""
echo "🎉 패키지 설치 완료!/Package installation completed!"
echo ""
echo "📋 사용 가능한 명령어/Available Commands:"
echo "   rokey-stt           - 한국어 음성-텍스트 노드 시작/Start Korean STT node"
echo "   rokey-trigger       - 시작 신호 테스트 구독자/Start signal test subscriber"  
echo "   rokey-test          - 전체 테스트 환경 실행/Launch full test environment"
echo ""
echo "🔧 사용 예시/Usage Examples:"
echo "   rokey-test                          # 전체 테스트 환경 실행"
echo "   rokey-test --check-only             # 환경 확인만 실행"
echo "   rokey-stt                           # 음성 인식만 실행"
echo "   rokey-trigger                       # 테스트 구독자만 실행"
echo ""

# .env 파일 확인 및 생성
if [ ! -f ".env" ]; then
    echo "🔧 .env 파일 생성 중.../Creating .env file..."
    cat > .env << 'EOF'
# OpenAI API Key for Whisper STT
# OpenAI Whisper STT용 API 키
OPENAI_API_KEY=your_openai_api_key_here

# Audio settings / 오디오 설정
SAMPLE_RATE=16000
CHANNELS=1
CHUNK_SIZE=1024

# STT settings / STT 설정
LANGUAGE=ko
MODEL=whisper-1
TRIGGER_PHRASE=시작해
EOF
    echo "📝 .env 파일이 생성되었습니다/.env file created"
    echo "⚠️  OpenAI API 키를 설정하세요/Please set your OpenAI API key"
fi

# 명령어 사용 가능성 테스트
echo "🧪 설치된 명령어 테스트 중.../Testing installed commands..."

if command -v rokey-stt &> /dev/null; then
    echo "✅ rokey-stt 명령어 사용 가능/rokey-stt command available"
else
    echo "⚠️  rokey-stt 명령어를 찾을 수 없음/rokey-stt command not found in PATH"
    echo "   터미널을 재시작하거나 PATH를 업데이트하세요/Restart terminal or update PATH"
fi

if command -v rokey-test &> /dev/null; then
    echo "✅ rokey-test 명령어 사용 가능/rokey-test command available"
else
    echo "⚠️  rokey-test 명령어를 찾을 수 없음/rokey-test command not found in PATH"
fi

echo ""
echo "🎯 빠른 시작/Quick Start:"
echo "   1. .env 파일에 OpenAI API 키 설정/Set OpenAI API key in .env file"
echo "   2. 실행: rokey-test/Run: rokey-test"
echo "   3. 마이크에 '시작해'라고 말하기/Say '시작해' into microphone"
echo ""
echo "📚 자세한 정보는 ROKEY_STT_README.md 참조"
echo "📚 For more information, see ROKEY_STT_README.md"
echo ""
echo "🎉 한국어 STT 사용 준비 완료! 🇰🇷"
echo "🎉 Ready to use Korean STT! 🇰🇷"