#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped, TwistStamped, WrenchStamped
from sensor_msgs.msg import JointState
from doosan_somacube_rl.msg import PolicyCmd, RegisterQuality
from std_msgs.msg import Bool, Float32
import numpy as np
from scipy.spatial.transform import Rotation as R
import tf2_ros
import tf2_geometry_msgs
from collections import deque
import time


class ImpedanceControlNode(Node):
    def __init__(self):
        super().__init__('imp_ctrl')
        
        # Parameters
        self.declare_parameters_from_yaml()
        
        # State variables
        self.current_pose = None
        self.current_velocity = None
        self.current_wrench = None
        self.target_pose = None
        self.policy_cmd = None
        self.quality_metrics = None
        
        # Control state
        self.control_active = False
        self.last_control_time = time.time()
        
        # Impedance gains (will be adapted)
        self.kp_xyz = np.array(self.get_parameter('imp_ctrl.gains.Kp_xyz').value)
        self.d_xyz = np.array(self.get_parameter('imp_ctrl.gains.D_xyz').value)
        self.kp_abc = np.array(self.get_parameter('imp_ctrl.gains.Kp_abc').value)
        self.d_abc = np.array(self.get_parameter('imp_ctrl.gains.D_abc').value)
        
        # Command history for smoothing
        self.cmd_history = deque(maxlen=5)
        self.wrench_history = deque(maxlen=10)
        
        # TF buffer
        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)
        
        # Subscribers
        self.pose_sub = self.create_subscription(
            PoseStamped,
            '/pose_tracker/smoothed_pose',
            self.pose_callback,
            10
        )
        
        self.velocity_sub = self.create_subscription(
            TwistStamped,
            '/ee/velocity',
            self.velocity_callback,
            10
        )
        
        self.wrench_sub = self.create_subscription(
            WrenchStamped,
            self.get_parameter('common.topics.ft_wrench').value,
            self.wrench_callback,
            10
        )
        
        self.target_pose_sub = self.create_subscription(
            PoseStamped,
            '/layer1_manager/target_pose',
            self.target_pose_callback,
            10
        )
        
        self.policy_cmd_sub = self.create_subscription(
            PolicyCmd,
            '/policy/lo/cmd',
            self.policy_cmd_callback,
            10
        )
        
        self.quality_sub = self.create_subscription(
            RegisterQuality,
            '/pc_register/quality',
            self.quality_callback,
            10
        )
        
        self.enable_sub = self.create_subscription(
            Bool,
            '/imp_ctrl/enable',
            self.enable_callback,
            10
        )
        
        # Publishers
        self.cmd_vel_pub = self.create_publisher(
            TwistStamped,
            '/doosan/cmd_vel',
            10
        )
        
        self.impedance_pub = self.create_publisher(
            WrenchStamped,
            '/doosan/impedance_cmd',
            10
        )
        
        self.confidence_pub = self.create_publisher(
            Float32,
            '/imp_ctrl/confidence',
            10
        )
        
        # Control timer
        control_rate_hz = self.get_parameter('common.realtime.node_rate_hz').value
        self.control_timer = self.create_timer(1.0 / control_rate_hz, self.control_callback)
        
        self.get_logger().info('Impedance Control node initialized')

    def declare_parameters_from_yaml(self):
        """Declare parameters from YAML config"""
        defaults = {
            'common.realtime.node_rate_hz': 100,
            'common.topics.ft_wrench': '/ee/ft',
            'imp_ctrl.mode': 'cartesian_impedance',
            'imp_ctrl.gains.Kp_xyz': [1200.0, 1200.0, 1500.0],
            'imp_ctrl.gains.D_xyz': [60.0, 60.0, 80.0],
            'imp_ctrl.gains.Kp_abc': [15.0, 15.0, 20.0],
            'imp_ctrl.gains.D_abc': [1.5, 1.5, 2.0],
            'imp_ctrl.saturation.max_lin_speed_mps': 0.05,
            'imp_ctrl.saturation.max_ang_speed_dps': 40.0,
            'imp_ctrl.saturation.max_lin_acc_mps2': 0.5,
            'imp_ctrl.saturation.max_ang_acc_dps2': 400.0,
            'imp_ctrl.saturation.max_force_N': 25.0,
            'imp_ctrl.saturation.max_torque_Nm': 3.0,
            'imp_ctrl.adapt_rules.enable': True,
            'imp_ctrl.adapt_rules.insert_progress_window_mm': 5.0,
            'imp_ctrl.adapt_rules.Kp_xyz_scale_range': [1.0, 0.6],
            'imp_ctrl.adapt_rules.D_xyz_scale_range': [1.0, 1.5],
            'policy_sac_low.safety_gating.force_limit_N': 20.0,
            'policy_sac_low.safety_gating.torque_limit_Nm': 2.0,
            'policy_sac_low.safety_gating.base_delta_pos_m': 0.004,
            'policy_sac_low.safety_gating.base_delta_rot_deg': 2.0,
            'policy_sac_low.safety_gating.adapt_by_icp_uncertainty': True,
            'policy_sac_low.safety_gating.icp_std_bounds_m': [0.0, 0.010],
            'policy_sac_low.safety_gating.scale_limits.delta_pos_scale_range': [1.0, 0.3],
            'policy_sac_low.safety_gating.scale_limits.delta_rot_scale_range': [1.0, 0.25],
        }
        
        for name, default_value in defaults.items():
            self.declare_parameter(name, default_value)

    def pose_callback(self, msg):
        """Handle current pose updates"""
        self.current_pose = msg

    def velocity_callback(self, msg):
        """Handle current velocity updates"""
        self.current_velocity = msg

    def wrench_callback(self, msg):
        """Handle force/torque measurements"""
        self.current_wrench = msg
        
        # Store in history for trend analysis
        wrench_data = {
            'timestamp': time.time(),
            'force': np.array([msg.wrench.force.x, msg.wrench.force.y, msg.wrench.force.z]),
            'torque': np.array([msg.wrench.torque.x, msg.wrench.torque.y, msg.wrench.torque.z])
        }
        self.wrench_history.append(wrench_data)

    def target_pose_callback(self, msg):
        """Handle target pose updates"""
        self.target_pose = msg

    def policy_cmd_callback(self, msg):
        """Handle policy command updates"""
        self.policy_cmd = msg

    def quality_callback(self, msg):
        """Handle registration quality updates"""
        self.quality_metrics = msg

    def enable_callback(self, msg):
        """Handle enable/disable commands"""
        self.control_active = msg.data
        if self.control_active:
            self.get_logger().info('Impedance control enabled')
        else:
            self.get_logger().info('Impedance control disabled')

    def control_callback(self):
        """Main control loop"""
        if not self.control_active:
            return
            
        if not all([self.current_pose, self.target_pose]):
            return
            
        try:
            current_time = time.time()
            dt = current_time - self.last_control_time
            self.last_control_time = current_time
            
            # Compute control command
            twist_cmd, confidence = self.compute_impedance_control(dt)
            
            if twist_cmd is not None:
                # Publish velocity command
                twist_msg = TwistStamped()
                twist_msg.header.stamp = self.get_clock().now().to_msg()
                twist_msg.header.frame_id = self.get_parameter('common.frames.base').value
                
                twist_msg.twist.linear.x = twist_cmd[0]
                twist_msg.twist.linear.y = twist_cmd[1]
                twist_msg.twist.linear.z = twist_cmd[2]
                twist_msg.twist.angular.x = twist_cmd[3]
                twist_msg.twist.angular.y = twist_cmd[4]
                twist_msg.twist.angular.z = twist_cmd[5]
                
                self.cmd_vel_pub.publish(twist_msg)
                
                # Publish confidence
                confidence_msg = Float32()
                confidence_msg.data = confidence
                self.confidence_pub.publish(confidence_msg)
                
        except Exception as e:
            self.get_logger().error(f'Control error: {e}')

    def compute_impedance_control(self, dt):
        """Compute impedance control command with confidence gating"""
        # Extract current pose
        current_pos = np.array([
            self.current_pose.pose.position.x,
            self.current_pose.pose.position.y,
            self.current_pose.pose.position.z
        ])
        
        current_quat = [
            self.current_pose.pose.orientation.x,
            self.current_pose.pose.orientation.y,
            self.current_pose.pose.orientation.z,
            self.current_pose.pose.orientation.w
        ]
        current_rot = R.from_quat(current_quat).as_matrix()
        
        # Extract target pose
        target_pos = np.array([
            self.target_pose.pose.position.x,
            self.target_pose.pose.position.y,
            self.target_pose.pose.position.z
        ])
        
        target_quat = [
            self.target_pose.pose.orientation.x,
            self.target_pose.pose.orientation.y,
            self.target_pose.pose.orientation.z,
            self.target_pose.pose.orientation.w
        ]
        target_rot = R.from_quat(target_quat).as_matrix()
        
        # Compute pose error
        pos_error = target_pos - current_pos
        
        # Rotation error (axis-angle)
        rot_error_matrix = target_rot @ current_rot.T
        rot_error_axis_angle = R.from_matrix(rot_error_matrix).as_rotvec()
        
        # Get current velocity (or zero if not available)
        if self.current_velocity:
            current_vel = np.array([
                self.current_velocity.twist.linear.x,
                self.current_velocity.twist.linear.y,
                self.current_velocity.twist.linear.z,
                self.current_velocity.twist.angular.x,
                self.current_velocity.twist.angular.y,
                self.current_velocity.twist.angular.z
            ])
        else:
            current_vel = np.zeros(6)
        
        # Apply policy command if available
        if self.policy_cmd:
            # Policy provides delta corrections
            policy_delta_pos = np.array([self.policy_cmd.dx, self.policy_cmd.dy, self.policy_cmd.dz])
            policy_delta_rot = np.array([self.policy_cmd.droll, self.policy_cmd.dpitch, self.policy_cmd.dyaw])
            
            # Add policy corrections to base errors
            pos_error += policy_delta_pos
            rot_error_axis_angle += policy_delta_rot
            
            # Adapt gains based on policy
            gain_scale_kp = 1.0 + self.policy_cmd.dKp
            gain_scale_kd = 1.0 + self.policy_cmd.dKd
        else:
            gain_scale_kp = 1.0
            gain_scale_kd = 1.0
        
        # Adapt impedance gains based on insertion progress and quality
        adapted_kp_xyz, adapted_d_xyz = self.adapt_impedance_gains(
            pos_error, gain_scale_kp, gain_scale_kd
        )
        
        # Compute impedance forces
        force_cmd = adapted_kp_xyz * pos_error - adapted_d_xyz * current_vel[:3]
        torque_cmd = self.kp_abc * rot_error_axis_angle - self.d_abc * current_vel[3:6]
        
        # Apply safety gating
        gated_force, gated_torque, gate_confidence = self.apply_safety_gating(
            force_cmd, torque_cmd
        )
        
        # Convert to velocity command (simplified impedance -> velocity mapping)
        # In practice, this would go to a robot controller that handles impedance
        vel_cmd = np.zeros(6)
        vel_cmd[:3] = gated_force / np.max(adapted_kp_xyz) * 0.1  # Scale to velocity
        vel_cmd[3:6] = gated_torque / np.max(self.kp_abc) * 0.1
        
        # Apply velocity limits
        vel_cmd = self.apply_velocity_limits(vel_cmd)
        
        # Store command in history
        cmd_data = {
            'timestamp': time.time(),
            'velocity': vel_cmd,
            'confidence': gate_confidence
        }
        self.cmd_history.append(cmd_data)
        
        return vel_cmd, gate_confidence

    def adapt_impedance_gains(self, pos_error, gain_scale_kp, gain_scale_kd):
        """Adapt impedance gains based on insertion progress and quality"""
        base_kp = self.kp_xyz * gain_scale_kp
        base_d = self.d_xyz * gain_scale_kd
        
        if not self.get_parameter('imp_ctrl.adapt_rules.enable').value:
            return base_kp, base_d
        
        # Insertion progress (estimated from z-error and force)
        insertion_progress = 0.0
        if self.current_wrench and abs(pos_error[2]) < 0.01:  # Close to target z
            force_z = self.current_wrench.wrench.force.z
            if force_z > 5.0:  # Contact detected
                window_mm = self.get_parameter('imp_ctrl.adapt_rules.insert_progress_window_mm').value
                insertion_progress = np.clip(abs(pos_error[2]) * 1000 / window_mm, 0.0, 1.0)
        
        # Scale gains based on progress
        kp_range = self.get_parameter('imp_ctrl.adapt_rules.Kp_xyz_scale_range').value
        d_range = self.get_parameter('imp_ctrl.adapt_rules.D_xyz_scale_range').value
        
        kp_scale = kp_range[0] + (kp_range[1] - kp_range[0]) * insertion_progress
        d_scale = d_range[0] + (d_range[1] - d_range[0]) * insertion_progress
        
        adapted_kp = base_kp * kp_scale
        adapted_d = base_d * d_scale
        
        return adapted_kp, adapted_d

    def apply_safety_gating(self, force_cmd, torque_cmd):
        """Apply confidence-based safety gating to control commands"""
        # Base safety limits
        force_limit = self.get_parameter('policy_sac_low.safety_gating.force_limit_N').value
        torque_limit = self.get_parameter('policy_sac_low.safety_gating.torque_limit_Nm').value
        
        # Initialize scaling factors
        force_scale = 1.0
        torque_scale = 1.0
        confidence = 1.0
        
        # Check current forces for safety
        if self.current_wrench:
            current_force = np.array([
                self.current_wrench.wrench.force.x,
                self.current_wrench.wrench.force.y,
                self.current_wrench.wrench.force.z
            ])
            current_force_mag = np.linalg.norm(current_force)
            
            # Reduce commands if already at force limit
            if current_force_mag > force_limit * 0.8:  # 80% of limit
                force_scale = max(0.1, (force_limit - current_force_mag) / (force_limit * 0.2))
                confidence *= 0.5  # Reduce confidence when near limits
        
        # Adapt scaling based on ICP uncertainty
        if self.get_parameter('policy_sac_low.safety_gating.adapt_by_icp_uncertainty').value and self.quality_metrics:
            icp_std = self.quality_metrics.icp_residual_std
            std_bounds = self.get_parameter('policy_sac_low.safety_gating.icp_std_bounds_m').value
            
            # Map ICP std to scale factor
            std_normalized = np.clip((icp_std - std_bounds[0]) / (std_bounds[1] - std_bounds[0]), 0.0, 1.0)
            
            # Get scale ranges
            pos_scale_range = self.get_parameter('policy_sac_low.safety_gating.scale_limits.delta_pos_scale_range').value
            rot_scale_range = self.get_parameter('policy_sac_low.safety_gating.scale_limits.delta_rot_scale_range').value
            
            # Higher uncertainty -> lower scaling
            uncertainty_pos_scale = pos_scale_range[1] + (pos_scale_range[0] - pos_scale_range[1]) * (1 - std_normalized)
            uncertainty_rot_scale = rot_scale_range[1] + (rot_scale_range[0] - rot_scale_range[1]) * (1 - std_normalized)
            
            force_scale *= uncertainty_pos_scale
            torque_scale *= uncertainty_rot_scale
            confidence *= (1 - std_normalized * 0.5)  # Reduce confidence with uncertainty
        
        # Apply scaling
        gated_force = force_cmd * force_scale
        gated_torque = torque_cmd * torque_scale
        
        # Hard limits
        force_mag = np.linalg.norm(gated_force)
        if force_mag > force_limit:
            gated_force = gated_force / force_mag * force_limit
            confidence *= 0.3
        
        torque_mag = np.linalg.norm(gated_torque)
        if torque_mag > torque_limit:
            gated_torque = gated_torque / torque_mag * torque_limit
            confidence *= 0.3
        
        return gated_force, gated_torque, np.clip(confidence, 0.0, 1.0)

    def apply_velocity_limits(self, vel_cmd):
        """Apply velocity and acceleration limits"""
        max_lin_speed = self.get_parameter('imp_ctrl.saturation.max_lin_speed_mps').value
        max_ang_speed = np.deg2rad(self.get_parameter('imp_ctrl.saturation.max_ang_speed_dps').value)
        
        # Linear velocity limits
        lin_vel = vel_cmd[:3]
        lin_speed = np.linalg.norm(lin_vel)
        if lin_speed > max_lin_speed:
            vel_cmd[:3] = lin_vel / lin_speed * max_lin_speed
        
        # Angular velocity limits
        ang_vel = vel_cmd[3:6]
        ang_speed = np.linalg.norm(ang_vel)
        if ang_speed > max_ang_speed:
            vel_cmd[3:6] = ang_vel / ang_speed * max_ang_speed
        
        return vel_cmd

    def get_control_confidence(self):
        """Get current control confidence score"""
        if not self.cmd_history:
            return 0.0
        
        # Use most recent confidence
        recent_confidence = self.cmd_history[-1]['confidence']
        
        # Consider command consistency
        if len(self.cmd_history) >= 3:
            recent_velocities = [cmd['velocity'] for cmd in list(self.cmd_history)[-3:]]
            vel_variations = []
            
            for i in range(1, len(recent_velocities)):
                variation = np.linalg.norm(recent_velocities[i] - recent_velocities[i-1])
                vel_variations.append(variation)
            
            if vel_variations:
                avg_variation = np.mean(vel_variations)
                consistency_score = max(0, 1.0 - avg_variation / 0.01)  # 1cm/s variation threshold
                recent_confidence *= (0.7 + 0.3 * consistency_score)
        
        return np.clip(recent_confidence, 0.0, 1.0)


def main(args=None):
    rclpy.init(args=args)
    node = ImpedanceControlNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()