#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped, WrenchStamped
from std_msgs.msg import String, Bool, Int32
from doosan_somacube_rl.msg import RegisterQuality, SafetyEvent
from sensor_msgs.msg import JointState
import numpy as np
from scipy.spatial.transform import Rotation as R
from enum import Enum
import time
import json


class SequenceState(Enum):
    IDLE = "idle"
    APPROACH = "approach"
    ALIGN = "align" 
    PLACE = "place"
    RETRACT = "retract"
    COMPLETE = "complete"
    ERROR = "error"
    REGRASP = "regrasp"


class SequencerNode(Node):
    def __init__(self):
        super().__init__('sequencer')
        
        # Parameters
        self.declare_parameters_from_yaml()
        
        # State variables
        self.current_state = SequenceState.IDLE
        self.state_start_time = time.time()
        self.retry_count = 0
        self.current_pose = None
        self.target_pose = None
        self.quality_metrics = None
        self.current_wrench = None
        self.safety_status = "NORMAL"
        
        # State transition criteria
        self.last_successful_stage_time = time.time()
        self.stage_completion_times = {}
        
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
        
        self.quality_sub = self.create_subscription(
            RegisterQuality,
            '/pc_register/quality',
            self.quality_callback,
            10
        )
        
        self.wrench_sub = self.create_subscription(
            WrenchStamped,
            self.get_parameter('common.topics.ft_wrench').value,
            self.wrench_callback,
            10
        )
        
        self.safety_status_sub = self.create_subscription(
            String,
            '/safety/status',
            self.safety_status_callback,
            10
        )
        
        self.safety_event_sub = self.create_subscription(
            SafetyEvent,
            '/safety/events',
            self.safety_event_callback,
            10
        )
        
        self.start_sequence_sub = self.create_subscription(
            Bool,
            '/sequencer/start',
            self.start_sequence_callback,
            10
        )
        
        # Publishers
        self.state_pub = self.create_publisher(
            String,
            '/sequencer/state',
            10
        )
        
        self.stage_complete_pub = self.create_publisher(
            String,
            '/sequencer/stage_complete',
            10
        )
        
        self.imp_ctrl_enable_pub = self.create_publisher(
            Bool,
            '/imp_ctrl/enable',
            10
        )
        
        self.replan_trigger_pub = self.create_publisher(
            Bool,
            '/planner_kang/replan',
            10
        )
        
        self.sequence_metrics_pub = self.create_publisher(
            String,  # JSON string with metrics
            '/sequencer/metrics',
            10
        )
        
        # State machine timer
        state_machine_rate_hz = 20  # 20Hz state machine updates
        self.state_timer = self.create_timer(1.0 / state_machine_rate_hz, self.state_machine_callback)
        
        self.get_logger().info('Sequencer node initialized')

    def declare_parameters_from_yaml(self):
        """Declare parameters from YAML config"""
        defaults = {
            'common.topics.ft_wrench': '/ee/ft',
            'sequencer.max_stage_time_s': 40.0,
            'sequencer.max_retries_per_stage': 3,
            'sequencer.switch_thresholds.geodesic_deg': 1.5,
            'sequencer.switch_thresholds.pos_m': 0.001,
            'sequencer.switch_thresholds.no_force_violation': True,
            'sequencer.regrasp_policy.enable': True,
            'sequencer.regrasp_policy.trigger_if_retries_exceed': 2,
            'sequencer.regrasp_policy.alt_approach_dirs_deg': [0, 90, 180, 270],
            'sequencer.logging.write_decisions': True
        }
        
        for name, default_value in defaults.items():
            self.declare_parameter(name, default_value)

    def pose_callback(self, msg):
        """Handle current pose updates"""
        self.current_pose = msg

    def target_pose_callback(self, msg):
        """Handle target pose updates"""
        self.target_pose = msg

    def quality_callback(self, msg):
        """Handle quality metrics updates"""
        self.quality_metrics = msg

    def wrench_callback(self, msg):
        """Handle force/torque updates"""
        self.current_wrench = msg

    def safety_status_callback(self, msg):
        """Handle safety status updates"""
        self.safety_status = msg.data

    def safety_event_callback(self, msg):
        """Handle safety events"""
        # Handle critical safety events by transitioning to error state
        if msg.severity >= 3:  # Critical
            self.get_logger().error(f'Critical safety event: {msg.type} - {msg.detail}')
            self.transition_to_state(SequenceState.ERROR, f'Safety event: {msg.type}')
        elif msg.severity >= 2 and msg.type in ['FORCE_VIOLATION', 'COLLISION_DETECTED']:
            # Force violations might require replan or regrasp
            self.handle_force_violation_during_sequence()

    def start_sequence_callback(self, msg):
        """Handle sequence start command"""
        if msg.data and self.current_state == SequenceState.IDLE:
            self.get_logger().info('Starting new sequence')
            self.transition_to_state(SequenceState.APPROACH, 'Sequence started')

    def state_machine_callback(self):
        """Main state machine update"""
        current_time = time.time()
        
        try:
            # Check for timeouts
            self.check_stage_timeout(current_time)
            
            # Execute current state logic
            if self.current_state == SequenceState.IDLE:
                self.handle_idle_state()
            elif self.current_state == SequenceState.APPROACH:
                self.handle_approach_state(current_time)
            elif self.current_state == SequenceState.ALIGN:
                self.handle_align_state(current_time)
            elif self.current_state == SequenceState.PLACE:
                self.handle_place_state(current_time)
            elif self.current_state == SequenceState.RETRACT:
                self.handle_retract_state(current_time)
            elif self.current_state == SequenceState.COMPLETE:
                self.handle_complete_state()
            elif self.current_state == SequenceState.ERROR:
                self.handle_error_state(current_time)
            elif self.current_state == SequenceState.REGRASP:
                self.handle_regrasp_state(current_time)
            
            # Publish current state
            self.publish_state()
            
        except Exception as e:
            self.get_logger().error(f'State machine error: {e}')
            self.transition_to_state(SequenceState.ERROR, f'State machine error: {e}')

    def handle_idle_state(self):
        """Handle IDLE state - waiting for sequence start"""
        # Ensure impedance control is disabled
        self.set_impedance_control(False)

    def handle_approach_state(self, current_time):
        """Handle APPROACH state - moving to approximate target position"""
        # Enable impedance control
        self.set_impedance_control(True)
        
        # Check if we have valid target pose
        if not self.target_pose:
            self.get_logger().warn('No target pose available for approach')
            return
        
        # Check approach completion criteria
        if self.is_approach_complete():
            self.transition_to_state(SequenceState.ALIGN, 'Approach complete, starting alignment')

    def handle_align_state(self, current_time):
        """Handle ALIGN state - fine alignment using vision and RL"""
        # Ensure impedance control is active
        self.set_impedance_control(True)
        
        # Check alignment completion criteria
        if self.is_alignment_complete():
            self.transition_to_state(SequenceState.PLACE, 'Alignment complete, starting placement')

    def handle_place_state(self, current_time):
        """Handle PLACE state - final insertion with force control"""
        # Check placement completion criteria
        if self.is_placement_complete():
            self.transition_to_state(SequenceState.RETRACT, 'Placement complete, retracting')

    def handle_retract_state(self, current_time):
        """Handle RETRACT state - backing away from completed placement"""
        # Check retraction completion
        if self.is_retraction_complete():
            self.transition_to_state(SequenceState.COMPLETE, 'Retraction complete, sequence finished')

    def handle_complete_state(self):
        """Handle COMPLETE state - sequence successfully finished"""
        # Disable impedance control
        self.set_impedance_control(False)
        
        # Publish completion
        self.stage_complete_pub.publish(String(data="SEQUENCE_COMPLETE"))
        
        # Log completion metrics
        self.log_sequence_completion()
        
        # Transition back to idle for next sequence
        self.transition_to_state(SequenceState.IDLE, 'Sequence completed, returning to idle')

    def handle_error_state(self, current_time):
        """Handle ERROR state - recover from errors or abort"""
        # Disable impedance control for safety
        self.set_impedance_control(False)
        
        # Check if we should retry or abort
        max_retries = self.get_parameter('sequencer.max_retries_per_stage').value
        
        if self.retry_count < max_retries:
            # Wait a bit before retry
            if current_time - self.state_start_time > 2.0:  # 2 second pause
                self.retry_count += 1
                self.get_logger().info(f'Retrying sequence (attempt {self.retry_count}/{max_retries})')
                
                # Check if we should trigger regrasp
                if self.should_trigger_regrasp():
                    self.transition_to_state(SequenceState.REGRASP, 'Triggering regrasp strategy')
                else:
                    self.transition_to_state(SequenceState.APPROACH, 'Retrying from approach')
        else:
            self.get_logger().error('Max retries exceeded, sequence failed')
            self.transition_to_state(SequenceState.IDLE, 'Sequence aborted after max retries')

    def handle_regrasp_state(self, current_time):
        """Handle REGRASP state - alternative grasp strategy"""
        # Trigger replan with alternative approach
        replan_msg = Bool()
        replan_msg.data = True
        self.replan_trigger_pub.publish(replan_msg)
        
        # Wait for replan to complete (simplified - in practice monitor replan status)
        if current_time - self.state_start_time > 5.0:  # 5 second replan time
            self.retry_count = 0  # Reset retry count for new grasp
            self.transition_to_state(SequenceState.APPROACH, 'Regrasp complete, trying new approach')

    def is_approach_complete(self):
        """Check if approach phase is complete"""
        if not all([self.current_pose, self.target_pose]):
            return False
        
        # Calculate position error
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
        
        pos_error = np.linalg.norm(target_pos - current_pos)
        
        # Approach is complete when within rough positioning tolerance
        approach_tolerance_m = 0.02  # 2cm tolerance for approach
        return pos_error < approach_tolerance_m

    def is_alignment_complete(self):
        """Check if alignment phase is complete"""
        if not self.quality_metrics:
            return False
        
        # Check quality-based alignment criteria
        geodesic_threshold = self.get_parameter('sequencer.switch_thresholds.geodesic_deg').value
        pos_threshold = self.get_parameter('sequencer.switch_thresholds.pos_m').value
        
        geodesic_ok = self.quality_metrics.geodesic_deg < geodesic_threshold
        
        # Estimate position error from point-to-plane distance
        pos_ok = self.quality_metrics.mean_point2plane_m < pos_threshold
        
        # Check no recent force violations if required
        force_ok = True
        if self.get_parameter('sequencer.switch_thresholds.no_force_violation').value:
            force_ok = self.safety_status == "NORMAL"
        
        # Additional quality checks
        quality_ok = (
            self.quality_metrics.inlier_ratio > 0.3 and  # Minimum inlier ratio
            self.quality_metrics.icp_residual_std < 0.005  # Good registration precision
        )
        
        alignment_complete = geodesic_ok and pos_ok and force_ok and quality_ok
        
        if alignment_complete:
            self.get_logger().info(
                f'Alignment complete: geodesic={self.quality_metrics.geodesic_deg:.1f}°, '
                f'pos_err={self.quality_metrics.mean_point2plane_m*1000:.1f}mm, '
                f'inlier={self.quality_metrics.inlier_ratio:.2f}'
            )
        
        return alignment_complete

    def is_placement_complete(self):
        """Check if placement phase is complete"""
        # Placement is complete when piece is seated (detected via force profile)
        if not self.current_wrench:
            return False
        
        # Check for stable contact forces indicating seating
        force_z = self.current_wrench.wrench.force.z
        
        # Look for characteristic force profile of successful insertion
        contact_force_threshold = 8.0  # N
        max_insertion_force = 15.0  # N
        
        # Placed when moderate contact force (piece resting but not excessive)
        placement_complete = (contact_force_threshold < force_z < max_insertion_force)
        
        # Additional check: position should be stable
        if placement_complete and self.quality_metrics:
            # Verify we're still well aligned
            if self.quality_metrics.geodesic_deg > 3.0:  # Lost alignment
                placement_complete = False
        
        return placement_complete

    def is_retraction_complete(self):
        """Check if retraction phase is complete"""
        if not self.current_wrench:
            return True  # No force sensor, assume complete
        
        # Retraction complete when forces return to low levels
        force_magnitude = np.sqrt(
            self.current_wrench.wrench.force.x**2 +
            self.current_wrench.wrench.force.y**2 +
            self.current_wrench.wrench.force.z**2
        )
        
        return force_magnitude < 3.0  # 3N threshold

    def check_stage_timeout(self, current_time):
        """Check for stage timeouts"""
        max_stage_time = self.get_parameter('sequencer.max_stage_time_s').value
        time_in_stage = current_time - self.state_start_time
        
        if time_in_stage > max_stage_time:
            self.get_logger().warn(f'Stage timeout in {self.current_state.value} after {time_in_stage:.1f}s')
            self.transition_to_state(SequenceState.ERROR, f'Stage timeout: {self.current_state.value}')

    def handle_force_violation_during_sequence(self):
        """Handle force violations that occur during sequence execution"""
        if self.current_state in [SequenceState.ALIGN, SequenceState.PLACE]:
            # Force violations during alignment/placement might require strategy change
            self.get_logger().warn(f'Force violation in {self.current_state.value} state')
            
            # Transition to error state for recovery
            self.transition_to_state(SequenceState.ERROR, 'Force violation during critical phase')

    def should_trigger_regrasp(self):
        """Determine if regrasp strategy should be triggered"""
        if not self.get_parameter('sequencer.regrasp_policy.enable').value:
            return False
        
        trigger_threshold = self.get_parameter('sequencer.regrasp_policy.trigger_if_retries_exceed').value
        return self.retry_count >= trigger_threshold

    def transition_to_state(self, new_state, reason=""):
        """Transition to a new sequence state"""
        if new_state == self.current_state:
            return
        
        old_state = self.current_state
        self.current_state = new_state
        self.state_start_time = time.time()
        
        # Log completion time of previous stage
        if old_state != SequenceState.IDLE:
            completion_time = time.time() - self.last_successful_stage_time
            self.stage_completion_times[old_state.value] = completion_time
            self.last_successful_stage_time = time.time()
        
        # Reset retry count for new stages (but not for error recovery)
        if new_state != SequenceState.ERROR:
            self.retry_count = 0
        
        self.get_logger().info(f'State transition: {old_state.value} -> {new_state.value} ({reason})')
        
        # Log decision if enabled
        if self.get_parameter('sequencer.logging.write_decisions').value:
            self.log_state_transition(old_state, new_state, reason)

    def set_impedance_control(self, enable):
        """Enable or disable impedance control"""
        enable_msg = Bool()
        enable_msg.data = enable
        self.imp_ctrl_enable_pub.publish(enable_msg)

    def publish_state(self):
        """Publish current sequence state"""
        state_msg = String()
        state_msg.data = self.current_state.value
        self.state_pub.publish(state_msg)

    def log_state_transition(self, old_state, new_state, reason):
        """Log state transition with context"""
        log_data = {
            'timestamp': time.time(),
            'old_state': old_state.value,
            'new_state': new_state.value,
            'reason': reason,
            'retry_count': self.retry_count,
            'safety_status': self.safety_status
        }
        
        # Add quality metrics if available
        if self.quality_metrics:
            log_data['quality'] = {
                'geodesic_deg': self.quality_metrics.geodesic_deg,
                'mean_point2plane_m': self.quality_metrics.mean_point2plane_m,
                'inlier_ratio': self.quality_metrics.inlier_ratio
            }
        
        # Add force data if available
        if self.current_wrench:
            force_mag = np.sqrt(
                self.current_wrench.wrench.force.x**2 +
                self.current_wrench.wrench.force.y**2 +
                self.current_wrench.wrench.force.z**2
            )
            log_data['force_magnitude'] = force_mag
        
        # Publish as JSON
        metrics_msg = String()
        metrics_msg.data = json.dumps(log_data)
        self.sequence_metrics_pub.publish(metrics_msg)

    def log_sequence_completion(self):
        """Log metrics for completed sequence"""
        total_time = sum(self.stage_completion_times.values())
        
        completion_data = {
            'timestamp': time.time(),
            'event': 'sequence_complete',
            'total_time_s': total_time,
            'stage_times': self.stage_completion_times,
            'total_retries': self.retry_count,
            'safety_violations': 0  # Would track from safety monitor
        }
        
        self.get_logger().info(f'Sequence completed in {total_time:.1f}s with {self.retry_count} retries')
        
        # Reset for next sequence
        self.stage_completion_times = {}

    def get_sequence_status(self):
        """Get current sequence status for external monitoring"""
        return {
            'current_state': self.current_state.value,
            'time_in_state': time.time() - self.state_start_time,
            'retry_count': self.retry_count,
            'safety_status': self.safety_status,
            'stage_completion_times': self.stage_completion_times
        }


def main(args=None):
    rclpy.init(args=args)
    node = SequencerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()