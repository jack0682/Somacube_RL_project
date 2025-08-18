#!/usr/bin/env python3

"""
Topic Validation Script for SomaCube RL System

Verifies that all essential topics are being published with correct message types
and reasonable data ranges. Used for system health monitoring and debugging.
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from sensor_msgs.msg import PointCloud2, Image, CameraInfo
from geometry_msgs.msg import PoseStamped, WrenchStamped, TwistStamped
from doosan_somacube_rl.msg import PolicyCmd, RegisterQuality, SafetyEvent
from std_msgs.msg import String, Bool, Float32, Int32
import numpy as np
import time
import json
import argparse
from datetime import datetime
from collections import defaultdict


class TopicVerifier(Node):
    def __init__(self):
        super().__init__('topic_verifier')
        
        # Test configuration
        self.verification_duration = 30.0  # seconds
        self.start_time = time.time()
        
        # Topic monitoring
        self.topic_stats = defaultdict(lambda: {
            'message_count': 0,
            'first_received': None,
            'last_received': None,
            'message_type': None,
            'data_samples': [],
            'errors': []
        })
        
        # Expected topics and their types
        self.expected_topics = {
            # Vision system
            '/camera/color/image_raw': Image,
            '/camera/aligned_depth_to_color/image_raw': Image,
            '/camera/color/camera_info': CameraInfo,
            
            # Point cloud processing
            '/pc_preprocess/output': PointCloud2,
            '/debug/heightmap': Image,
            
            # Registration
            '/pc_register/pose': PoseStamped,
            '/pc_register/quality': RegisterQuality,
            
            # Pose tracking
            '/pose_tracker/smoothed_pose': PoseStamped,
            
            # Control
            '/layer1_manager/target_pose': PoseStamped,
            '/policy/lo/cmd': PolicyCmd,
            '/doosan/cmd_vel': TwistStamped,
            '/imp_ctrl/enable': Bool,
            '/imp_ctrl/confidence': Float32,
            
            # Safety
            '/ee/ft': WrenchStamped,
            '/safety/events': SafetyEvent,
            '/safety/status': String,
            '/safety/emergency_stop': Bool,
            
            # Sequencing
            '/sequencer/state': String,
            '/sequencer/stage_complete': String,
            
            # Assembly management
            '/layer1_manager/current_piece': Int32,
            '/layer1_manager/assembly_status': String,
            '/layer1_manager/target_pose': PoseStamped,
            
            # Logging
            '/logger/kpi_metrics': String,
            '/logger/success_rate': Float32,
            '/logger/system_health': String,
            
            # Policy
            '/policy/reward': Float32,
            '/policy/confidence': Float32
        }
        
        # Setup subscribers
        self.setup_subscribers()
        
        # Verification timer
        self.verification_timer = self.create_timer(1.0, self.check_progress)
        
        # Results
        self.verification_complete = False
        self.results = {}
        
        self.get_logger().info(f'Topic verification started for {len(self.expected_topics)} topics')
        self.get_logger().info(f'Verification duration: {self.verification_duration}s')

    def setup_subscribers(self):
        """Setup subscribers for all expected topics"""
        # Flexible QoS for different topic types
        sensor_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=1
        )
        
        reliable_qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
            depth=1
        )
        
        for topic_name, msg_type in self.expected_topics.items():
            try:
                # Use sensor QoS for sensor topics, reliable for others
                qos = sensor_qos if any(sensor in topic_name for sensor in 
                                      ['/camera', '/ee/ft', '/pc_']) else reliable_qos
                
                # Create callback function for this topic
                callback = self.create_topic_callback(topic_name, msg_type)
                
                # Create subscription
                self.create_subscription(
                    msg_type,
                    topic_name,
                    callback,
                    qos
                )
                
                self.get_logger().debug(f'Subscribed to {topic_name}')
                
            except Exception as e:
                self.topic_stats[topic_name]['errors'].append(f'Subscription failed: {e}')
                self.get_logger().warn(f'Failed to subscribe to {topic_name}: {e}')

    def create_topic_callback(self, topic_name, msg_type):
        """Create a callback function for a specific topic"""
        def callback(msg):
            current_time = time.time()
            stats = self.topic_stats[topic_name]
            
            # Update basic stats
            stats['message_count'] += 1
            if stats['first_received'] is None:
                stats['first_received'] = current_time
            stats['last_received'] = current_time
            stats['message_type'] = type(msg).__name__
            
            # Validate message content
            try:
                validation_result = self.validate_message(topic_name, msg)
                if validation_result:
                    stats['data_samples'].append(validation_result)
            except Exception as e:
                stats['errors'].append(f'Validation error: {e}')
        
        return callback

    def validate_message(self, topic_name, msg):
        """Validate message content and extract key metrics"""
        validation = {'timestamp': time.time()}
        
        try:
            if isinstance(msg, PoseStamped):
                # Validate pose data
                pos = msg.pose.position
                ori = msg.pose.orientation
                
                validation['position_norm'] = np.sqrt(pos.x**2 + pos.y**2 + pos.z**2)
                validation['orientation_norm'] = np.sqrt(ori.x**2 + ori.y**2 + ori.z**2 + ori.w**2)
                validation['has_header'] = hasattr(msg, 'header')
                validation['frame_id'] = msg.header.frame_id if hasattr(msg, 'header') else ''
                
                # Check for reasonable values
                if validation['position_norm'] > 10.0:  # 10m seems excessive
                    self.topic_stats[topic_name]['errors'].append('Position norm too large')
                
                if abs(validation['orientation_norm'] - 1.0) > 0.1:  # Quaternion should be unit
                    self.topic_stats[topic_name]['errors'].append('Quaternion not normalized')
            
            elif isinstance(msg, WrenchStamped):
                # Validate force/torque data
                force = msg.wrench.force
                torque = msg.wrench.torque
                
                force_norm = np.sqrt(force.x**2 + force.y**2 + force.z**2)
                torque_norm = np.sqrt(torque.x**2 + torque.y**2 + torque.z**2)
                
                validation['force_magnitude'] = force_norm
                validation['torque_magnitude'] = torque_norm
                
                # Check for reasonable force values
                if force_norm > 100.0:  # 100N seems high for assembly
                    self.topic_stats[topic_name]['errors'].append(f'High force: {force_norm:.1f}N')
            
            elif isinstance(msg, RegisterQuality):
                # Validate registration quality metrics
                validation['geodesic_deg'] = msg.geodesic_deg
                validation['point2plane_m'] = msg.mean_point2plane_m
                validation['inlier_ratio'] = msg.inlier_ratio
                validation['icp_std'] = msg.icp_residual_std
                
                # Check ranges
                if not (0 <= msg.inlier_ratio <= 1):
                    self.topic_stats[topic_name]['errors'].append('Inlier ratio out of range')
                
                if msg.geodesic_deg > 180:
                    self.topic_stats[topic_name]['errors'].append('Geodesic angle > 180 degrees')
            
            elif isinstance(msg, PolicyCmd):
                # Validate policy commands
                deltas = [msg.dx, msg.dy, msg.dz, msg.droll, msg.dpitch, msg.dyaw]
                validation['max_delta'] = max(abs(d) for d in deltas)
                validation['gain_deltas'] = [msg.dKp, msg.dKd]
                
                # Check for reasonable command magnitudes
                if validation['max_delta'] > 0.1:  # 10cm or 0.1 rad seems large
                    self.topic_stats[topic_name]['errors'].append('Large policy delta')
            
            elif isinstance(msg, SafetyEvent):
                # Validate safety events
                validation['event_type'] = msg.type
                validation['severity'] = msg.severity
                validation['detail_length'] = len(msg.detail)
                
                if msg.severity > 3:
                    self.topic_stats[topic_name]['errors'].append('Invalid severity level')
            
            elif isinstance(msg, Image):
                # Validate image data
                validation['encoding'] = msg.encoding
                validation['width'] = msg.width
                validation['height'] = msg.height
                validation['data_size'] = len(msg.data)
                
                if msg.width == 0 or msg.height == 0:
                    self.topic_stats[topic_name]['errors'].append('Zero image dimensions')
                
                if len(msg.data) == 0:
                    self.topic_stats[topic_name]['errors'].append('Empty image data')
            
            elif isinstance(msg, PointCloud2):
                # Validate point cloud data
                validation['width'] = msg.width
                validation['height'] = msg.height
                validation['point_step'] = msg.point_step
                validation['data_size'] = len(msg.data)
                validation['is_dense'] = msg.is_dense
                
                expected_data_size = msg.width * msg.height * msg.point_step
                if len(msg.data) != expected_data_size:
                    self.topic_stats[topic_name]['errors'].append('Point cloud data size mismatch')
            
            elif isinstance(msg, String):
                # Validate string messages
                validation['content'] = msg.data
                validation['length'] = len(msg.data)
                
                # Try to parse JSON if it looks like JSON
                if msg.data.strip().startswith('{'):
                    try:
                        json.loads(msg.data)
                        validation['valid_json'] = True
                    except:
                        validation['valid_json'] = False
            
            elif isinstance(msg, (Float32, Bool, Int32)):
                # Simple scalar validation
                validation['value'] = getattr(msg, 'data', str(msg))
            
            return validation
            
        except Exception as e:
            self.topic_stats[topic_name]['errors'].append(f'Message validation failed: {e}')
            return {'validation_error': str(e)}

    def check_progress(self):
        """Check verification progress and status"""
        elapsed_time = time.time() - self.start_time
        
        if elapsed_time >= self.verification_duration:
            if not self.verification_complete:
                self.complete_verification()
        else:
            # Progress update
            progress = elapsed_time / self.verification_duration * 100
            active_topics = sum(1 for stats in self.topic_stats.values() if stats['message_count'] > 0)
            
            self.get_logger().info(
                f'Verification progress: {progress:.1f}% - {active_topics}/{len(self.expected_topics)} topics active'
            )

    def complete_verification(self):
        """Complete verification and generate report"""
        self.verification_complete = True
        self.verification_timer.cancel()
        
        # Generate results
        self.results = self.analyze_results()
        
        # Print report
        self.print_verification_report()
        
        # Save results to file
        self.save_results_to_file()
        
        self.get_logger().info('Topic verification completed')

    def analyze_results(self):
        """Analyze verification results"""
        results = {
            'timestamp': datetime.now().isoformat(),
            'verification_duration_s': self.verification_duration,
            'total_expected_topics': len(self.expected_topics),
            'topic_results': {},
            'summary': {
                'active_topics': 0,
                'silent_topics': 0,
                'error_topics': 0,
                'healthy_topics': 0
            }
        }
        
        for topic_name, stats in self.topic_stats.items():
            topic_result = {
                'expected': True,
                'active': stats['message_count'] > 0,
                'message_count': stats['message_count'],
                'error_count': len(stats['errors']),
                'errors': stats['errors'],
                'first_received': stats['first_received'],
                'last_received': stats['last_received'],
                'message_type': stats['message_type']
            }
            
            # Calculate message rate
            if stats['first_received'] and stats['last_received']:
                duration = stats['last_received'] - stats['first_received']
                if duration > 0:
                    topic_result['message_rate_hz'] = stats['message_count'] / duration
                else:
                    topic_result['message_rate_hz'] = 0
            else:
                topic_result['message_rate_hz'] = 0
            
            # Add sample data statistics
            if stats['data_samples']:
                topic_result['sample_count'] = len(stats['data_samples'])
                topic_result['latest_sample'] = stats['data_samples'][-1]
            
            # Determine topic health
            if not topic_result['active']:
                topic_result['health'] = 'SILENT'
                results['summary']['silent_topics'] += 1
            elif topic_result['error_count'] > 0:
                topic_result['health'] = 'ERROR'
                results['summary']['error_topics'] += 1
            else:
                topic_result['health'] = 'HEALTHY'
                results['summary']['healthy_topics'] += 1
                results['summary']['active_topics'] += 1
            
            results['topic_results'][topic_name] = topic_result
        
        return results

    def print_verification_report(self):
        """Print verification report to console"""
        print("\n" + "="*80)
        print("TOPIC VERIFICATION REPORT")
        print("="*80)
        
        summary = self.results['summary']
        print(f"Total Topics Expected: {self.results['total_expected_topics']}")
        print(f"Healthy Topics:       {summary['healthy_topics']}")
        print(f"Silent Topics:        {summary['silent_topics']}")
        print(f"Error Topics:         {summary['error_topics']}")
        print(f"Verification Duration: {self.results['verification_duration_s']}s")
        
        print("\nTOPIC DETAILS:")
        print("-" * 80)
        
        # Sort topics by health status for better readability
        topic_items = sorted(
            self.results['topic_results'].items(),
            key=lambda x: (x[1]['health'], x[0])
        )
        
        for topic_name, result in topic_items:
            status = result['health']
            msg_count = result['message_count']
            rate = result.get('message_rate_hz', 0)
            errors = result['error_count']
            
            status_emoji = {'HEALTHY': '✅', 'SILENT': '❌', 'ERROR': '⚠️ '}.get(status, '?')
            
            print(f"{status_emoji} {topic_name:<40} | "
                  f"Messages: {msg_count:>4} | "
                  f"Rate: {rate:>6.1f}Hz | "
                  f"Errors: {errors}")
            
            # Show errors if any
            if errors > 0:
                for error in result['errors'][:3]:  # Show first 3 errors
                    print(f"    └─ {error}")
                if len(result['errors']) > 3:
                    print(f"    └─ ... and {len(result['errors']) - 3} more errors")
        
        print("\n" + "="*80)
        
        # Overall health assessment
        if summary['silent_topics'] == 0 and summary['error_topics'] == 0:
            print("🎉 ALL TOPICS HEALTHY - System ready for operation!")
        elif summary['silent_topics'] > 0:
            print(f"⚠️  WARNING: {summary['silent_topics']} topics are silent - Check node status")
        elif summary['error_topics'] > 0:
            print(f"❌ ERROR: {summary['error_topics']} topics have errors - Debug required")

    def save_results_to_file(self):
        """Save verification results to JSON file"""
        filename = f"topic_verification_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(self.results, f, indent=2, default=str)
            
            self.get_logger().info(f'Verification results saved to: {filename}')
            
        except Exception as e:
            self.get_logger().error(f'Failed to save results: {e}')


def main():
    parser = argparse.ArgumentParser(description='Verify SomaCube RL system topics')
    parser.add_argument(
        '--duration', '-d', 
        type=float, 
        default=30.0,
        help='Verification duration in seconds (default: 30.0)'
    )
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Reduce log verbosity'
    )
    
    args = parser.parse_args()
    
    rclpy.init()
    
    verifier = TopicVerifier()
    verifier.verification_duration = args.duration
    
    if args.quiet:
        verifier.get_logger().set_level(rclpy.logging.LoggingSeverity.WARN)
    
    try:
        rclpy.spin(verifier)
    except KeyboardInterrupt:
        print("\nVerification interrupted by user")
        if not verifier.verification_complete:
            verifier.complete_verification()
    finally:
        verifier.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()