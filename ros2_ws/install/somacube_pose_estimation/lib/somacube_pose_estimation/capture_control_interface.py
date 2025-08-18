#!/usr/bin/env python3
"""
캡처 제어 인터페이스 노드
SLAM-free 글로벌 맵핑을 위한 사용자 친화적 캡처 제어 시스템
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Bool, Int32
from geometry_msgs.msg import PoseStamped
import json
import threading
import time
import os
import sys
from datetime import datetime
from pathlib import Path


class CaptureControlInterface(Node):
    """캡처 제어 인터페이스"""
    
    def __init__(self):
        super().__init__('capture_control_interface')
        
        # Parameters
        self.declare_parameters_from_yaml()
        
        # Publishers
        self.capture_trigger_pub = self.create_publisher(
            Bool,
            '/synchronized_capture/trigger',
            10
        )
        
        self.pose_index_pub = self.create_publisher(
            Int32,
            '/camera_pose_manager/set_pose_index',
            10
        )
        
        self.next_pose_pub = self.create_publisher(
            String,
            '/camera_pose_manager/next_pose',
            10
        )
        
        self.manual_pose_pub = self.create_publisher(
            PoseStamped,
            '/camera_pose_manager/set_manual_pose',
            10
        )
        
        # Subscribers for status monitoring
        self.capture_status_sub = self.create_subscription(
            String,
            '/synchronized_capture/status',
            self.capture_status_callback,
            10
        )
        
        self.pose_status_sub = self.create_subscription(
            String,
            '/camera_pose_manager/global_map_status',
            self.pose_status_callback,
            10
        )
        
        # State
        self.capture_status = {}
        self.pose_status = {}
        self.current_session = None
        self.interface_mode = 'cli'  # 'cli' or 'auto'
        
        # Interface control
        self.running = True
        self.auto_sequence_active = False
        
        # Start interface
        self.start_interface()
        
        self.get_logger().info('Capture Control Interface initialized')
        self.get_logger().info('Use "help" command for available operations')

    def declare_parameters_from_yaml(self):
        """YAML 설정에서 파라미터 선언"""
        defaults = {
            'capture_control.interface_mode': 'cli',
            'capture_control.auto_sequence_delay_sec': 3.0,
            'capture_control.poses_per_session': 8,
            'capture_control.enable_status_display': True,
            'capture_control.status_refresh_rate_hz': 2.0,
        }
        
        for name, default_value in defaults.items():
            self.declare_parameter(name, default_value)

    def capture_status_callback(self, msg):
        """캡처 상태 콜백"""
        try:
            self.capture_status = json.loads(msg.data)
        except json.JSONDecodeError:
            pass

    def pose_status_callback(self, msg):
        """포즈 상태 콜백"""
        try:
            self.pose_status = json.loads(msg.data)
        except json.JSONDecodeError:
            pass

    def start_interface(self):
        """인터페이스 시작"""
        interface_mode = self.get_parameter('capture_control.interface_mode').value
        
        if interface_mode == 'cli':
            # CLI 인터페이스를 별도 스레드에서 실행
            cli_thread = threading.Thread(target=self.run_cli_interface, daemon=True)
            cli_thread.start()
            
            # 상태 디스플레이
            if self.get_parameter('capture_control.enable_status_display').value:
                status_rate = self.get_parameter('capture_control.status_refresh_rate_hz').value
                self.status_timer = self.create_timer(1.0 / status_rate, self.display_status)
        else:
            self.get_logger().info('Auto mode - waiting for external commands')

    def run_cli_interface(self):
        """CLI 인터페이스 실행"""
        self.print_welcome()
        
        while self.running:
            try:
                command = input("\n[SomaCapture] >>> ").strip().lower()
                
                if command in ['quit', 'exit', 'q']:
                    self.running = False
                    break
                elif command == 'help' or command == 'h':
                    self.print_help()
                elif command == 'status' or command == 's':
                    self.print_detailed_status()
                elif command == 'capture' or command == 'c':
                    self.trigger_capture()
                elif command == 'next' or command == 'n':
                    self.next_pose()
                elif command.startswith('pose '):
                    try:
                        pose_index = int(command.split()[1])
                        self.set_pose_index(pose_index)
                    except (IndexError, ValueError):
                        print("Usage: pose <index>")
                elif command == 'auto' or command == 'a':
                    self.start_auto_sequence()
                elif command == 'stop':
                    self.stop_auto_sequence()
                elif command == 'session':
                    self.print_session_info()
                elif command == 'clear':
                    os.system('clear' if os.name == 'posix' else 'cls')
                elif command == '':
                    continue
                else:
                    print(f"Unknown command: {command}. Type 'help' for available commands.")
                    
            except KeyboardInterrupt:
                print("\nExiting...")
                self.running = False
                break
            except EOFError:
                self.running = False
                break
            except Exception as e:
                print(f"Error: {e}")

    def print_welcome(self):
        """환영 메시지"""
        print("\n" + "="*60)
        print("  SOMA CUBE POSE ESTIMATION - CAPTURE CONTROL INTERFACE")
        print("  SLAM-free Global Mapping System")
        print("="*60)
        print("Type 'help' for available commands")

    def print_help(self):
        """도움말 출력"""
        print("\n=== CAPTURE CONTROL COMMANDS ===")
        print("Basic Commands:")
        print("  capture, c      - Trigger synchronized capture")
        print("  next, n         - Move to next camera pose")
        print("  pose <index>    - Set specific camera pose index")
        print("  status, s       - Show detailed system status")
        print("")
        print("Automation:")
        print("  auto, a         - Start automatic capture sequence")
        print("  stop            - Stop automatic sequence")
        print("")
        print("Utility:")
        print("  session         - Show current session information")
        print("  clear           - Clear screen")
        print("  help, h         - Show this help")
        print("  quit, q         - Exit interface")
        print("")
        print("=== USAGE EXAMPLE ===")
        print("1. pose 0          # Set first camera position")
        print("2. capture         # Capture RGB-Depth data")
        print("3. next            # Move to next position")
        print("4. capture         # Repeat for all poses")
        print("   OR")
        print("1. auto            # Automatic sequence for all poses")

    def print_detailed_status(self):
        """상세 상태 정보 출력"""
        print("\n" + "="*50)
        print("SYSTEM STATUS")
        print("="*50)
        
        # 캡처 상태
        if self.capture_status:
            print("🎥 CAPTURE STATUS:")
            print(f"  Captures taken: {self.capture_status.get('capture_count', 0)}")
            print(f"  Current pose: {self.capture_status.get('current_pose_index', 0)}")
            print(f"  Capture enabled: {self.capture_status.get('capture_enabled', False)}")
            print(f"  Global map points: {self.capture_status.get('global_map_points', 0):,}")
            
            # 동기화 통계
            sync_stats = self.capture_status.get('timestamp_statistics', {})
            if sync_stats.get('count', 0) > 0:
                print(f"  Sync quality: {sync_stats.get('mean_ms', 0):.2f}±{sync_stats.get('std_ms', 0):.2f}ms")
                print(f"  Max sync delta: {sync_stats.get('max_ms', 0):.2f}ms")
            
            # 세션 정보
            session_dir = self.capture_status.get('session_directory', 'N/A')
            print(f"  Session dir: {Path(session_dir).name if session_dir != 'N/A' else 'N/A'}")
            
        # 포즈 매니저 상태
        if self.pose_status:
            print("\n📍 POSE MANAGER STATUS:")
            print(f"  Current pose index: {self.pose_status.get('current_pose_index', 0)}")
            print(f"  Total poses: {self.pose_status.get('total_poses', 0)}")
            print(f"  Mode: {self.pose_status.get('mode', 'unknown')}")
            
            current_pose = self.pose_status.get('current_pose', {})
            if current_pose:
                pos = current_pose.get('position', [0, 0, 0])
                print(f"  Position: [{pos[0]:.3f}, {pos[1]:.3f}, {pos[2]:.3f}]")
        
        # 자동 시퀀스 상태
        print(f"\n🤖 AUTO SEQUENCE: {'ACTIVE' if self.auto_sequence_active else 'INACTIVE'}")
        
        print("="*50)

    def display_status(self):
        """간단한 상태 디스플레이 (타이머 콜백)"""
        # 간단한 상태 라인만 출력 (CLI 방해하지 않음)
        if self.capture_status and not self.auto_sequence_active:
            captures = self.capture_status.get('capture_count', 0)
            pose_idx = self.capture_status.get('current_pose_index', 0)
            global_pts = self.capture_status.get('global_map_points', 0)
            
            # 터미널 제목에 상태 표시 (지원되는 경우)
            if hasattr(sys.stdout, 'write'):
                status_line = f"Captures: {captures} | Pose: {pose_idx} | Points: {global_pts:,}"
                # print(f"\033]0;SomaCapture - {status_line}\007", end='')

    def trigger_capture(self):
        """캡처 트리거"""
        try:
            msg = Bool()
            msg.data = True
            self.capture_trigger_pub.publish(msg)
            print("✅ Capture triggered")
            
            # 캡처 완료 대기 (간단한 피드백)
            time.sleep(0.5)
            
        except Exception as e:
            print(f"❌ Capture trigger failed: {e}")

    def next_pose(self):
        """다음 포즈로 이동"""
        try:
            msg = String()
            msg.data = ""
            self.next_pose_pub.publish(msg)
            print("➡️  Moving to next pose")
            
        except Exception as e:
            print(f"❌ Next pose failed: {e}")

    def set_pose_index(self, index: int):
        """특정 포즈 인덱스 설정"""
        try:
            msg = Int32()
            msg.data = index
            self.pose_index_pub.publish(msg)
            print(f"📍 Set pose index to {index}")
            
        except Exception as e:
            print(f"❌ Set pose index failed: {e}")

    def start_auto_sequence(self):
        """자동 시퀀스 시작"""
        if self.auto_sequence_active:
            print("⚠️  Auto sequence already active")
            return
            
        self.auto_sequence_active = True
        print("🤖 Starting automatic capture sequence...")
        
        # 자동 시퀀스를 별도 스레드에서 실행
        auto_thread = threading.Thread(target=self.run_auto_sequence, daemon=True)
        auto_thread.start()

    def stop_auto_sequence(self):
        """자동 시퀀스 중지"""
        if not self.auto_sequence_active:
            print("⚠️  No auto sequence running")
            return
            
        self.auto_sequence_active = False
        print("🛑 Auto sequence stopped")

    def run_auto_sequence(self):
        """자동 시퀀스 실행"""
        try:
            total_poses = self.get_parameter('capture_control.poses_per_session').value
            delay_sec = self.get_parameter('capture_control.auto_sequence_delay_sec').value
            
            print(f"🎯 Auto sequence: {total_poses} poses with {delay_sec}s delay")
            
            for pose_idx in range(total_poses):
                if not self.auto_sequence_active:
                    print("🛑 Auto sequence interrupted")
                    return
                    
                print(f"\n📍 Pose {pose_idx + 1}/{total_poses}")
                
                # 포즈 설정
                self.set_pose_index(pose_idx)
                time.sleep(delay_sec)  # 포즈 이동 대기
                
                # 캡처
                print("📸 Capturing...")
                self.trigger_capture()
                time.sleep(delay_sec)  # 캡처 완료 대기
                
            print(f"\n✅ Auto sequence completed! {total_poses} poses captured")
            self.auto_sequence_active = False
            
        except Exception as e:
            print(f"❌ Auto sequence error: {e}")
            self.auto_sequence_active = False

    def print_session_info(self):
        """세션 정보 출력"""
        print("\n=== SESSION INFORMATION ===")
        
        if self.capture_status:
            session_dir = self.capture_status.get('session_directory', 'N/A')
            if session_dir != 'N/A':
                session_path = Path(session_dir)
                print(f"Session directory: {session_path}")
                print(f"Session name: {session_path.name}")
                
                # 디렉토리 크기 (대략적)
                if session_path.exists():
                    try:
                        total_size = sum(f.stat().st_size for f in session_path.rglob('*') if f.is_file())
                        size_mb = total_size / (1024 * 1024)
                        print(f"Data size: {size_mb:.1f} MB")
                        
                        # 파일 개수
                        rgb_files = len(list(session_path.rglob('rgb_*.png')))
                        depth_files = len(list(session_path.rglob('depth_*.png')))
                        print(f"Files: {rgb_files} RGB, {depth_files} depth")
                        
                    except Exception as e:
                        print(f"Could not analyze session data: {e}")
                else:
                    print("Session directory does not exist yet")
            else:
                print("No active session")
        else:
            print("No capture status available")


def main(args=None):
    rclpy.init(args=args)
    node = CaptureControlInterface()
    
    try:
        # CLI가 메인 스레드에서 실행되므로 ROS2 스핀은 별도 스레드
        ros_thread = threading.Thread(target=lambda: rclpy.spin(node), daemon=True)
        ros_thread.start()
        
        # 메인 스레드는 인터페이스가 끝날 때까지 대기
        while node.running:
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        pass
    finally:
        node.running = False
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()