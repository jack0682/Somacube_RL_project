#!/usr/bin/env python3
"""
DoosanRobotics M0609 포즈 시퀀스 가이드
로봇 이동을 위한 좌표 시퀀스와 검증 스크립트
"""

import numpy as np
from typing import List, Tuple, Dict

class DoosanPoseSequence:
    """DoosanRobotics M0609 카메라 포즈 시퀀스"""
    
    def __init__(self):
        # 작업 영역 정보
        self.workspace_bounds = {
            'x_min': 424.85,
            'x_max': 499.90,
            'y_min': 3.83,
            'y_max': 78.83,
            'z_table': 12.4
        }
        
        # 블록 놓을 위치들
        self.drop_positions = [
            (424.850, 78.830, 12.400, 20.22, -179.57, 15.42),   # 1번
            (424.870, 3.830, 12.420, 20.3, -179.57, 15.5),     # 2번  
            (499.900, 3.820, 12.440, 20.46, -179.57, 15.66),   # 3번
            (499.900, 78.830, 12.400, 20.4, -179.57, 15.65),   # 4번
        ]
        
        # 카메라 포즈 시퀀스 (gripper 좌표 기준)
        self.camera_poses = [
            {
                'id': 'pose_0_center_top',
                'position': (462.0, 41.0, 312.0),  # 작업 영역 중앙 직상방
                'orientation': (20.0, -179.0, 90.0),
                'description': '작업 영역 중앙 직상방 - 전체 조망',
                'priority': 1  # 가장 중요한 포즈
            },
            {
                'id': 'pose_1_corner1',
                'position': (350.0, 150.0, 262.0),  # 1번 코너 관찰
                'orientation': (35.0, -160.0, 45.0),
                'description': '1번 코너 (424.85, 78.83) 관찰',
                'priority': 2
            },
            {
                'id': 'pose_2_corner2',
                'position': (350.0, -30.0, 262.0),  # 2번 코너 관찰
                'orientation': (35.0, -160.0, 135.0),
                'description': '2번 코너 (424.87, 3.83) 관찰',
                'priority': 2
            },
            {
                'id': 'pose_3_corner3',
                'position': (575.0, -30.0, 262.0),  # 3번 코너 관찰
                'orientation': (35.0, -160.0, 225.0),
                'description': '3번 코너 (499.9, 3.82) 관찰',
                'priority': 2
            },
            {
                'id': 'pose_4_corner4',
                'position': (575.0, 150.0, 262.0),  # 4번 코너 관찰
                'orientation': (35.0, -160.0, 315.0),
                'description': '4번 코너 (499.9, 78.83) 관찰',
                'priority': 2
            },
            {
                'id': 'pose_5_left_side',
                'position': (400.0, 200.0, 212.0),  # 좌측면 전체 관찰
                'orientation': (45.0, -145.0, 60.0),
                'description': '좌측면에서 작업 영역 전체 관찰',
                'priority': 3
            },
            {
                'id': 'pose_6_right_side',
                'position': (525.0, -50.0, 212.0),  # 우측면 전체 관찰
                'orientation': (45.0, -145.0, 240.0),
                'description': '우측면에서 작업 영역 전체 관찰',
                'priority': 3
            },
            {
                'id': 'pose_7_diagonal',
                'position': (400.0, 100.0, 362.0),  # 대각선 종합 관찰
                'orientation': (60.0, -120.0, 90.0),
                'description': '대각선에서 작업 영역 종합 관찰',
                'priority': 3
            }
        ]
    
    def get_pose_sequence(self, priority_level: int = 3) -> List[Dict]:
        """우선순위별 포즈 시퀀스 반환"""
        return [pose for pose in self.camera_poses if pose['priority'] <= priority_level]
    
    def validate_pose_safety(self, position: Tuple[float, float, float]) -> Dict:
        """포즈 안전성 검증"""
        x, y, z = position
        
        safety_report = {
            'safe': True,
            'warnings': [],
            'errors': []
        }
        
        # Z축 안전성 검사
        if z < 150.0:
            safety_report['errors'].append(f"Z축 너무 낮음: {z}mm (최소 150mm 권장)")
            safety_report['safe'] = False
        elif z < 200.0:
            safety_report['warnings'].append(f"Z축 주의: {z}mm (200mm 이상 권장)")
        
        # 작업 영역과의 거리 검사
        workspace_center = (462.0, 41.0)
        distance = np.sqrt((x - workspace_center[0])**2 + (y - workspace_center[1])**2)
        
        if distance > 300.0:
            safety_report['warnings'].append(f"작업 영역에서 멀음: {distance:.1f}mm")
        
        # 로봇 가동 범위 검사 (대략적)
        if not (200.0 <= x <= 700.0):
            safety_report['errors'].append(f"X축 가동 범위 초과: {x}mm")
            safety_report['safe'] = False
            
        if not (-200.0 <= y <= 300.0):
            safety_report['errors'].append(f"Y축 가동 범위 초과: {y}mm")
            safety_report['safe'] = False
            
        if z > 500.0:
            safety_report['warnings'].append(f"Z축 매우 높음: {z}mm")
        
        return safety_report
    
    def print_pose_table(self):
        """포즈 표 출력"""
        print("\n" + "="*80)
        print("DoosanRobotics M0609 - 소마큐브 포즈 추정 카메라 포즈 시퀀스")
        print("="*80)
        
        header = f"{'ID':<8} {'X[mm]':<8} {'Y[mm]':<8} {'Z[mm]':<8} {'A[°]':<8} {'B[°]':<8} {'C[°]':<8} {'설명':<25}"
        print(header)
        print("-" * 80)
        
        for i, pose in enumerate(self.camera_poses):
            pos = pose['position']
            ori = pose['orientation']
            desc = pose['description'][:25]
            
            row = f"{i:<8} {pos[0]:<8.1f} {pos[1]:<8.1f} {pos[2]:<8.1f} {ori[0]:<8.1f} {ori[1]:<8.1f} {ori[2]:<8.1f} {desc:<25}"
            print(row)
            
            # 안전성 검증
            safety = self.validate_pose_safety(pos)
            if not safety['safe']:
                print(f"    ⚠️  ERROR: {', '.join(safety['errors'])}")
            elif safety['warnings']:
                print(f"    ⚡ WARNING: {', '.join(safety['warnings'])}")
        
        print("="*80)
    
    def generate_robot_script(self, script_format: str = 'drl') -> str:
        """로봇 제어 스크립트 생성"""
        if script_format == 'drl':
            return self._generate_drl_script()
        elif script_format == 'python':
            return self._generate_python_script()
        else:
            raise ValueError(f"Unsupported script format: {script_format}")
    
    def _generate_drl_script(self) -> str:
        """DRL (Doosan Robot Language) 스크립트 생성"""
        script = """# DoosanRobotics M0609 소마큐브 포즈 시퀀스
# 각 포즈에서 ROS2 캡처 신호 대기

def main():
    # 초기화
    set_velj(30)  # joint velocity 30%
    set_accj(20)  # joint acceleration 20%
    
    # 안전 위치로 이동
    movej([0, 0, 90, 0, 90, 0], vel=30, acc=20)
    wait(1.0)
    
"""
        
        for i, pose in enumerate(self.camera_poses):
            pos = pose['position']
            ori = pose['orientation']
            desc = pose['description']
            
            script += f"""
    # Pose {i}: {desc}
    print("Moving to Pose {i}: {desc}")
    movel([{pos[0]}, {pos[1]}, {pos[2]}, {ori[0]}, {ori[1]}, {ori[2]}], vel=20, acc=10)
    wait(2.0)  # 안정화 대기
    
    # ROS2 캡처 신호 대기 (수동으로 capture 명령 실행)
    print("Ready for capture at Pose {i}. Execute: [SomaCapture] >>> pose {i}")
    print("Then execute: [SomaCapture] >>> capture")
    tp_popup("Press OK after capture is completed", DR_PM_MESSAGE, DR_PM_OK)
    
"""
        
        script += """
    # 완료 후 안전 위치로 복귀
    print("All poses completed. Returning to safe position.")
    movej([0, 0, 90, 0, 90, 0], vel=30, acc=20)
    
end
"""
        return script
    
    def _generate_python_script(self) -> str:
        """Python 제어 스크립트 생성 (참고용)"""
        script = """#!/usr/bin/env python3
\"\"\"
DoosanRobotics M0609 포즈 시퀀스 제어 스크립트 (참고용)
실제 로봇 제어를 위해서는 Doosan Robot SDK 필요
\"\"\"

import time

# 포즈 시퀀스 데이터
poses = [
"""
        
        for i, pose in enumerate(self.camera_poses):
            pos = pose['position']
            ori = pose['orientation']
            desc = pose['description']
            script += f"    {{'id': {i}, 'pos': {pos}, 'ori': {ori}, 'desc': '{desc}'}},\n"
        
        script += """]

def move_to_pose(pose_data):
    print(f"Moving to Pose {pose_data['id']}: {pose_data['desc']}")
    print(f"Position: {pose_data['pos']} mm")
    print(f"Orientation: {pose_data['ori']} degrees")
    
    # 실제 로봇 제어 코드는 여기에 추가
    # robot.movel(pose_data['pos'] + pose_data['ori'])
    
    time.sleep(2.0)  # 안정화 대기
    input(f"Press Enter after capturing at Pose {pose_data['id']}...")

def main():
    print("DoosanRobotics M0609 소마큐브 포즈 시퀀스")
    print("ROS2 시스템이 실행 중인지 확인하세요:")
    print("ros2 launch somacube_pose_estimation doosan_m0609_soma_cube.launch.py")
    print()
    
    for pose in poses:
        move_to_pose(pose)
    
    print("모든 포즈 완료!")

if __name__ == '__main__':
    main()
"""
        return script


def main():
    """메인 함수 - 포즈 시퀀스 정보 출력"""
    sequence = DoosanPoseSequence()
    
    # 포즈 표 출력
    sequence.print_pose_table()
    
    # 필수 포즈만 출력
    print("\n" + "="*40)
    print("최소 필수 포즈 (Priority 1-2):")
    print("="*40)
    essential_poses = sequence.get_pose_sequence(priority_level=2)
    for i, pose in enumerate(essential_poses):
        pos = pose['position']
        ori = pose['orientation']
        print(f"Pose {i}: {pos} + {ori} - {pose['description']}")
    
    # DRL 스크립트 생성
    print("\n생성된 DRL 스크립트를 파일로 저장하려면:")
    print("python3 doosan_pose_sequence.py > soma_cube_poses.drl")


if __name__ == '__main__':
    main()