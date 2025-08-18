# OpenAI API를 활용한 소마큐브 조립 시스템

기존 DQN 모델을 OpenAI GPT 모델로 대체하여 소마큐브 해법을 생성하는 시스템입니다.

## 🚀 주요 기능

### 🧠 지능형 해법 생성
- **DQN 모델**: 기존 강화학습 기반 해법 생성
- **OpenAI API**: GPT-4o를 사용한 지능형 해법 생성
- **하이브리드 시스템**: 두 방식을 선택적으로 사용 가능

### 🤖 AI 기반 그랩 최적화
- **지능형 그리퍼 자세 최적화**: 물리적 제약조건을 고려한 최적 자세 계산
- **특이점 감지 및 회피**: 조인트별 특이점 실시간 감지 및 회피 전략
- **충돌 위험 평가**: AI 기반 충돌 위험 예측 및 회피
- **적응형 학습**: 실행 결과를 기반으로 한 실시간 성능 개선

### 🔧 통합 시스템
- **로봇 통합**: 실제 로봇 팔을 사용한 물리적 조립
- **완벽한 호환성**: 기존 시스템과 100% 호환되는 인터페이스

## 📋 사전 요구사항

### 필수 패키지
```bash
pip install -r requirements.txt
```

### 패키지 목록
- `openai>=1.0.0`
- `python-dotenv>=1.0.0`
- `numpy`
- `torch`
- `scipy`

## 🔧 설정 방법

### 1. .env 파일 생성
```bash
cp .env.example .env
```

### 2. .env 파일 편집
```env
# OpenAI API 설정
OPENAI_API_KEY=your_openai_api_key_here

# 사용할 GPT 모델 (선택사항)
OPENAI_MODEL=gpt-4o

# API 호출 재시도 횟수 (선택사항)
OPENAI_MAX_RETRIES=3
```

### 3. OpenAI API 키 발급
1. [OpenAI 웹사이트](https://platform.openai.com/)에서 계정 생성
2. API 키 생성
3. `.env` 파일에 키 입력

## 🏃‍♂️ 실행 방법

### 기본 실행
```bash
ros2 run somacube RL_with_robot2
```

### 테스트 실행
```bash
python test_openai_solver.py
```

## 🤖 사용 방법

1. **해법 생성 방식 선택**:
   - `1`: DQN 모델 (기존)
   - `2`: OpenAI API (GPT-4o)

2. **OpenAI 모드 선택시**:
   - `.env` 파일에서 자동으로 API 키 로드
   - 없으면 수동 입력 요청

3. **로봇 조립 실행**:
   - 생성된 해법으로 실제 로봇 조립 수행

## 📊 장단점 비교

### 🤖 DQN 모델
**장점:**
- 빠른 추론 속도
- 오프라인 작동 가능
- 운영 비용 없음
- 일관된 성능

**단점:**
- 사전 학습 필요
- 설명력 부족
- 제한된 유연성

### 🧠 OpenAI API
**장점:**
- 설명 가능한 추론
- 높은 유연성
- 학습 과정 불필요
- 다양한 전략 시도

**단점:**
- API 사용 비용
- 인터넷 연결 필수
- 응답 시간 변동
- 외부 서비스 의존

## 🔍 디버깅

### API 키 관련 문제
```bash
# 환경변수 확인
echo $OPENAI_API_KEY

# .env 파일 확인
cat .env
```

### 의존성 문제
```bash
# 패키지 설치 확인
pip list | grep openai
pip list | grep dotenv
```

### 로그 확인
- OpenAI API 호출 과정과 응답을 콘솔에서 확인 가능
- 해법 유효성 검증 결과도 실시간 출력

## 🎯 권장 사용법

- **연구/개발 단계**: OpenAI API 사용 (설명력과 유연성)
- **실제 운영 환경**: DQN 모델 사용 (안정성과 비용 효율)
- **하이브리드 운영**: 평소는 DQN, 실패시 OpenAI로 대안 해법 생성

## 🛠 커스터마이징

### 모델 변경
`.env` 파일에서 `OPENAI_MODEL` 설정:
- `gpt-4o`: 권장 (최고 성능)
- `gpt-4`: 대안
- `gpt-3.5-turbo`: 저비용 옵션

### 재시도 횟수 조정
```env
OPENAI_MAX_RETRIES=5  # 기본값: 3
```

## 📞 지원

문제가 발생하면 다음을 확인하세요:
1. API 키가 올바르게 설정되었는지
2. 인터넷 연결 상태
3. OpenAI 계정의 사용량 한도
4. 필요한 패키지가 모두 설치되었는지