#!/usr/bin/env python3
"""
Data Simulation Script for SomaCube RL System Testing
Publishes realistic simulated data to test the pipeline without real hardware
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
import numpy as np
import time
import json
from typing import Dict, List
import argparse
from dataclasses import dataclass

# ROS messages
from std_msgs.msg import String, Header
from geometry_msgs.msg import WrenchStamped, Wrench, Vector3, PoseStamped, Pose, Point, Quaternion
from sensor_msgs.msg import PointCloud2, Image, CameraInfo
from builtin_interfaces.msg import Time as RosTime
from doosan_somacube_rl.msg import RegisterQuality, SafetyEvent, PolicyCmd

@dataclass
class SimulationParams:
    """Simulation parameters"""
    register_rate: float = 30.0
    ft_rate: float = 100.0
    safety_event_rate: float = 0.1  # Events per second
    kpi_rate: float = 0.5  # Every 2 seconds
    noise_level: float = 0.1
    scenario: str = "normal"  # normal, degraded, failure

class DataSimulator(Node):
    def __init__(self, params: SimulationParams):
        super().__init__('data_simulator')
        
        self.params = params
        self.start_time = time.time()
        
        # QoS profiles
        reliable_qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10
        )
        
        sensor_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=5
        )
        
        # Publishers
        self.setup_publishers(reliable_qos, sensor_qos)
        
        # Simulation state
        self.sim_state = {
            'phase': 'approach',  # approach, align, place, settle
            'insertion_depth': 0.0,
            'geodesic_error': 15.0,  # Start misaligned
            'force_buildup': 0.0,
            'quality_trend': 'improving',
            'last_safety_event': 0.0,
            'episode_count': 0
        }
        
        # Create timers
        self.setup_timers()
        
        self.get_logger().info(f'Data simulator started - Scenario: {params.scenario}')

    def setup_publishers(self, reliable_qos, sensor_qos):
        """Setup all publishers"""
        
        self.quality_pub = self.create_publisher(
            RegisterQuality, '/pc_register/quality', sensor_qos)
        
        self.pose_pub = self.create_publisher(
            PoseStamped, '/pose/filtered', sensor_qos)
        
        self.ft_pub = self.create_publisher(
            WrenchStamped, '/ee/ft', sensor_qos)
        
        self.safety_pub = self.create_publisher(
            SafetyEvent, '/safety/events', reliable_qos)
        
        self.kpi_pub = self.create_publisher(
            String, '/kpi/state', reliable_qos)
        
        self.policy_pub = self.create_publisher(
            PolicyCmd, '/policy/lo/cmd', reliable_qos)
        
        self.sequencer_pub = self.create_publisher(
            String, '/sequencer/state', reliable_qos)
        
        # Optional: simulated camera/point cloud data
        self.pointcloud_pub = self.create_publisher(
            PointCloud2, '/pc_preprocess/output', sensor_qos)

    def setup_timers(self):
        """Setup simulation timers"""
        
        # Registration quality updates
        self.create_timer(1.0 / self.params.register_rate, self.publish_quality)
        
        # Force/torque data
        self.create_timer(1.0 / self.params.ft_rate, self.publish_forces)
        
        # KPI updates
        self.create_timer(1.0 / self.params.kpi_rate, self.publish_kpis)
        
        # Scenario updates (state machine)
        self.create_timer(0.1, self.update_simulation_state)
        
        # Periodic safety events
        self.create_timer(2.0, self.maybe_publish_safety_event)
        
        # Policy commands (shadow mode)
        self.create_timer(1.0 / 50.0, self.publish_policy_cmd)

    def get_current_time_msg(self):
        """Get current ROS time message"""
        now = self.get_clock().now()
        return now.to_msg()

    def add_noise(self, value: float, relative: bool = True) -> float:
        """Add realistic noise to a value"""
        if relative:
            noise = np.random.normal(0, abs(value) * self.params.noise_level)
        else:
            noise = np.random.normal(0, self.params.noise_level)
        return value + noise

    def update_simulation_state(self):
        """Update simulation state machine"""
        elapsed = time.time() - self.start_time
        state = self.sim_state
        
        # Phase transitions based on quality and time
        if state['phase'] == 'approach':
            # Approach phase: gradually improve alignment
            if state['geodesic_error'] > 5.0:
                state['geodesic_error'] -= 0.1
            else:
                state['phase'] = 'align'
                self.get_logger().info("Simulation: Transition to ALIGN phase")
        
        elif state['phase'] == 'align':
            # Alignment phase: fine-tune orientation
            if state['geodesic_error'] > 1.5:
                state['geodesic_error'] -= 0.05
            else:
                state['phase'] = 'place'
                self.get_logger().info("Simulation: Transition to PLACE phase")
        
        elif state['phase'] == 'place':
            # Placement phase: insert with increasing forces
            state['insertion_depth'] += 0.0001  # 0.1mm per update
            state['force_buildup'] += 0.1
            
            if state['insertion_depth'] > 0.005:  # 5mm insertion
                state['phase'] = 'settle'
                self.get_logger().info("Simulation: Transition to SETTLE phase")
        
        elif state['phase'] == 'settle':
            # Settlement phase: stabilize
            if elapsed % 30 < 25:  # Most of the time
                state['geodesic_error'] = max(0.5, state['geodesic_error'] - 0.01)
                state['force_buildup'] = max(2.0, state['force_buildup'] - 0.05)
            else:
                # Reset for next episode
                state['phase'] = 'approach'
                state['geodesic_error'] = 15.0 + np.random.uniform(-5, 5)
                state['insertion_depth'] = 0.0
                state['force_buildup'] = 0.0
                state['episode_count'] += 1
                self.get_logger().info(f"Simulation: Episode {state['episode_count']} started")
        
        # Apply scenario-specific modifications
        if self.params.scenario == "degraded":
            state['geodesic_error'] += 0.1  # Slower convergence
            state['force_buildup'] += 0.5   # Higher forces
        elif self.params.scenario == "failure":
            if elapsed % 45 < 5:  # Periodic failures
                state['geodesic_error'] += 2.0
                state['force_buildup'] += 5.0

    def publish_quality(self):
        """Publish registration quality metrics"""
        state = self.sim_state
        
        msg = RegisterQuality()
        msg.stamp = self.get_current_time_msg()
        
        # Realistic quality metrics based on simulation state
        base_geodesic = state['geodesic_error']
        msg.geodesic_deg = self.add_noise(base_geodesic)
        
        # Point-to-plane distance correlates with geodesic error
        base_p2p = base_geodesic * 0.0002 + 0.0001  # mm scale
        msg.mean_point2plane_m = max(0.00005, self.add_noise(base_p2p))
        
        # Inlier ratio improves as alignment gets better
        base_inlier = max(0.3, min(0.9, 0.9 - base_geodesic * 0.03))
        msg.inlier_ratio = self.add_noise(base_inlier, relative=False)
        
        # ICP residual standard deviation
        base_residual = base_p2p * 2.0
        msg.icp_residual_std = max(0.0001, self.add_noise(base_residual))
        
        # Chamfer distance
        base_chamfer = base_p2p * 1.5
        msg.chamfer_bidir_m = max(0.00008, self.add_noise(base_chamfer))
        
        self.quality_pub.publish(msg)

    def publish_forces(self):
        """Publish force/torque data"""
        state = self.sim_state
        
        msg = WrenchStamped()
        msg.header.stamp = self.get_current_time_msg()
        msg.header.frame_id = "tool0"
        
        # Base forces depend on insertion depth and contact
        base_fz = state['force_buildup']
        if state['phase'] in ['place', 'settle']:
            base_fz += 5.0  # Contact forces
        
        # Add realistic force patterns
        msg.wrench.force.x = self.add_noise(0.5 * np.sin(time.time() * 0.1))
        msg.wrench.force.y = self.add_noise(0.3 * np.cos(time.time() * 0.15))
        msg.wrench.force.z = self.add_noise(base_fz)
        
        # Torques from misalignment
        torque_scale = state['geodesic_error'] * 0.1
        msg.wrench.torque.x = self.add_noise(torque_scale * np.sin(time.time() * 0.2))
        msg.wrench.torque.y = self.add_noise(torque_scale * np.cos(time.time() * 0.18))
        msg.wrench.torque.z = self.add_noise(torque_scale * 0.5)
        
        self.ft_pub.publish(msg)

    def publish_policy_cmd(self):
        """Publish RL policy commands (shadow mode)"""
        state = self.sim_state
        
        msg = PolicyCmd()
        msg.header.stamp = self.get_current_time_msg()
        msg.header.frame_id = "base"
        
        # Policy tries to correct errors
        error_scale = min(1.0, state['geodesic_error'] / 10.0)
        
        # Position corrections (small, safety-gated)
        msg.dx = self.add_noise(error_scale * 0.001 * np.random.randn())
        msg.dy = self.add_noise(error_scale * 0.001 * np.random.randn())
        msg.dz = self.add_noise(-0.0005 if state['phase'] == 'place' else 0.0)
        
        # Rotation corrections
        msg.droll = self.add_noise(error_scale * 0.02 * np.random.randn())
        msg.dpitch = self.add_noise(error_scale * 0.02 * np.random.randn())
        msg.dyaw = self.add_noise(error_scale * 0.01 * np.random.randn())
        
        # Impedance adjustments
        msg.d_kp = self.add_noise(0.0)  # Usually no change
        msg.d_kd = self.add_noise(0.0)
        
        self.policy_pub.publish(msg)

    def maybe_publish_safety_event(self):
        """Occasionally publish safety events"""
        state = self.sim_state
        now = time.time()
        
        # Event probability based on scenario
        if self.params.scenario == "normal":
            event_prob = 0.05  # 5% chance per check
        elif self.params.scenario == "degraded":
            event_prob = 0.15  # 15% chance
        else:  # failure
            event_prob = 0.3   # 30% chance
        
        if np.random.random() < event_prob:
            msg = SafetyEvent()
            msg.stamp = self.get_current_time_msg()
            
            # Different event types
            event_types = [
                ("force_limit", "Force limit approached", 2),
                ("vision_timeout", "Vision processing timeout", 1),
                ("collision_detected", "Contact force spike", 3),
                ("motion_limit", "Joint limit approached", 2),
                ("quality_degraded", "Registration quality poor", 2),
            ]
            
            event_type, detail, severity = event_types[np.random.randint(len(event_types))]
            
            # Higher severity in failure mode
            if self.params.scenario == "failure" and severity < 3:
                severity += 1
            
            msg.type = event_type
            msg.detail = f"{detail} (sim: {state['phase']})"
            msg.severity = severity
            
            self.safety_pub.publish(msg)
            state['last_safety_event'] = now

    def publish_kpis(self):
        """Publish system KPI data"""
        state = self.sim_state
        elapsed = time.time() - self.start_time
        
        # Calculate success rate (sliding window)
        episodes = max(1, state['episode_count'])
        if self.params.scenario == "normal":
            success_rate = 0.85 + 0.1 * np.random.randn()
        elif self.params.scenario == "degraded":
            success_rate = 0.65 + 0.1 * np.random.randn()
        else:  # failure
            success_rate = 0.35 + 0.15 * np.random.randn()
        
        success_rate = max(0.0, min(1.0, success_rate))
        
        kpis = {
            "success_rate_windowed": success_rate,
            "avg_geodesic_deg": state['geodesic_error'],
            "avg_point2plane_mm": state['geodesic_error'] * 0.2 + 0.1,
            "avg_chamfer_mm": state['geodesic_error'] * 0.15 + 0.08,
            "peak_force_N": state['force_buildup'] + 5.0,
            "impact_integral": state['force_buildup'] * elapsed * 0.1,
            "replan_time_s": 0.15 + 0.05 * np.random.randn(),
            "system_uptime_s": elapsed,
            "episodes_completed": episodes,
            "current_phase": state['phase']
        }
        
        msg = String()
        msg.data = json.dumps(kpis)
        self.kpi_pub.publish(msg)
        
        # Also publish sequencer state
        seq_msg = String()
        seq_msg.data = json.dumps({
            "state": state['phase'].upper(),
            "episode": episodes,
            "quality_ok": state['geodesic_error'] < 2.0,
            "force_ok": state['force_buildup'] < 15.0
        })
        self.sequencer_pub.publish(seq_msg)

def main():
    parser = argparse.ArgumentParser(description='SomaCube RL Data Simulator')
    parser.add_argument('--scenario', choices=['normal', 'degraded', 'failure'], 
                       default='normal', help='Simulation scenario')
    parser.add_argument('--register-rate', type=float, default=30.0,
                       help='Registration quality publish rate (Hz)')
    parser.add_argument('--ft-rate', type=float, default=100.0,
                       help='Force/torque publish rate (Hz)')
    parser.add_argument('--noise-level', type=float, default=0.1,
                       help='Noise level for measurements (0.0-1.0)')
    parser.add_argument('--duration', type=int, default=0,
                       help='Run duration in seconds (0=infinite)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    
    args = parser.parse_args()
    
    params = SimulationParams(
        register_rate=args.register_rate,
        ft_rate=args.ft_rate,
        noise_level=args.noise_level,
        scenario=args.scenario
    )
    
    rclpy.init()
    
    try:
        simulator = DataSimulator(params)
        
        if args.duration > 0:
            print(f"Running simulation for {args.duration} seconds...")
            start_time = time.time()
            while rclpy.ok() and (time.time() - start_time) < args.duration:
                rclpy.spin_once(simulator, timeout_sec=0.1)
        else:
            print("Running simulation indefinitely (Ctrl+C to stop)...")
            rclpy.spin(simulator)
            
    except KeyboardInterrupt:
        print("\nSimulation stopped by user")
    finally:
        if 'simulator' in locals():
            simulator.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()