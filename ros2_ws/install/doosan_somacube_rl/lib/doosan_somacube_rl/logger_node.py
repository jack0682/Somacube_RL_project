#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped, WrenchStamped
from doosan_somacube_rl.msg import PolicyCmd, RegisterQuality, SafetyEvent
from std_msgs.msg import String, Float32
import numpy as np
import pandas as pd
import csv
import json
import time
import os
from pathlib import Path
from collections import deque
from datetime import datetime


class LoggerNode(Node):
    def __init__(self):
        super().__init__('logger')
        
        # Parameters
        self.declare_parameters_from_yaml()
        
        # Create log directory
        self.log_dir = Path.home() / 'somacube_logs'
        self.log_dir.mkdir(exist_ok=True)
        
        # Initialize log files
        self.init_log_files()
        
        # Data buffers
        self.kpi_buffer = deque(maxlen=1000)
        self.sensor_buffer = deque(maxlen=500)
        self.event_buffer = deque(maxlen=200)
        
        # State variables
        self.session_start_time = time.time()
        self.last_kpi_report_time = time.time()
        self.sequence_count = 0
        self.total_success_count = 0
        
        # Subscribers for data collection
        self.setup_subscribers()
        
        # Publishers for real-time metrics
        self.setup_publishers()
        
        # Timers
        kpi_rate_hz = 1.0 / self.get_parameter('logger.kpi.report_interval_s').value
        self.kpi_timer = self.create_timer(1.0 / kpi_rate_hz, self.kpi_report_callback)
        
        # Data logging timer (higher frequency)
        data_log_rate_hz = 10.0  # 10Hz data logging
        self.data_log_timer = self.create_timer(1.0 / data_log_rate_hz, self.data_log_callback)
        
        self.get_logger().info(f'Logger node initialized, logs in: {self.log_dir}')

    def declare_parameters_from_yaml(self):
        """Declare parameters from YAML config"""
        defaults = {
            'logger.kpi.report_interval_s': 2.0,
            'logger.kpi.metrics': [
                'success_rate_windowed',
                'avg_geodesic_deg',
                'avg_point2plane_mm',
                'avg_chamfer_mm',
                'peak_force_N',
                'impact_integral',
                'replan_time_s'
            ],
            'logger.rosbag.enable': True,
            'logger.rosbag.topics': [
                '/pc_register/pose',
                '/pc_register/quality',
                '/policy/lo/cmd',
                '/ee/ft',
                '/safety/events'
            ],
            'logger.tensors.enable': True,
            'logger.tensors.fields': [
                'obs',
                'act',
                'rew',
                'done',
                'quality.mean_point2plane_m',
                'quality.chamfer_bidir_m',
                'quality.inlier_ratio',
                'quality.icp_residual_std',
                'quality.geodesic_deg'
            ]
        }
        
        for name, default_value in defaults.items():
            self.declare_parameter(name, default_value)

    def init_log_files(self):
        """Initialize CSV log files"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # KPI log file
        self.kpi_log_file = self.log_dir / f'kpi_{timestamp}.csv'
        self.kpi_fieldnames = [
            'timestamp', 'session_time_s', 'sequence_count', 'success_rate_windowed',
            'avg_geodesic_deg', 'avg_point2plane_mm', 'avg_chamfer_mm',
            'peak_force_N', 'impact_integral', 'replan_time_s', 'total_violations'
        ]
        
        with open(self.kpi_log_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=self.kpi_fieldnames)
            writer.writeheader()
        
        # Sensor data log file
        self.sensor_log_file = self.log_dir / f'sensors_{timestamp}.csv'
        self.sensor_fieldnames = [
            'timestamp', 'session_time_s', 'pose_x', 'pose_y', 'pose_z',
            'pose_qx', 'pose_qy', 'pose_qz', 'pose_qw',
            'force_x', 'force_y', 'force_z', 'torque_x', 'torque_y', 'torque_z',
            'geodesic_deg', 'point2plane_m', 'inlier_ratio', 'icp_std'
        ]
        
        with open(self.sensor_log_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=self.sensor_fieldnames)
            writer.writeheader()
        
        # Event log file
        self.event_log_file = self.log_dir / f'events_{timestamp}.csv'
        self.event_fieldnames = [
            'timestamp', 'session_time_s', 'event_type', 'event_detail', 
            'severity', 'source_node', 'sequence_id', 'piece_id'
        ]
        
        with open(self.event_log_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=self.event_fieldnames)
            writer.writeheader()
        
        # Policy/RL data log file (if tensor logging enabled)
        if self.get_parameter('logger.tensors.enable').value:
            self.policy_log_file = self.log_dir / f'policy_{timestamp}.csv'
            self.policy_fieldnames = [
                'timestamp', 'session_time_s', 'obs_dim', 'act_dim',
                'reward', 'done', 'confidence_score', 
                'policy_dx', 'policy_dy', 'policy_dz',
                'policy_droll', 'policy_dpitch', 'policy_dyaw',
                'policy_dKp', 'policy_dKd'
            ]
            
            with open(self.policy_log_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=self.policy_fieldnames)
                writer.writeheader()

    def setup_subscribers(self):
        """Set up subscribers for data collection"""
        # Pose data
        self.pose_sub = self.create_subscription(
            PoseStamped,
            '/pose_tracker/smoothed_pose',
            self.pose_callback,
            10
        )
        
        # Force/torque data
        self.wrench_sub = self.create_subscription(
            WrenchStamped,
            '/ee/ft',
            self.wrench_callback,
            10
        )
        
        # Registration quality
        self.quality_sub = self.create_subscription(
            RegisterQuality,
            '/pc_register/quality',
            self.quality_callback,
            10
        )
        
        # Policy commands
        self.policy_cmd_sub = self.create_subscription(
            PolicyCmd,
            '/policy/lo/cmd',
            self.policy_callback,
            10
        )
        
        # Safety events
        self.safety_event_sub = self.create_subscription(
            SafetyEvent,
            '/safety/events',
            self.safety_event_callback,
            10
        )
        
        # Sequencer state for episode tracking
        self.sequencer_state_sub = self.create_subscription(
            String,
            '/sequencer/state',
            self.sequencer_state_callback,
            10
        )
        
        # Assembly metrics
        self.assembly_metrics_sub = self.create_subscription(
            String,
            '/layer1_manager/metrics',
            self.assembly_metrics_callback,
            10
        )
        
        # Sequence completion
        self.stage_complete_sub = self.create_subscription(
            String,
            '/sequencer/stage_complete',
            self.stage_complete_callback,
            10
        )

    def setup_publishers(self):
        """Set up publishers for real-time metrics"""
        self.kpi_metrics_pub = self.create_publisher(
            String,  # JSON metrics
            '/logger/kpi_metrics',
            10
        )
        
        self.success_rate_pub = self.create_publisher(
            Float32,
            '/logger/success_rate',
            10
        )
        
        self.system_health_pub = self.create_publisher(
            String,
            '/logger/system_health',
            10
        )

    def pose_callback(self, msg):
        """Handle pose data"""
        self.latest_pose = msg

    def wrench_callback(self, msg):
        """Handle force/torque data"""
        self.latest_wrench = msg

    def quality_callback(self, msg):
        """Handle registration quality data"""
        self.latest_quality = msg

    def policy_callback(self, msg):
        """Handle policy command data"""
        self.latest_policy_cmd = msg

    def safety_event_callback(self, msg):
        """Handle safety events"""
        current_time = time.time()
        session_time = current_time - self.session_start_time
        
        event_data = {
            'timestamp': current_time,
            'session_time_s': session_time,
            'event_type': msg.type,
            'event_detail': msg.detail,
            'severity': msg.severity,
            'source_node': 'safety_monitor',
            'sequence_id': self.sequence_count,
            'piece_id': getattr(self, 'current_piece_id', None)
        }
        
        self.event_buffer.append(event_data)

    def sequencer_state_callback(self, msg):
        """Handle sequencer state changes"""
        if msg.data == 'idle' and hasattr(self, 'in_sequence') and self.in_sequence:
            # Sequence ended
            self.in_sequence = False
        elif msg.data == 'approach' and not hasattr(self, 'in_sequence'):
            # New sequence started
            self.sequence_count += 1
            self.in_sequence = True

    def assembly_metrics_callback(self, msg):
        """Handle assembly metrics"""
        try:
            metrics_data = json.loads(msg.data)
            self.latest_assembly_metrics = metrics_data
        except json.JSONDecodeError:
            pass

    def stage_complete_callback(self, msg):
        """Handle stage completion"""
        if msg.data == "SEQUENCE_COMPLETE":
            self.total_success_count += 1

    def data_log_callback(self):
        """Log high-frequency sensor data"""
        current_time = time.time()
        session_time = current_time - self.session_start_time
        
        # Collect current sensor data
        sensor_data = {
            'timestamp': current_time,
            'session_time_s': session_time
        }
        
        # Add pose data if available
        if hasattr(self, 'latest_pose'):
            pose = self.latest_pose.pose
            sensor_data.update({
                'pose_x': pose.position.x,
                'pose_y': pose.position.y,
                'pose_z': pose.position.z,
                'pose_qx': pose.orientation.x,
                'pose_qy': pose.orientation.y,
                'pose_qz': pose.orientation.z,
                'pose_qw': pose.orientation.w
            })
        else:
            sensor_data.update({
                'pose_x': 0, 'pose_y': 0, 'pose_z': 0,
                'pose_qx': 0, 'pose_qy': 0, 'pose_qz': 0, 'pose_qw': 1
            })
        
        # Add force/torque data if available
        if hasattr(self, 'latest_wrench'):
            wrench = self.latest_wrench.wrench
            sensor_data.update({
                'force_x': wrench.force.x,
                'force_y': wrench.force.y,
                'force_z': wrench.force.z,
                'torque_x': wrench.torque.x,
                'torque_y': wrench.torque.y,
                'torque_z': wrench.torque.z
            })
        else:
            sensor_data.update({
                'force_x': 0, 'force_y': 0, 'force_z': 0,
                'torque_x': 0, 'torque_y': 0, 'torque_z': 0
            })
        
        # Add quality data if available
        if hasattr(self, 'latest_quality'):
            quality = self.latest_quality
            sensor_data.update({
                'geodesic_deg': quality.geodesic_deg,
                'point2plane_m': quality.mean_point2plane_m,
                'inlier_ratio': quality.inlier_ratio,
                'icp_std': quality.icp_residual_std
            })
        else:
            sensor_data.update({
                'geodesic_deg': 0, 'point2plane_m': 0,
                'inlier_ratio': 0, 'icp_std': 0
            })
        
        # Store in buffer
        self.sensor_buffer.append(sensor_data)
        
        # Log policy data if available
        if self.get_parameter('logger.tensors.enable').value and hasattr(self, 'latest_policy_cmd'):
            self.log_policy_data(current_time, session_time)

    def log_policy_data(self, current_time, session_time):
        """Log policy/RL data"""
        policy_cmd = self.latest_policy_cmd
        
        policy_data = {
            'timestamp': current_time,
            'session_time_s': session_time,
            'obs_dim': 12,  # Placeholder - would track actual observation dimension
            'act_dim': 8,   # Placeholder - would track actual action dimension
            'reward': 0.0,  # Placeholder - would need reward signal
            'done': False,  # Placeholder - would need episode termination signal
            'confidence_score': getattr(self, 'latest_confidence', 0.0),
            'policy_dx': policy_cmd.dx,
            'policy_dy': policy_cmd.dy,
            'policy_dz': policy_cmd.dz,
            'policy_droll': policy_cmd.droll,
            'policy_dpitch': policy_cmd.dpitch,
            'policy_dyaw': policy_cmd.dyaw,
            'policy_dKp': policy_cmd.dKp,
            'policy_dKd': policy_cmd.dKd
        }
        
        # Write to policy log file
        try:
            with open(self.policy_log_file, 'a', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=self.policy_fieldnames)
                writer.writerow(policy_data)
        except Exception as e:
            self.get_logger().warn(f'Failed to write policy data: {e}')

    def kpi_report_callback(self):
        """Generate and publish KPI report"""
        current_time = time.time()
        session_time = current_time - self.session_start_time
        
        try:
            # Calculate KPIs
            kpis = self.calculate_kpis()
            
            # Add metadata
            kpis.update({
                'timestamp': current_time,
                'session_time_s': session_time,
                'sequence_count': self.sequence_count
            })
            
            # Store in buffer
            self.kpi_buffer.append(kpis)
            
            # Write to KPI log file
            with open(self.kpi_log_file, 'a', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=self.kpi_fieldnames)
                # Fill missing fields with 0
                row_data = {field: kpis.get(field, 0) for field in self.kpi_fieldnames}
                writer.writerow(row_data)
            
            # Publish real-time metrics
            self.publish_kpi_metrics(kpis)
            
            # Write sensor data batch
            self.flush_sensor_data()
            
            # Write event data batch
            self.flush_event_data()
            
        except Exception as e:
            self.get_logger().error(f'KPI report error: {e}')

    def calculate_kpis(self):
        """Calculate Key Performance Indicators"""
        kpis = {}
        
        # Success rate (windowed over recent sequences)
        window_size = 20
        recent_sequences = min(window_size, self.sequence_count)
        if recent_sequences > 0:
            kpis['success_rate_windowed'] = self.total_success_count / recent_sequences
        else:
            kpis['success_rate_windowed'] = 0.0
        
        # Average quality metrics from recent sensor data
        if self.sensor_buffer:
            recent_data = list(self.sensor_buffer)[-50:]  # Last 50 samples
            
            # Geodesic angle average
            geodesic_values = [d.get('geodesic_deg', 0) for d in recent_data]
            kpis['avg_geodesic_deg'] = np.mean(geodesic_values) if geodesic_values else 0
            
            # Point-to-plane distance average (convert to mm)
            point2plane_values = [d.get('point2plane_m', 0) * 1000 for d in recent_data]
            kpis['avg_point2plane_mm'] = np.mean(point2plane_values) if point2plane_values else 0
            
            # Chamfer distance (use point2plane as proxy)
            kpis['avg_chamfer_mm'] = kpis['avg_point2plane_mm']
            
            # Peak force
            force_magnitudes = []
            for d in recent_data:
                fx, fy, fz = d.get('force_x', 0), d.get('force_y', 0), d.get('force_z', 0)
                force_mag = np.sqrt(fx**2 + fy**2 + fz**2)
                force_magnitudes.append(force_mag)
            
            kpis['peak_force_N'] = max(force_magnitudes) if force_magnitudes else 0
            
            # Impact integral (simplified as sum of force changes)
            if len(force_magnitudes) > 1:
                force_changes = np.abs(np.diff(force_magnitudes))
                kpis['impact_integral'] = np.sum(force_changes)
            else:
                kpis['impact_integral'] = 0
        else:
            kpis.update({
                'avg_geodesic_deg': 0,
                'avg_point2plane_mm': 0,
                'avg_chamfer_mm': 0,
                'peak_force_N': 0,
                'impact_integral': 0
            })
        
        # Replan time (placeholder - would need actual timing data)
        kpis['replan_time_s'] = 0.5  # Placeholder value
        
        # Safety violations count
        recent_violations = [e for e in self.event_buffer if e['severity'] >= 2]
        kpis['total_violations'] = len(recent_violations)
        
        return kpis

    def publish_kpi_metrics(self, kpis):
        """Publish KPI metrics to topics"""
        # JSON metrics
        kpi_msg = String()
        kpi_msg.data = json.dumps(kpis, default=str)
        self.kpi_metrics_pub.publish(kpi_msg)
        
        # Success rate
        success_msg = Float32()
        success_msg.data = float(kpis.get('success_rate_windowed', 0))
        self.success_rate_pub.publish(success_msg)
        
        # System health
        health_status = self.assess_system_health(kpis)
        health_msg = String()
        health_msg.data = health_status
        self.system_health_pub.publish(health_msg)

    def assess_system_health(self, kpis):
        """Assess overall system health"""
        issues = []
        
        # Check success rate
        if kpis.get('success_rate_windowed', 0) < 0.5:
            issues.append('LOW_SUCCESS_RATE')
        
        # Check force levels
        if kpis.get('peak_force_N', 0) > 20:
            issues.append('HIGH_FORCES')
        
        # Check registration quality
        if kpis.get('avg_geodesic_deg', 0) > 5:
            issues.append('POOR_ALIGNMENT')
        
        # Check safety violations
        if kpis.get('total_violations', 0) > 5:
            issues.append('FREQUENT_VIOLATIONS')
        
        if not issues:
            return 'HEALTHY'
        elif len(issues) == 1:
            return f'CAUTION_{issues[0]}'
        else:
            return f'WARNING_{len(issues)}_ISSUES'

    def flush_sensor_data(self):
        """Write buffered sensor data to file"""
        if not self.sensor_buffer:
            return
        
        try:
            with open(self.sensor_log_file, 'a', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=self.sensor_fieldnames)
                
                for data in self.sensor_buffer:
                    # Fill missing fields with 0
                    row_data = {field: data.get(field, 0) for field in self.sensor_fieldnames}
                    writer.writerow(row_data)
            
            # Clear buffer after writing
            self.sensor_buffer.clear()
            
        except Exception as e:
            self.get_logger().warn(f'Failed to flush sensor data: {e}')

    def flush_event_data(self):
        """Write buffered event data to file"""
        if not self.event_buffer:
            return
        
        try:
            with open(self.event_log_file, 'a', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=self.event_fieldnames)
                
                for data in self.event_buffer:
                    # Fill missing fields with empty string or 0
                    row_data = {}
                    for field in self.event_fieldnames:
                        if field in ['severity', 'sequence_id', 'piece_id']:
                            row_data[field] = data.get(field, 0)
                        else:
                            row_data[field] = data.get(field, '')
                    writer.writerow(row_data)
            
            # Clear buffer after writing
            self.event_buffer.clear()
            
        except Exception as e:
            self.get_logger().warn(f'Failed to flush event data: {e}')

    def get_session_summary(self):
        """Get session summary statistics"""
        session_time = time.time() - self.session_start_time
        
        summary = {
            'session_duration_s': session_time,
            'total_sequences': self.sequence_count,
            'successful_sequences': self.total_success_count,
            'overall_success_rate': self.total_success_count / max(self.sequence_count, 1),
            'data_points_logged': len(self.sensor_buffer) + sum(len(self.kpi_buffer) for _ in range(len(self.kpi_buffer))),
            'safety_events': len(self.event_buffer),
            'log_files': {
                'kpi': str(self.kpi_log_file),
                'sensors': str(self.sensor_log_file),
                'events': str(self.event_log_file)
            }
        }
        
        if hasattr(self, 'policy_log_file'):
            summary['log_files']['policy'] = str(self.policy_log_file)
        
        return summary


def main(args=None):
    rclpy.init(args=args)
    node = LoggerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        # Print session summary on exit
        summary = node.get_session_summary()
        node.get_logger().info(f'Session summary: {json.dumps(summary, indent=2)}')
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()