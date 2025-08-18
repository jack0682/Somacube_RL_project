#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import WrenchStamped, TwistStamped, PoseStamped
from sensor_msgs.msg import Image, JointState
from std_msgs.msg import Bool, String
from doosan_somacube_rl.msg import SafetyEvent, RegisterQuality
import numpy as np
from collections import deque
import time
import cv2
from cv_bridge import CvBridge


class SafetyMonitorNode(Node):
    def __init__(self):
        super().__init__('safety_monitor')
        
        # Parameters
        self.declare_parameters_from_yaml()
        
        # State variables
        self.current_wrench = None
        self.current_velocity = None
        self.current_pose = None
        self.vision_last_time = None
        self.joint_states = None
        self.estop_state = False
        
        # Safety state
        self.safety_violations = deque(maxlen=20)
        self.consecutive_collisions = 0
        self.last_violation_time = 0
        self.backoff_active = False
        self.backoff_start_time = 0
        
        # History for trend analysis
        self.force_history = deque(maxlen=50)
        self.velocity_history = deque(maxlen=50)
        
        # CV bridge for image processing
        self.bridge = CvBridge()
        
        # Subscribers
        self.wrench_sub = self.create_subscription(
            WrenchStamped,
            self.get_parameter('common.topics.ft_wrench').value,
            self.wrench_callback,
            10
        )
        
        self.velocity_sub = self.create_subscription(
            TwistStamped,
            '/doosan/cmd_vel',
            self.velocity_callback,
            10
        )
        
        self.pose_sub = self.create_subscription(
            PoseStamped,
            '/pose_tracker/smoothed_pose',
            self.pose_callback,
            10
        )
        
        self.rgb_sub = self.create_subscription(
            Image,
            self.get_parameter('common.topics.rgb').value,
            self.vision_callback,
            10
        )
        
        self.joint_states_sub = self.create_subscription(
            JointState,
            '/joint_states',
            self.joint_states_callback,
            10
        )
        
        self.estop_sub = self.create_subscription(
            Bool,
            '/system/estop',
            self.estop_callback,
            10
        )
        
        # Publishers
        self.safety_event_pub = self.create_publisher(
            SafetyEvent,
            '/safety/events',
            10
        )
        
        self.emergency_stop_pub = self.create_publisher(
            Bool,
            '/safety/emergency_stop',
            10
        )
        
        self.backoff_cmd_pub = self.create_publisher(
            TwistStamped,
            '/safety/backoff_cmd',
            10
        )
        
        self.safety_status_pub = self.create_publisher(
            String,
            '/safety/status',
            10
        )
        
        # Timer for safety monitoring
        monitor_rate_hz = 50  # High rate for safety
        self.monitor_timer = self.create_timer(1.0 / monitor_rate_hz, self.monitor_callback)
        
        self.get_logger().info('Safety Monitor node initialized')

    def declare_parameters_from_yaml(self):
        """Declare parameters from YAML config"""
        defaults = {
            'common.topics.ft_wrench': '/ee/ft',
            'common.topics.rgb': '/camera/color/image_raw',
            'safety_monitor.rules.force_violation_N': 22.0,
            'safety_monitor.rules.torque_violation_Nm': 2.2,
            'safety_monitor.rules.consecutive_collision_max': 3,
            'safety_monitor.rules.vision_timeout_s': 0.6,
            'safety_monitor.backoff.lin_m': 0.006,
            'safety_monitor.backoff.rot_deg': 3.0,
            'safety_monitor.backoff.speed_scale': 0.5,
            'safety_monitor.backoff.retries': 2
        }
        
        for name, default_value in defaults.items():
            self.declare_parameter(name, default_value)

    def wrench_callback(self, msg):
        """Handle force/torque measurements"""
        self.current_wrench = msg
        
        # Store in history
        current_time = time.time()
        force_data = {
            'timestamp': current_time,
            'force': np.array([msg.wrench.force.x, msg.wrench.force.y, msg.wrench.force.z]),
            'torque': np.array([msg.wrench.torque.x, msg.wrench.torque.y, msg.wrench.torque.z])
        }
        self.force_history.append(force_data)

    def velocity_callback(self, msg):
        """Handle velocity command monitoring"""
        self.current_velocity = msg
        
        # Store in history
        velocity_data = {
            'timestamp': time.time(),
            'linear': np.array([msg.twist.linear.x, msg.twist.linear.y, msg.twist.linear.z]),
            'angular': np.array([msg.twist.angular.x, msg.twist.angular.y, msg.twist.angular.z])
        }
        self.velocity_history.append(velocity_data)

    def pose_callback(self, msg):
        """Handle pose updates"""
        self.current_pose = msg

    def vision_callback(self, msg):
        """Handle vision data for timeout monitoring"""
        self.vision_last_time = time.time()

    def joint_states_callback(self, msg):
        """Handle joint state monitoring"""
        self.joint_states = msg

    def estop_callback(self, msg):
        """Handle emergency stop state"""
        self.estop_state = msg.data
        
        if self.estop_state:
            self.publish_safety_event('EMERGENCY_STOP', 'External E-Stop activated', severity=3)

    def monitor_callback(self):
        """Main safety monitoring loop"""
        current_time = time.time()
        
        try:
            # Check various safety conditions
            self.check_force_violations(current_time)
            self.check_velocity_violations(current_time)
            self.check_vision_timeout(current_time)
            self.check_joint_limits()
            self.check_collision_patterns(current_time)
            
            # Handle backoff if active
            if self.backoff_active:
                self.handle_backoff(current_time)
            
            # Publish safety status
            self.publish_safety_status()
            
        except Exception as e:
            self.get_logger().error(f'Safety monitor error: {e}')

    def check_force_violations(self, current_time):
        """Check for force/torque violations"""
        if not self.current_wrench:
            return
        
        force = np.array([
            self.current_wrench.wrench.force.x,
            self.current_wrench.wrench.force.y,
            self.current_wrench.wrench.force.z
        ])
        
        torque = np.array([
            self.current_wrench.wrench.torque.x,
            self.current_wrench.wrench.torque.y,
            self.current_wrench.wrench.torque.z
        ])
        
        force_limit = self.get_parameter('safety_monitor.rules.force_violation_N').value
        torque_limit = self.get_parameter('safety_monitor.rules.torque_violation_Nm').value
        
        force_mag = np.linalg.norm(force)
        torque_mag = np.linalg.norm(torque)
        
        # Check force violation
        if force_mag > force_limit:
            self.handle_safety_violation(
                'FORCE_VIOLATION',
                f'Force magnitude {force_mag:.2f}N exceeds limit {force_limit}N',
                severity=2,
                current_time=current_time
            )
        
        # Check torque violation
        if torque_mag > torque_limit:
            self.handle_safety_violation(
                'TORQUE_VIOLATION',
                f'Torque magnitude {torque_mag:.2f}Nm exceeds limit {torque_limit}Nm',
                severity=2,
                current_time=current_time
            )
        
        # Check for sudden force spikes (collision detection)
        if len(self.force_history) >= 3:
            recent_forces = [f['force'] for f in list(self.force_history)[-3:]]
            force_changes = []
            
            for i in range(1, len(recent_forces)):
                change = np.linalg.norm(recent_forces[i] - recent_forces[i-1])
                force_changes.append(change)
            
            if force_changes:
                max_change = max(force_changes)
                if max_change > 10.0:  # 10N sudden change
                    self.handle_collision_detection(current_time, max_change)

    def check_velocity_violations(self, current_time):
        """Check for dangerous velocity commands"""
        if not self.current_velocity:
            return
        
        linear_vel = np.array([
            self.current_velocity.twist.linear.x,
            self.current_velocity.twist.linear.y,
            self.current_velocity.twist.linear.z
        ])
        
        angular_vel = np.array([
            self.current_velocity.twist.angular.x,
            self.current_velocity.twist.angular.y,
            self.current_velocity.twist.angular.z
        ])
        
        # Safety velocity limits (more conservative than control limits)
        max_safe_lin_vel = 0.1  # 10cm/s
        max_safe_ang_vel = 0.5  # 0.5 rad/s
        
        lin_speed = np.linalg.norm(linear_vel)
        ang_speed = np.linalg.norm(angular_vel)
        
        if lin_speed > max_safe_lin_vel:
            self.handle_safety_violation(
                'VELOCITY_VIOLATION',
                f'Linear velocity {lin_speed:.3f}m/s exceeds safe limit {max_safe_lin_vel}m/s',
                severity=1,
                current_time=current_time
            )
        
        if ang_speed > max_safe_ang_vel:
            self.handle_safety_violation(
                'VELOCITY_VIOLATION',
                f'Angular velocity {ang_speed:.3f}rad/s exceeds safe limit {max_safe_ang_vel}rad/s',
                severity=1,
                current_time=current_time
            )

    def check_vision_timeout(self, current_time):
        """Check for vision system timeout"""
        if self.vision_last_time is None:
            return
        
        vision_timeout = self.get_parameter('safety_monitor.rules.vision_timeout_s').value
        time_since_vision = current_time - self.vision_last_time
        
        if time_since_vision > vision_timeout:
            self.handle_safety_violation(
                'VISION_TIMEOUT',
                f'No vision data for {time_since_vision:.1f}s (limit {vision_timeout}s)',
                severity=2,
                current_time=current_time
            )

    def check_joint_limits(self):
        """Check for joint limit violations"""
        if not self.joint_states:
            return
        
        # Basic joint limit checking (would need actual robot limits)
        for i, (position, velocity) in enumerate(zip(self.joint_states.position, self.joint_states.velocity)):
            # Example limits - replace with actual robot specifications
            max_velocity = 2.0  # rad/s
            
            if abs(velocity) > max_velocity:
                self.publish_safety_event(
                    'JOINT_VELOCITY',
                    f'Joint {i} velocity {velocity:.2f} exceeds limit {max_velocity}',
                    severity=1
                )

    def check_collision_patterns(self, current_time):
        """Detect collision patterns from recent safety violations"""
        if not self.safety_violations:
            return
        
        # Count recent force/torque violations
        recent_violations = [
            v for v in self.safety_violations 
            if current_time - v['timestamp'] < 5.0 and 
            v['type'] in ['FORCE_VIOLATION', 'TORQUE_VIOLATION']
        ]
        
        if len(recent_violations) >= self.get_parameter('safety_monitor.rules.consecutive_collision_max').value:
            self.handle_safety_violation(
                'COLLISION_PATTERN',
                f'{len(recent_violations)} force violations in 5 seconds',
                severity=3,
                current_time=current_time
            )

    def handle_collision_detection(self, current_time, force_change):
        """Handle sudden collision detection"""
        self.consecutive_collisions += 1
        
        self.publish_safety_event(
            'COLLISION_DETECTED',
            f'Sudden force change {force_change:.1f}N (collision #{self.consecutive_collisions})',
            severity=2
        )
        
        # Trigger backoff maneuver
        self.trigger_backoff(current_time)

    def handle_safety_violation(self, violation_type, detail, severity, current_time):
        """Handle safety violations with appropriate responses"""
        # Store violation
        violation = {
            'type': violation_type,
            'detail': detail,
            'severity': severity,
            'timestamp': current_time
        }
        self.safety_violations.append(violation)
        self.last_violation_time = current_time
        
        # Publish safety event
        self.publish_safety_event(violation_type, detail, severity)
        
        # Take action based on severity
        if severity >= 3:  # Critical
            self.trigger_emergency_stop()
        elif severity >= 2:  # Warning - trigger backoff
            self.trigger_backoff(current_time)

    def trigger_emergency_stop(self):
        """Trigger emergency stop"""
        self.get_logger().error('EMERGENCY STOP TRIGGERED')
        
        # Publish emergency stop
        estop_msg = Bool()
        estop_msg.data = True
        self.emergency_stop_pub.publish(estop_msg)
        
        self.publish_safety_event(
            'EMERGENCY_STOP',
            'Critical safety violation - emergency stop activated',
            severity=3
        )

    def trigger_backoff(self, current_time):
        """Trigger backoff maneuver"""
        if self.backoff_active:
            return  # Already in backoff
        
        self.backoff_active = True
        self.backoff_start_time = current_time
        
        self.get_logger().warn('Backoff maneuver triggered')
        
        self.publish_safety_event(
            'BACKOFF_TRIGGERED',
            'Safety backoff maneuver initiated',
            severity=1
        )

    def handle_backoff(self, current_time):
        """Execute backoff maneuver"""
        backoff_duration = 2.0  # 2 second backoff
        
        if current_time - self.backoff_start_time > backoff_duration:
            # End backoff
            self.backoff_active = False
            self.get_logger().info('Backoff maneuver completed')
            return
        
        # Generate backoff velocity command
        backoff_cmd = TwistStamped()
        backoff_cmd.header.stamp = self.get_clock().now().to_msg()
        backoff_cmd.header.frame_id = 'base_link'
        
        # Move back along negative Z (up) and slightly back
        backoff_linear_m = self.get_parameter('safety_monitor.backoff.lin_m').value
        backoff_rot_deg = self.get_parameter('safety_monitor.backoff.rot_deg').value
        speed_scale = self.get_parameter('safety_monitor.backoff.speed_scale').value
        
        backoff_cmd.twist.linear.z = backoff_linear_m * speed_scale  # Move up
        backoff_cmd.twist.linear.x = -backoff_linear_m * 0.5 * speed_scale  # Move back
        backoff_cmd.twist.angular.y = np.deg2rad(backoff_rot_deg) * speed_scale  # Tilt back
        
        self.backoff_cmd_pub.publish(backoff_cmd)

    def publish_safety_event(self, event_type, detail, severity):
        """Publish safety event message"""
        event_msg = SafetyEvent()
        event_msg.type = event_type
        event_msg.detail = detail
        event_msg.severity = severity
        event_msg.stamp = self.get_clock().now().to_msg()
        
        self.safety_event_pub.publish(event_msg)
        
        # Log with appropriate level
        if severity >= 3:
            self.get_logger().error(f'SAFETY: {event_type} - {detail}')
        elif severity >= 2:
            self.get_logger().warn(f'SAFETY: {event_type} - {detail}')
        else:
            self.get_logger().info(f'SAFETY: {event_type} - {detail}')

    def publish_safety_status(self):
        """Publish overall safety status"""
        current_time = time.time()
        
        # Determine status
        if self.estop_state:
            status = "EMERGENCY_STOP"
        elif self.backoff_active:
            status = "BACKOFF_ACTIVE"
        elif self.safety_violations and (current_time - self.last_violation_time) < 1.0:
            status = "VIOLATION_RECENT"
        elif self.consecutive_collisions > 0 and (current_time - self.last_violation_time) < 10.0:
            status = f"COLLISION_COUNT_{self.consecutive_collisions}"
        else:
            status = "NORMAL"
            # Reset collision count if been normal for a while
            if (current_time - self.last_violation_time) > 10.0:
                self.consecutive_collisions = 0
        
        status_msg = String()
        status_msg.data = status
        self.safety_status_pub.publish(status_msg)

    def get_safety_metrics(self):
        """Get current safety metrics for logging"""
        current_time = time.time()
        
        metrics = {
            'violations_last_minute': len([
                v for v in self.safety_violations 
                if current_time - v['timestamp'] < 60.0
            ]),
            'consecutive_collisions': self.consecutive_collisions,
            'backoff_active': self.backoff_active,
            'estop_state': self.estop_state,
            'time_since_last_violation': current_time - self.last_violation_time if self.last_violation_time else float('inf')
        }
        
        if self.current_wrench:
            force = np.array([
                self.current_wrench.wrench.force.x,
                self.current_wrench.wrench.force.y,
                self.current_wrench.wrench.force.z
            ])
            metrics['current_force_magnitude'] = float(np.linalg.norm(force))
        else:
            metrics['current_force_magnitude'] = 0.0
        
        return metrics


def main(args=None):
    rclpy.init(args=args)
    node = SafetyMonitorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()