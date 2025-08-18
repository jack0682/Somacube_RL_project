"""
소마큐브 6DoF 포즈 추정: 수학적 정밀 체계

이 패키지는 수학적으로 엄밀한 이론을 바탕으로 소마큐브 조각들의 
6DoF 포즈를 추정하는 시스템을 제공합니다.

핵심 구성요소:
- YOLO 기반 객체 검출
- 점군 전처리 및 세그멘테이션  
- PCA 기반 축 추정
- 맨해튼 정렬 및 자세 복원
- 멀티뷰 융합
- 수학적 품질 검증
"""

__version__ = "1.0.0"
__author__ = "Soma Cube Team"

# Mathematical foundations
from .mathematical_foundations import *
from .pointcloud_processing import *
from .pose_estimation import *
from .multiview_fusion import *