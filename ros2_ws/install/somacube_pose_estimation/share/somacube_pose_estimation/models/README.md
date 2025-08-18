# 모델 디렉토리

이 디렉토리에 훈련된 YOLO 모델 파일(.pt)을 배치하세요.

## 필요한 파일들

1. **somacube_best.pt** - 메인 소마큐브 검출 모델
2. **somacube_segment.pt** - 세그멘테이션 모델 (선택사항)

## 모델 요구사항

- YOLO v8 이상 지원
- 입력 크기: 640x640 (기본값, 설정 변경 가능)
- 클래스: 소마큐브 7개 조각 타입

## 클래스 구조
```
0: piece_L      # L자 조각
1: piece_T      # T자 조각  
2: piece_Z      # Z자 조각
3: piece_O      # O자 조각 (2x2x1)
4: piece_I      # I자 조각 (직선)
5: piece_S      # S자 조각
6: piece_P      # P자 조각
```

## 성능 요구사항

- mAP@0.5 > 0.85
- 실시간 추론 속도 (>30 FPS on CPU)
- False positive rate < 5%

## 사용법

모델 파일을 이 디렉토리에 복사한 후 ROS2 노드를 실행하세요:

```bash
ros2 run somacube_pose_estimation yolo_detector_node.py
```