#!/usr/bin/env python3
"""
System Health Monitor for SomaCube RL Pipeline
Continuously monitors system health, node status, and performance metrics
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
import psutil
import time
import json
import os
import sys
from datetime import datetime
from collections import defaultdict, deque
import argparse

# ROS messages
from std_msgs.msg import String
from geometry_msgs.msg import WrenchStamped
from doosan_somacube_rl.msg import RegisterQuality, SafetyEvent

class SystemMonitor(Node):
    def __init__(self, args):
        super().__init__('system_monitor')
        
        self.args = args
        self.start_time = time.time()
        
        # Health metrics storage
        self.metrics = {
            'node_health': {},
            'topic_health': {},
            'system_resources': {},
            'performance': defaultdict(list),
            'alerts': deque(maxlen=100),
        }
        
        # Topic monitoring
        self.topic_stats = defaultdict(lambda: {
            'last_msg_time': 0,
            'msg_count': 0,
            'expected_hz': 0,
            'actual_hz': 0,
        })
        
        # Expected topic rates (Hz)
        self.expected_rates = {
            '/pc_register/quality': 30,
            '/pose/filtered': 30, 
            '/ee/ft': 100,
            '/safety/events': 1,  # Event-driven
            '/kpi/state': 0.5,    # Every 2 seconds
            '/policy/lo/cmd': 50,
        }
        
        # QoS
        reliable_qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
            depth=1
        )
        
        sensor_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=5
        )
        
        # Subscribers
        self.setup_subscribers(reliable_qos, sensor_qos)
        
        # Publishers
        self.health_pub = self.create_publisher(
            String, '/system/health', reliable_qos)
        
        # Timers
        self.create_timer(1.0, self.update_metrics)  # 1 Hz monitoring
        self.create_timer(5.0, self.check_system_health)  # 5s health checks
        self.create_timer(10.0, self.publish_health_report)  # 10s reports
        
        # Output file
        if args.output:
            self.output_file = open(args.output, 'w')
            self.output_file.write("timestamp,metric,value,status\n")
        else:
            self.output_file = None
        
        self.get_logger().info(f'System monitor started, output: {args.output or "console"}')

    def setup_subscribers(self, reliable_qos, sensor_qos):
        """Set up topic subscribers for monitoring"""
        
        # Quality metrics
        self.create_subscription(
            RegisterQuality, '/pc_register/quality',
            lambda msg: self.topic_callback('/pc_register/quality', msg),
            sensor_qos
        )
        
        # Forces
        self.create_subscription(
            WrenchStamped, '/ee/ft',
            lambda msg: self.topic_callback('/ee/ft', msg),
            sensor_qos
        )
        
        # Safety events
        self.create_subscription(
            SafetyEvent, '/safety/events',
            lambda msg: self.safety_event_callback(msg),
            reliable_qos
        )
        
        # KPI data
        self.create_subscription(
            String, '/kpi/state',
            lambda msg: self.kpi_callback(msg),
            reliable_qos
        )

    def topic_callback(self, topic_name, msg):
        """Generic topic callback for rate monitoring"""
        now = time.time()
        stats = self.topic_stats[topic_name]
        
        # Update message count and timing
        stats['msg_count'] += 1
        if stats['last_msg_time'] > 0:
            interval = now - stats['last_msg_time']
            if interval > 0:
                stats['actual_hz'] = 1.0 / interval
        
        stats['last_msg_time'] = now
        stats['expected_hz'] = self.expected_rates.get(topic_name, 0)
        
        # Store specific metric values
        if topic_name == '/pc_register/quality':
            self.metrics['performance']['geodesic_deg'].append(msg.geodesic_deg)
            self.metrics['performance']['inlier_ratio'].append(msg.inlier_ratio)
            self.metrics['performance']['point2plane_m'].append(msg.mean_point2plane_m)
        elif topic_name == '/ee/ft':
            force_mag = (msg.wrench.force.x**2 + msg.wrench.force.y**2 + msg.wrench.force.z**2)**0.5
            self.metrics['performance']['force_magnitude'].append(force_mag)

    def safety_event_callback(self, msg):
        """Handle safety events"""
        now = time.time()
        self.topic_callback('/safety/events', msg)
        
        # Log safety events
        alert = {
            'timestamp': now,
            'type': msg.type,
            'detail': msg.detail,
            'severity': msg.severity
        }
        self.metrics['alerts'].append(alert)
        
        # High severity events
        if msg.severity >= 3:  # Error level
            self.get_logger().error(f'Safety event: {msg.type} - {msg.detail}')

    def kpi_callback(self, msg):
        """Handle KPI updates"""
        self.topic_callback('/kpi/state', msg)
        
        try:
            kpi_data = json.loads(msg.data)
            for key, value in kpi_data.items():
                if isinstance(value, (int, float)):
                    self.metrics['performance'][f'kpi_{key}'].append(value)
        except json.JSONDecodeError:
            pass

    def update_metrics(self):
        """Update system metrics every second"""
        now = time.time()
        
        # System resources
        self.metrics['system_resources'] = {
            'cpu_percent': psutil.cpu_percent(interval=0.1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent,
            'network_io': psutil.net_io_counters(),
            'uptime': now - self.start_time,
        }
        
        # Node health (check if ROS nodes are running)
        try:
            node_list = self.get_node_names()
            expected_nodes = [
                'pc_preprocess', 'pc_register', 'pose_tracker',
                'safety_monitor', 'imp_ctrl', 'sequencer',
                'layer1_manager', 'logger', 'policy_sac_low'
            ]
            
            self.metrics['node_health'] = {
                'total_nodes': len(node_list),
                'expected_nodes': len(expected_nodes),
                'missing_nodes': [n for n in expected_nodes if n not in node_list],
                'running_nodes': [n for n in expected_nodes if n in node_list]
            }
        except Exception as e:
            self.get_logger().warn(f'Could not get node list: {e}')

    def check_system_health(self):
        """Perform comprehensive health checks"""
        health_score = 100
        issues = []
        
        # Check system resources
        resources = self.metrics['system_resources']
        if resources.get('cpu_percent', 0) > 80:
            health_score -= 20
            issues.append('High CPU usage')
        
        if resources.get('memory_percent', 0) > 85:
            health_score -= 15
            issues.append('High memory usage')
        
        if resources.get('disk_percent', 0) > 90:
            health_score -= 10
            issues.append('Low disk space')
        
        # Check topic health
        now = time.time()
        for topic, stats in self.topic_stats.items():
            expected_hz = stats['expected_hz']
            if expected_hz > 0:  # Only check topics with expected rates
                time_since_last = now - stats['last_msg_time']
                timeout = 2.0 / expected_hz  # Allow 2x expected interval
                
                if time_since_last > timeout:
                    health_score -= 10
                    issues.append(f'Topic {topic} timeout ({time_since_last:.1f}s)')
                
                # Check rate
                actual_hz = stats.get('actual_hz', 0)
                if actual_hz < expected_hz * 0.5:  # Less than 50% expected rate
                    health_score -= 5
                    issues.append(f'Topic {topic} low rate ({actual_hz:.1f}/{expected_hz}Hz)')
        
        # Check for recent safety events
        recent_alerts = [a for a in self.metrics['alerts'] 
                        if now - a['timestamp'] < 30 and a['severity'] >= 3]
        if recent_alerts:
            health_score -= len(recent_alerts) * 5
            issues.append(f'{len(recent_alerts)} recent safety events')
        
        # Check node health
        node_health = self.metrics['node_health']
        missing_nodes = node_health.get('missing_nodes', [])
        if missing_nodes:
            health_score -= len(missing_nodes) * 10
            issues.append(f'Missing nodes: {missing_nodes}')
        
        # Store health assessment
        self.metrics['system_health'] = {
            'score': max(0, health_score),
            'status': self.get_health_status(health_score),
            'issues': issues,
            'timestamp': now
        }
        
        # Log if unhealthy
        if health_score < 80:
            self.get_logger().warn(f'System health: {health_score}/100 - Issues: {", ".join(issues)}')

    def get_health_status(self, score):
        """Convert health score to status string"""
        if score >= 90:
            return 'EXCELLENT'
        elif score >= 80:
            return 'GOOD'
        elif score >= 60:
            return 'FAIR'
        elif score >= 40:
            return 'POOR'
        else:
            return 'CRITICAL'

    def publish_health_report(self):
        """Publish periodic health reports"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'system_health': self.metrics['system_health'],
            'system_resources': self.metrics['system_resources'],
            'topic_stats': dict(self.topic_stats),
            'node_health': self.metrics['node_health'],
            'recent_alerts': list(self.metrics['alerts'])[-5:],  # Last 5 alerts
            'performance_summary': self.get_performance_summary(),
        }
        
        # Publish to ROS topic
        health_msg = String()
        health_msg.data = json.dumps(report, default=str)
        self.health_pub.publish(health_msg)
        
        # Console output
        if self.args.verbose:
            self.print_health_report(report)
        
        # File output
        if self.output_file:
            timestamp = report['timestamp']
            health = report['system_health']
            self.output_file.write(f"{timestamp},health_score,{health['score']},{health['status']}\n")
            
            resources = report['system_resources']
            self.output_file.write(f"{timestamp},cpu_percent,{resources['cpu_percent']},OK\n")
            self.output_file.write(f"{timestamp},memory_percent,{resources['memory_percent']},OK\n")
            self.output_file.flush()

    def get_performance_summary(self):
        """Calculate performance metrics summary"""
        summary = {}
        
        for metric, values in self.metrics['performance'].items():
            if values:
                recent_values = values[-30:]  # Last 30 values
                summary[metric] = {
                    'count': len(recent_values),
                    'mean': sum(recent_values) / len(recent_values),
                    'min': min(recent_values),
                    'max': max(recent_values),
                    'latest': recent_values[-1] if recent_values else None
                }
        
        return summary

    def print_health_report(self, report):
        """Print formatted health report to console"""
        print("\n" + "="*60)
        print(f"SomaCube RL System Health Report - {report['timestamp']}")
        print("="*60)
        
        # System health
        health = report['system_health']
        print(f"Overall Health: {health['score']}/100 ({health['status']})")
        if health['issues']:
            print(f"Issues: {', '.join(health['issues'])}")
        
        # System resources
        resources = report['system_resources']
        print(f"CPU: {resources['cpu_percent']:.1f}% | "
              f"Memory: {resources['memory_percent']:.1f}% | "
              f"Disk: {resources['disk_percent']:.1f}%")
        
        # Node status
        node_health = report['node_health']
        print(f"Nodes: {len(node_health.get('running_nodes', []))}/{node_health.get('expected_nodes', 0)} running")
        if node_health.get('missing_nodes'):
            print(f"Missing: {', '.join(node_health['missing_nodes'])}")
        
        # Topic rates
        print("\nTopic Health:")
        for topic, stats in report['topic_stats'].items():
            expected_hz = stats.get('expected_hz', 0)
            actual_hz = stats.get('actual_hz', 0)
            if expected_hz > 0:
                rate_health = "✓" if actual_hz >= expected_hz * 0.8 else "⚠" if actual_hz >= expected_hz * 0.5 else "✗"
                print(f"  {rate_health} {topic}: {actual_hz:.1f}/{expected_hz}Hz")
        
        # Performance summary
        perf = report.get('performance_summary', {})
        if perf:
            print("\nPerformance Metrics:")
            for metric, stats in perf.items():
                if stats['count'] > 0:
                    print(f"  {metric}: {stats['latest']:.3f} (avg: {stats['mean']:.3f})")
        
        print("="*60)

    def destroy_node(self):
        if self.output_file:
            self.output_file.close()
        super().destroy_node()

def main():
    parser = argparse.ArgumentParser(description='SomaCube RL System Monitor')
    parser.add_argument('--output', '-o', help='Output CSV file for metrics')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose console output')
    parser.add_argument('--duration', '-d', type=int, help='Run for specified seconds (0=infinite)', default=0)
    
    args = parser.parse_args()
    
    rclpy.init()
    
    try:
        monitor = SystemMonitor(args)
        
        if args.duration > 0:
            print(f"Running system monitor for {args.duration} seconds...")
            start_time = time.time()
            while rclpy.ok() and (time.time() - start_time) < args.duration:
                rclpy.spin_once(monitor, timeout_sec=0.1)
        else:
            print("Running system monitor indefinitely (Ctrl+C to stop)...")
            rclpy.spin(monitor)
            
    except KeyboardInterrupt:
        print("\nSystem monitor stopped by user")
    finally:
        if 'monitor' in locals():
            monitor.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()