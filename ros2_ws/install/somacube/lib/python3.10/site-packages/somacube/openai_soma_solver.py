#!/usr/bin/env python3
"""
OpenAI API 기반 소마큐브 솔버
기존 DQN 모델을 OpenAI GPT 모델로 대체하는 구현
"""

import os
import json
import numpy as np
from typing import List, Tuple, Dict, Optional
from openai import OpenAI
import time

# .env 파일 지원
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️ python-dotenv not installed. Using system environment variables only.")

# 기존 모듈에서 import
from .RL_with_robot2 import BASE_PIECES, ALL_PIECE_ORIENTATIONS, ActionMapper

class OpenAISomaCubeSolver:
    """
    OpenAI API를 사용하여 소마큐브 해법을 생성하는 클래스
    """
    
    def __init__(self, api_key: str = None, model: str = None, max_retries: int = None):
        """
        초기화
        
        Args:
            api_key: OpenAI API 키 (None이면 환경변수에서 읽음)
            model: 사용할 GPT 모델 (None이면 환경변수에서 읽음, 기본: gpt-4o)
            max_retries: API 호출 재시도 횟수 (None이면 환경변수에서 읽음, 기본: 3)
        """
        # .env 파일 또는 환경변수에서 설정 읽기
        self.api_key = api_key or os.getenv('OPENAI_API_KEY', '')
        self.model = model or os.getenv('OPENAI_MODEL', 'gpt-4o')
        self.max_retries = max_retries or int(os.getenv('OPENAI_MAX_RETRIES', '3'))
        
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable or pass api_key parameter.")
        
        self.client = OpenAI(api_key=self.api_key)
        self.action_mapper = ActionMapper()
        
        # 소마큐브 조각 정보를 텍스트로 변환
        self.piece_descriptions = self._create_piece_descriptions()
        
        # 시스템 프롬프트 정의
        self.system_prompt = self._create_system_prompt()
        
        # 대화 히스토리 저장
        self.conversation_history = []
        
        print(f"🧠 OpenAI 솔버 초기화 완료 (Model: {self.model}, Max Retries: {self.max_retries})")
        
    def _create_piece_descriptions(self) -> Dict[int, str]:
        """각 조각의 형태를 텍스트로 설명"""
        descriptions = {
            0: "V piece: L-shaped piece with 3 cubes forming a right angle",
            1: "L piece: 4 cubes in L-shape with longer arm",
            2: "T piece: 4 cubes forming T-shape",
            3: "Z piece: 4 cubes forming Z or S-shape",
            4: "A piece: 4 cubes forming right-handed step shape",
            5: "B piece: 4 cubes forming left-handed step shape", 
            6: "P piece: 4 cubes forming P or mirror-L shape"
        }
        return descriptions
        
    def _create_system_prompt(self) -> str:
        """시스템 프롬프트 생성"""
        return """You are an expert 3D puzzle solver specializing in Soma Cube assembly.

TASK: Generate a complete solution sequence to assemble a 3x3x3 Soma Cube using 7 unique pieces.

PIECES AVAILABLE:
- Piece 0 (V): 3 cubes in L-shape
- Piece 1 (L): 4 cubes in extended L-shape  
- Piece 2 (T): 4 cubes in T-shape
- Piece 3 (Z): 4 cubes in Z/S-shape
- Piece 4 (A): 4 cubes in right-handed step
- Piece 5 (B): 4 cubes in left-handed step
- Piece 6 (P): 4 cubes in P-shape

COORDINATE SYSTEM:
- 3x3x3 grid with coordinates (x,y,z) where each is 0, 1, or 2
- Position (0,0,0) is bottom-left-front corner
- Each piece has multiple possible orientations (rotations)

CONSTRAINTS:
1. Use each piece exactly once
2. Fill entire 3x3x3 cube with no gaps or overlaps
3. Pieces must be physically supported (not floating)
4. Consider piece orientations and rotations

OUTPUT FORMAT:
Return ONLY a valid JSON array with 7 steps:
[
  {"piece_id": 0, "orientation": 0, "position": [0,0,0]},
  {"piece_id": 1, "orientation": 2, "position": [1,0,0]},
  ...
]

IMPORTANT:
- Ensure no pieces overlap
- Ensure all positions are within 0-2 range
- Ensure pieces are properly supported
- Think step by step about placement strategy
"""

    def _grid_state_to_text(self, grid: np.ndarray, placed_pieces: List[int]) -> str:
        """그리드 상태를 텍스트로 변환"""
        text = f"Current 3x3x3 grid state:\n"
        
        for z in range(3):
            text += f"Layer {z} (z={z}):\n"
            for y in range(2, -1, -1):  # y=2부터 y=0까지 (위에서 아래로)
                row = ""
                for x in range(3):
                    cell = grid[x, y, z]
                    row += f"{cell:2d} "
                text += f"  {row}\n"
            text += "\n"
        
        text += f"Remaining pieces to place: {[i for i in range(7) if i not in placed_pieces]}\n"
        text += f"Placed pieces: {placed_pieces}\n"
        
        return text
    
    def solve_soma_cube(self, max_retries: int = None) -> Optional[List[Tuple[int, int, Tuple[int, int, int]]]]:
        """
        OpenAI API를 사용하여 소마큐브 해법 생성
        
        Args:
            max_retries: API 호출 재시도 횟수 (None이면 초기화시 설정된 값 사용)
            
        Returns:
            해법 시퀀스 또는 None (실패시)
        """
        max_retries = max_retries or self.max_retries
        for attempt in range(max_retries):
            try:
                print(f"OpenAI API 호출 시도 {attempt + 1}/{max_retries}")
                
                # 사용자 프롬프트 생성
                user_prompt = """Generate a complete Soma Cube solution.

Please provide a step-by-step solution that:
1. Places all 7 pieces in the 3x3x3 grid
2. Ensures no overlaps or gaps
3. Follows physical constraints (support, no floating pieces)

Think through the placement strategy:
- Start with larger/more constrained pieces
- Consider corner and edge placements first
- Ensure each piece fits within remaining space
- Verify no conflicts with previously placed pieces

Return the solution as a JSON array of 7 placement instructions."""

                # API 호출
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.3,  # 일관성을 위해 낮은 온도
                    max_tokens=2000
                )
                
                solution_text = response.choices[0].message.content.strip()
                print(f"OpenAI 응답:\n{solution_text}")
                
                # JSON 파싱 시도
                solution = self._parse_solution(solution_text)
                
                if solution:
                    # 해법 유효성 검증
                    if self._validate_solution(solution):
                        print("✅ 유효한 해법 생성 성공!")
                        return solution
                    else:
                        print(f"❌ 해법 유효성 검증 실패 (시도 {attempt + 1})")
                else:
                    print(f"❌ 해법 파싱 실패 (시도 {attempt + 1})")
                    
            except Exception as e:
                print(f"❌ API 호출 오류 (시도 {attempt + 1}): {str(e)}")
                time.sleep(1)  # 재시도 전 대기
                
        print("❌ 모든 시도 실패")
        return None
    
    def _parse_solution(self, solution_text: str) -> Optional[List[Tuple[int, int, Tuple[int, int, int]]]]:
        """
        OpenAI 응답에서 해법 추출
        
        Args:
            solution_text: OpenAI API 응답 텍스트
            
        Returns:
            파싱된 해법 또는 None
        """
        try:
            # JSON 부분 추출
            start_idx = solution_text.find('[')
            end_idx = solution_text.rfind(']') + 1
            
            if start_idx == -1 or end_idx == 0:
                return None
                
            json_text = solution_text[start_idx:end_idx]
            solution_data = json.loads(json_text)
            
            # 형식 변환: OpenAI 형식 -> 기존 시스템 형식
            solution = []
            for step in solution_data:
                piece_id = step["piece_id"]
                orientation = step["orientation"]
                position = tuple(step["position"])
                
                solution.append((piece_id, orientation, position))
                
            return solution
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"JSON 파싱 오류: {str(e)}")
            return None
    
    def _validate_solution(self, solution: List[Tuple[int, int, Tuple[int, int, int]]]) -> bool:
        """
        생성된 해법의 유효성 검증
        
        Args:
            solution: 검증할 해법
            
        Returns:
            유효성 여부
        """
        if len(solution) != 7:
            print(f"잘못된 해법 길이: {len(solution)} (expected: 7)")
            return False
            
        # 사용된 조각 ID 확인
        used_pieces = set()
        grid = np.zeros((3, 3, 3), dtype=int)
        
        for step_idx, (piece_id, orientation, position) in enumerate(solution):
            # 중복 조각 확인
            if piece_id in used_pieces:
                print(f"중복 조각 사용: {piece_id}")
                return False
            used_pieces.add(piece_id)
            
            # 유효 범위 확인
            if not (0 <= piece_id <= 6):
                print(f"잘못된 조각 ID: {piece_id}")
                return False
                
            x, y, z = position
            if not (0 <= x <= 2 and 0 <= y <= 2 and 0 <= z <= 2):
                print(f"잘못된 위치: {position}")
                return False
                
            # 방향 인덱스 확인
            if orientation < 0 or orientation >= len(ALL_PIECE_ORIENTATIONS[piece_id]):
                print(f"잘못된 방향 인덱스: {orientation} for piece {piece_id}")
                return False
                
            # 조각 배치 가능성 확인
            piece_coords = ALL_PIECE_ORIENTATIONS[piece_id][orientation]
            
            for rel_x, rel_y, rel_z in piece_coords:
                abs_x = position[0] + rel_x
                abs_y = position[1] + rel_y
                abs_z = position[2] + rel_z
                
                # 범위 확인
                if not (0 <= abs_x <= 2 and 0 <= abs_y <= 2 and 0 <= abs_z <= 2):
                    print(f"조각이 그리드를 벗어남: ({abs_x}, {abs_y}, {abs_z})")
                    return False
                    
                # 겹침 확인
                if grid[abs_x, abs_y, abs_z] != 0:
                    print(f"겹침 발생: ({abs_x}, {abs_y}, {abs_z})")
                    return False
                    
                grid[abs_x, abs_y, abs_z] = piece_id + 1
        
        # 전체 그리드가 채워졌는지 확인
        if np.sum(grid == 0) != 0:
            print(f"빈 공간 존재: {np.sum(grid == 0)}개")
            return False
            
        print("✅ 해법 유효성 검증 통과")
        return True
    
    def solve_with_feedback(self, feedback: str = "") -> Optional[List[Tuple[int, int, Tuple[int, int, int]]]]:
        """
        피드백을 반영한 해법 생성
        
        Args:
            feedback: 이전 해법에 대한 피드백
            
        Returns:
            개선된 해법 또는 None
        """
        user_prompt = f"""Generate an improved Soma Cube solution.

Previous feedback: {feedback}

Please provide a better solution that addresses the feedback.
Consider:
1. Different placement strategies
2. Alternative piece orientations  
3. Better space utilization
4. Physical constraints and stability

Return the solution as a JSON array of 7 placement instructions."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.5,  # 다양성을 위해 약간 높은 온도
                max_tokens=2000
            )
            
            solution_text = response.choices[0].message.content.strip()
            solution = self._parse_solution(solution_text)
            
            if solution and self._validate_solution(solution):
                return solution
                
        except Exception as e:
            print(f"피드백 기반 해법 생성 오류: {str(e)}")
            
        return None


class OpenAISomaCubeInterface:
    """
    기존 시스템과 OpenAI 솔버를 연결하는 인터페이스
    """
    
    def __init__(self, api_key: str = None):
        """
        초기화
        
        Args:
            api_key: OpenAI API 키 (None이면 .env 파일에서 읽음)
        """
        try:
            self.solver = OpenAISomaCubeSolver(api_key=api_key)
        except ValueError as e:
            print(f"❌ OpenAI 솔버 초기화 실패: {e}")
            raise
        
    def generate_solution_path(self) -> Optional[List[Tuple[int, int, Tuple[int, int, int]]]]:
        """
        기존 main() 함수에서 사용할 수 있는 해법 생성
        
        Returns:
            DQN과 동일한 형식의 해법 시퀀스
        """
        print("🧠 OpenAI API로 소마큐브 해법 생성 중...")
        
        solution = self.solver.solve_soma_cube()
        
        if solution:
            print("✅ OpenAI 기반 해법 생성 성공!")
            
            # 해법 정보 출력
            print("\n생성된 해법:")
            for i, (piece_id, orientation, position) in enumerate(solution):
                print(f"  Step {i+1}: 조각 {piece_id}, 방향 {orientation}, 위치 {position}")
                
            return solution
        else:
            print("❌ OpenAI 해법 생성 실패")
            return None
    
    def get_fallback_solution(self) -> List[Tuple[int, int, Tuple[int, int, int]]]:
        """
        API 실패시 사용할 기본 해법
        """
        # 알려진 유효한 소마큐브 해법 중 하나
        return [
            (0, 0, (0, 0, 0)),  # V piece
            (1, 1, (1, 0, 0)),  # L piece
            (2, 0, (0, 1, 0)),  # T piece
            (3, 2, (2, 0, 0)),  # Z piece
            (4, 1, (0, 0, 1)),  # A piece
            (5, 0, (1, 1, 1)),  # B piece
            (6, 3, (2, 2, 0))   # P piece
        ]