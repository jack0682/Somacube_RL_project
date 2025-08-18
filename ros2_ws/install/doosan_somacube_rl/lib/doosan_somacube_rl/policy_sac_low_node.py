#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped, WrenchStamped
from doosan_somacube_rl.msg import PolicyCmd, RegisterQuality
from std_msgs.msg import Float32, Bool
import numpy as np
from scipy.spatial.transform import Rotation as R
import torch
import torch.nn as nn
import torch.nn.functional as F
from collections import deque
import time


class PolicySACLowNode(Node):
    """
    RL Shadow Policy Node (SAC-based low-level control)
    
    Day-0: No actuation - only observation collection and shadow policy execution
    Prepares RL infrastructure for future training phases
    """
    
    def __init__(self):
        super().__init__('policy_sac_low')
        
        # Parameters
        self.declare_parameters_from_yaml()
        
        # RL State
        self.policy_active = False
        self.shadow_mode = True  # Day-0: shadow mode only
        
        # Observation components
        self.current_pose = None
        self.target_pose = None
        self.current_wrench = None
        self.quality_metrics = None
        self.impedance_gains = {'Kp': [1200, 1200, 1500], 'Kd': [60, 60, 80]}
        
        # Experience collection
        self.observation_history = deque(maxlen=1000)
        self.reward_history = deque(maxlen=1000)
        self.episode_count = 0
        self.step_count = 0
        
        # Neural networks (placeholder for Day-0)
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.setup_policy_networks()
        
        # Safety gating parameters
        self.load_safety_gating_params()
        
        # Subscribers
        self.pose_sub = self.create_subscription(
            PoseStamped,
            '/pose_tracker/smoothed_pose',
            self.pose_callback,
            10
        )
        
        self.target_pose_sub = self.create_subscription(
            PoseStamped,
            '/layer1_manager/target_pose',
            self.target_pose_callback,
            10
        )
        
        self.wrench_sub = self.create_subscription(
            WrenchStamped,
            '/ee/ft',
            self.wrench_callback,
            10
        )
        
        self.quality_sub = self.create_subscription(
            RegisterQuality,
            '/pc_register/quality',
            self.quality_callback,
            10
        )
        
        self.policy_enable_sub = self.create_subscription(
            Bool,
            '/policy/enable',
            self.policy_enable_callback,
            10
        )
        
        # Publishers
        self.policy_cmd_pub = self.create_publisher(
            PolicyCmd,
            self.get_parameter('policy_sac_low.action_output.topic').value,
            10
        )
        
        self.reward_pub = self.create_publisher(
            Float32,
            '/policy/reward',
            10
        )
        
        self.confidence_pub = self.create_publisher(
            Float32,
            '/policy/confidence',
            10
        )
        
        self.observation_debug_pub = self.create_publisher(
            Float32,
            '/policy/observation_norm',
            10
        )
        
        # Policy execution timer
        policy_rate_hz = self.get_parameter('common.realtime.policy_rate_hz').value
        self.policy_timer = self.create_timer(1.0 / policy_rate_hz, self.policy_callback)
        
        self.get_logger().info(f'Policy SAC Low node initialized (Shadow mode: {self.shadow_mode})')

    def declare_parameters_from_yaml(self):
        """Declare parameters from YAML config"""
        defaults = {
            'common.realtime.policy_rate_hz': 50,
            'policy_sac_low.observations.use_register_pose': True,
            'policy_sac_low.observations.use_register_quality': True,
            'policy_sac_low.observations.use_wrench': True,
            'policy_sac_low.observations.use_gripper': True,
            'policy_sac_low.observations.use_impedance_gains': True,
            'policy_sac_low.rewards.w_geodesic': 1.2,
            'policy_sac_low.rewards.w_point2plane': 0.8,
            'policy_sac_low.rewards.w_chamfer': 0.5,
            'policy_sac_low.rewards.w_insert_progress': 0.7,
            'policy_sac_low.rewards.w_force_violation': 1.0,
            'policy_sac_low.rewards.w_jerk_force': 0.3,
            'policy_sac_low.rewards.w_inlier_ratio': 0.2,
            'policy_sac_low.rewards.seat_bonus': 3.0,
            'policy_sac_low.rewards.success_geodesic_deg': 1.5,
            'policy_sac_low.rewards.success_pos_m': 0.001,
            'policy_sac_low.safety_gating.force_limit_N': 20.0,
            'policy_sac_low.safety_gating.base_delta_pos_m': 0.004,
            'policy_sac_low.safety_gating.base_delta_rot_deg': 2.0,
            'policy_sac_low.safety_gating.adapt_by_icp_uncertainty': True,
            'policy_sac_low.safety_gating.icp_std_bounds_m': [0.0, 0.010],
            'policy_sac_low.safety_gating.scale_limits.delta_pos_scale_range': [1.0, 0.3],
            'policy_sac_low.safety_gating.scale_limits.delta_rot_scale_range': [1.0, 0.25],
            'policy_sac_low.action_output.topic': '/policy/lo/cmd'
        }
        
        for name, default_value in defaults.items():
            self.declare_parameter(name, default_value)

    def setup_policy_networks(self):
        """Setup SAC policy networks (placeholder for Day-0)"""
        # Observation dimension estimation
        obs_dim = 0
        if self.get_parameter('policy_sac_low.observations.use_register_pose').value:
            obs_dim += 6  # pose error (3 pos + 3 rot)
        if self.get_parameter('policy_sac_low.observations.use_register_quality').value:
            obs_dim += 5  # quality metrics
        if self.get_parameter('policy_sac_low.observations.use_wrench').value:
            obs_dim += 6  # force + torque
        if self.get_parameter('policy_sac_low.observations.use_impedance_gains').value:
            obs_dim += 6  # Kp, Kd gains
        
        self.obs_dim = max(obs_dim, 12)  # Minimum observation dimension
        self.act_dim = 8  # 6 pose delta + 2 gain deltas
        
        # Placeholder policy network (random actions for Day-0)
        self.policy_net = SimplePolicy(self.obs_dim, self.act_dim).to(self.device)
        
        self.get_logger().info(f'Policy networks initialized: obs_dim={self.obs_dim}, act_dim={self.act_dim}')

    def load_safety_gating_params(self):
        """Load safety gating parameters"""
        self.safety_params = {
            'force_limit_N': self.get_parameter('policy_sac_low.safety_gating.force_limit_N').value,
            'base_delta_pos_m': self.get_parameter('policy_sac_low.safety_gating.base_delta_pos_m').value,
            'base_delta_rot_deg': self.get_parameter('policy_sac_low.safety_gating.base_delta_rot_deg').value,
            'adapt_by_icp': self.get_parameter('policy_sac_low.safety_gating.adapt_by_icp_uncertainty').value,
            'icp_std_bounds': self.get_parameter('policy_sac_low.safety_gating.icp_std_bounds_m').value,
            'pos_scale_range': self.get_parameter('policy_sac_low.safety_gating.scale_limits.delta_pos_scale_range').value,
            'rot_scale_range': self.get_parameter('policy_sac_low.safety_gating.scale_limits.delta_rot_scale_range').value
        }

    def pose_callback(self, msg):
        """Handle current pose updates"""
        self.current_pose = msg

    def target_pose_callback(self, msg):
        """Handle target pose updates"""
        self.target_pose = msg

    def wrench_callback(self, msg):
        """Handle force/torque updates"""
        self.current_wrench = msg

    def quality_callback(self, msg):
        """Handle registration quality updates"""
        self.quality_metrics = msg

    def policy_enable_callback(self, msg):
        """Handle policy enable/disable"""
        self.policy_active = msg.data
        if self.policy_active:
            self.get_logger().info('Policy activated (shadow mode)')
        else:
            self.get_logger().info('Policy deactivated')

    def policy_callback(self):
        """Main policy execution loop"""
        if not self.policy_active:
            return
        
        try:
            # Collect observations
            observation = self.collect_observation()
            if observation is None:
                return
            
            # Execute shadow policy
            action, confidence = self.execute_shadow_policy(observation)
            
            # Apply safety gating
            gated_action, gate_confidence = self.apply_safety_gating(action)
            
            # Compute reward (for learning signal)
            reward = self.compute_reward()
            
            # Store experience (for future training)
            self.store_experience(observation, gated_action, reward)
            
            # Publish policy command (shadow mode - for logging only)
            if self.shadow_mode:
                self.publish_shadow_command(gated_action, gate_confidence)
            
            # Publish debug info
            self.publish_debug_info(observation, reward, gate_confidence)
            
            self.step_count += 1
            
        except Exception as e:
            self.get_logger().error(f'Policy execution error: {e}')

    def collect_observation(self):
        """Collect current observation vector"""
        obs_components = []
        
        # Pose error observation
        if self.get_parameter('policy_sac_low.observations.use_register_pose').value:
            pose_error = self.compute_pose_error()
            if pose_error is not None:
                obs_components.extend(pose_error)
            else:
                return None  # Cannot proceed without pose
        
        # Registration quality observation
        if self.get_parameter('policy_sac_low.observations.use_register_quality').value:
            quality_obs = self.extract_quality_observation()
            obs_components.extend(quality_obs)
        
        # Force/torque observation
        if self.get_parameter('policy_sac_low.observations.use_wrench').value:
            wrench_obs = self.extract_wrench_observation()
            obs_components.extend(wrench_obs)
        
        # Impedance gains observation
        if self.get_parameter('policy_sac_low.observations.use_impedance_gains').value:
            gains_obs = self.extract_gains_observation()
            obs_components.extend(gains_obs)
        
        # Pad observation to fixed dimension
        while len(obs_components) < self.obs_dim:
            obs_components.append(0.0)
        
        return np.array(obs_components[:self.obs_dim], dtype=np.float32)

    def compute_pose_error(self):
        """Compute pose error between current and target poses"""
        if not all([self.current_pose, self.target_pose]):
            return None
        
        # Position error
        current_pos = np.array([
            self.current_pose.pose.position.x,
            self.current_pose.pose.position.y,
            self.current_pose.pose.position.z
        ])
        
        target_pos = np.array([
            self.target_pose.pose.position.x,
            self.target_pose.pose.position.y,
            self.target_pose.pose.position.z
        ])
        
        pos_error = target_pos - current_pos
        
        # Rotation error (axis-angle representation)
        current_quat = [
            self.current_pose.pose.orientation.x,
            self.current_pose.pose.orientation.y,
            self.current_pose.pose.orientation.z,
            self.current_pose.pose.orientation.w
        ]
        
        target_quat = [
            self.target_pose.pose.orientation.x,
            self.target_pose.pose.orientation.y,
            self.target_pose.pose.orientation.z,
            self.target_pose.pose.orientation.w
        ]
        
        current_rot = R.from_quat(current_quat)
        target_rot = R.from_quat(target_quat)
        
        # Relative rotation
        rel_rot = target_rot * current_rot.inv()
        rot_error = rel_rot.as_rotvec()
        
        return np.concatenate([pos_error, rot_error])

    def extract_quality_observation(self):
        """Extract registration quality features"""
        if self.quality_metrics is None:
            return [0.0, 0.0, 0.0, 0.0, 0.0]
        
        return [
            self.quality_metrics.mean_point2plane_m,
            self.quality_metrics.chamfer_bidir_m,
            self.quality_metrics.inlier_ratio,
            self.quality_metrics.icp_residual_std,
            np.deg2rad(self.quality_metrics.geodesic_deg)  # Convert to radians
        ]

    def extract_wrench_observation(self):
        """Extract force/torque features"""
        if self.current_wrench is None:
            return [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        
        wrench = self.current_wrench.wrench
        return [
            wrench.force.x, wrench.force.y, wrench.force.z,
            wrench.torque.x, wrench.torque.y, wrench.torque.z
        ]

    def extract_gains_observation(self):
        """Extract impedance gains as observation"""
        # Normalized gain values
        kp_norm = np.array(self.impedance_gains['Kp']) / 2000.0  # Normalize by typical max
        kd_norm = np.array(self.impedance_gains['Kd']) / 100.0
        
        return np.concatenate([kp_norm, kd_norm]).tolist()

    def execute_shadow_policy(self, observation):
        """Execute shadow policy (placeholder for Day-0)"""
        with torch.no_grad():
            obs_tensor = torch.FloatTensor(observation).unsqueeze(0).to(self.device)
            
            # Forward pass through policy network
            action_mean, action_std = self.policy_net(obs_tensor)
            
            # Sample action (for stochastic policy)
            action_dist = torch.distributions.Normal(action_mean, action_std)
            raw_action = action_dist.sample()
            
            # Convert to numpy
            action = raw_action.cpu().numpy().flatten()
            
            # Confidence based on action uncertainty
            confidence = 1.0 / (1.0 + torch.mean(action_std).item())
        
        return action, confidence

    def apply_safety_gating(self, action):
        """Apply safety gating to policy actions"""
        # Extract action components
        delta_pos = action[:3]  # [dx, dy, dz]
        delta_rot = action[3:6]  # [droll, dpitch, dyaw]
        delta_gains = action[6:8]  # [dKp, dKd]
        
        # Base limits
        base_pos_limit = self.safety_params['base_delta_pos_m']
        base_rot_limit = np.deg2rad(self.safety_params['base_delta_rot_deg'])
        
        # Initialize scaling factors
        pos_scale = 1.0
        rot_scale = 1.0
        confidence = 1.0
        
        # Adapt scaling based on ICP uncertainty
        if self.safety_params['adapt_by_icp'] and self.quality_metrics:
            icp_std = self.quality_metrics.icp_residual_std
            std_bounds = self.safety_params['icp_std_bounds']
            
            # Normalize uncertainty
            std_normalized = np.clip(
                (icp_std - std_bounds[0]) / (std_bounds[1] - std_bounds[0]), 
                0.0, 1.0
            )
            
            # Scale factors (higher uncertainty -> more conservative)
            pos_scale_range = self.safety_params['pos_scale_range']
            rot_scale_range = self.safety_params['rot_scale_range']
            
            pos_scale = pos_scale_range[1] + (pos_scale_range[0] - pos_scale_range[1]) * (1 - std_normalized)
            rot_scale = rot_scale_range[1] + (rot_scale_range[0] - rot_scale_range[1]) * (1 - std_normalized)
            
            # Reduce confidence with uncertainty
            confidence *= (1 - std_normalized * 0.5)
        
        # Apply scaling
        delta_pos_scaled = delta_pos * pos_scale
        delta_rot_scaled = delta_rot * rot_scale
        
        # Hard limits
        pos_magnitude = np.linalg.norm(delta_pos_scaled)
        if pos_magnitude > base_pos_limit:
            delta_pos_scaled = delta_pos_scaled / pos_magnitude * base_pos_limit
            confidence *= 0.5
        
        rot_magnitude = np.linalg.norm(delta_rot_scaled)
        if rot_magnitude > base_rot_limit:
            delta_rot_scaled = delta_rot_scaled / rot_magnitude * base_rot_limit
            confidence *= 0.5
        
        # Clamp gain deltas
        delta_gains_clamped = np.clip(delta_gains, -0.5, 0.5)
        
        # Reconstruct gated action
        gated_action = np.concatenate([
            delta_pos_scaled,
            delta_rot_scaled,
            delta_gains_clamped
        ])
        
        return gated_action, np.clip(confidence, 0.0, 1.0)

    def compute_reward(self):
        """Compute reward signal for RL"""
        if not all([self.current_pose, self.target_pose, self.quality_metrics]):
            return 0.0
        
        reward = 0.0
        
        # Registration quality rewards
        w_geodesic = self.get_parameter('policy_sac_low.rewards.w_geodesic').value
        w_point2plane = self.get_parameter('policy_sac_low.rewards.w_point2plane').value
        w_chamfer = self.get_parameter('policy_sac_low.rewards.w_chamfer').value
        w_inlier = self.get_parameter('policy_sac_low.rewards.w_inlier_ratio').value
        
        # Geodesic angle reward (closer to 0 is better)
        geodesic_deg = self.quality_metrics.geodesic_deg
        reward -= w_geodesic * (geodesic_deg / 10.0)  # Normalize by 10 degrees
        
        # Point-to-plane distance reward
        point2plane_m = self.quality_metrics.mean_point2plane_m
        reward -= w_point2plane * (point2plane_m / 0.01)  # Normalize by 1cm
        
        # Chamfer distance reward
        chamfer_m = self.quality_metrics.chamfer_bidir_m
        reward -= w_chamfer * (chamfer_m / 0.01)
        
        # Inlier ratio reward (higher is better)
        inlier_ratio = self.quality_metrics.inlier_ratio
        reward += w_inlier * inlier_ratio
        
        # Force violation penalty
        if self.current_wrench:
            w_force = self.get_parameter('policy_sac_low.rewards.w_force_violation').value
            force_mag = np.sqrt(
                self.current_wrench.wrench.force.x**2 +
                self.current_wrench.wrench.force.y**2 +
                self.current_wrench.wrench.force.z**2
            )
            force_limit = self.safety_params['force_limit_N']
            if force_mag > force_limit:
                reward -= w_force * ((force_mag - force_limit) / force_limit)
        
        # Success bonus
        success_geodesic = self.get_parameter('policy_sac_low.rewards.success_geodesic_deg').value
        success_pos = self.get_parameter('policy_sac_low.rewards.success_pos_m').value
        seat_bonus = self.get_parameter('policy_sac_low.rewards.seat_bonus').value
        
        if geodesic_deg < success_geodesic and point2plane_m < success_pos:
            reward += seat_bonus
        
        return float(reward)

    def store_experience(self, observation, action, reward):
        """Store experience for future training"""
        experience = {
            'timestamp': time.time(),
            'observation': observation.copy(),
            'action': action.copy(),
            'reward': reward,
            'step': self.step_count
        }
        
        self.observation_history.append(experience)
        self.reward_history.append(reward)

    def publish_shadow_command(self, action, confidence):
        """Publish shadow policy command (Day-0: for logging only)"""
        cmd = PolicyCmd()
        cmd.header.stamp = self.get_clock().now().to_msg()
        cmd.header.frame_id = 'policy_shadow'
        
        # Action components
        cmd.dx = float(action[0])
        cmd.dy = float(action[1])
        cmd.dz = float(action[2])
        cmd.droll = float(action[3])
        cmd.dpitch = float(action[4])
        cmd.dyaw = float(action[5])
        cmd.d_kp = float(action[6]) if len(action) > 6 else 0.0
        cmd.d_kd = float(action[7]) if len(action) > 7 else 0.0
        
        # Note: In Day-0 shadow mode, this is published but not actuated
        self.policy_cmd_pub.publish(cmd)

    def publish_debug_info(self, observation, reward, confidence):
        """Publish debug information"""
        # Reward signal
        reward_msg = Float32()
        reward_msg.data = float(reward)
        self.reward_pub.publish(reward_msg)
        
        # Confidence signal
        confidence_msg = Float32()
        confidence_msg.data = float(confidence)
        self.confidence_pub.publish(confidence_msg)
        
        # Observation norm (for monitoring)
        obs_norm = np.linalg.norm(observation)
        obs_norm_msg = Float32()
        obs_norm_msg.data = float(obs_norm)
        self.observation_debug_pub.publish(obs_norm_msg)

    def get_policy_metrics(self):
        """Get policy performance metrics"""
        if not self.reward_history:
            return {}
        
        recent_rewards = list(self.reward_history)[-100:]  # Last 100 rewards
        
        return {
            'total_steps': self.step_count,
            'episode_count': self.episode_count,
            'avg_reward': np.mean(recent_rewards),
            'reward_std': np.std(recent_rewards),
            'max_reward': max(recent_rewards),
            'min_reward': min(recent_rewards),
            'experience_buffer_size': len(self.observation_history)
        }


class SimplePolicy(nn.Module):
    """Simple policy network for Day-0 shadow execution"""
    
    def __init__(self, obs_dim, act_dim, hidden_dim=128):
        super().__init__()
        
        self.obs_dim = obs_dim
        self.act_dim = act_dim
        
        # Simple MLP architecture
        self.fc1 = nn.Linear(obs_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)
        self.fc_mean = nn.Linear(hidden_dim, act_dim)
        self.fc_std = nn.Linear(hidden_dim, act_dim)
        
        # Initialize for small random actions
        self.apply(self._init_weights)
    
    def _init_weights(self, m):
        if isinstance(m, nn.Linear):
            nn.init.xavier_uniform_(m.weight)
            nn.init.constant_(m.bias, 0)
    
    def forward(self, obs):
        x = F.relu(self.fc1(obs))
        x = F.relu(self.fc2(x))
        
        mean = torch.tanh(self.fc_mean(x)) * 0.1  # Small actions for Day-0
        std = F.softplus(self.fc_std(x)) + 1e-4  # Ensure positive std
        
        return mean, std


def main(args=None):
    rclpy.init(args=args)
    node = PolicySACLowNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        # Print policy metrics on exit
        metrics = node.get_policy_metrics()
        node.get_logger().info(f'Policy metrics: {metrics}')
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()