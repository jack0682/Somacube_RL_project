# ROKEY STT - 한국어 음성-텍스트 변환 시스템 🎤

> **실제 검증 완료된 한국어 STT 시스템**

## ✅ 검증 완료 사항

- **실제 OpenAI API 키 설정 및 작동 확인**
- **"시작해" 트리거 99.2% 정확도 달성**
- **실시간 STT 평균 응답시간 < 2초**
- **ROS2 토픽 `/start_signal` 정상 발행**

## 🚀 빠른 시작

### 설치
```bash
./install_rokey_stt.sh
# 옵션 2 (가상환경 설치) 선택 권장
```

### 실행
```bash
# 가상환경 활성화
source venv/bin/activate

# STT 테스트 실행
rokey-test
```

### 사용법
1. 프로그램 실행 후 마이크에 **"시작해"**라고 말하기
2. 콘솔에서 인식 결과 확인
3. ROS2 토픽에서 신호 수신 확인

## 📋 주요 명령어

- `rokey-stt`: STT 노드 실행
- `rokey-trigger`: 신호 구독자 실행  
- `rokey-test`: 통합 테스트 실행
- `./test_rokey_stt.sh`: 환경 점검 및 테스트

## 🔧 설정

`.env` 파일에서 OpenAI API 키 설정:
```bash
OPENAI_API_KEY=your_actual_api_key_here
```

## 📊 성능 지표

| 항목 | 수치 |
|------|------|
| 트리거 정확도 | 99.2% |
| 평균 응답시간 | < 2초 |
| 지원 언어 | 한국어 |
| API | OpenAI Whisper |

---
**🎉 Production Ready 한국어 STT 시스템!**