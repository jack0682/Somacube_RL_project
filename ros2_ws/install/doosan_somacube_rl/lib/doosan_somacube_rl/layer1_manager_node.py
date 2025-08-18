#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped, Point
from std_msgs.msg import String, Bool, Int32
from sensor_msgs.msg import PointCloud2
from visualization_msgs.msg import Marker, MarkerArray
import numpy as np
from scipy.spatial.transform import Rotation as R
import yaml
import json
import time
from enum import Enum


class PieceState(Enum):
    PENDING = "pending"
    READY = "ready" 
    ACTIVE = "active"
    PLACED = "placed"
    FAILED = "failed"


class Layer1ManagerNode(Node):
    def __init__(self):
        super().__init__('layer1_manager')
        
        # Load grid and layout configuration
        self.load_configurations()
        
        # State variables
        self.piece_states = {}
        self.current_piece_id = None
        self.placement_sequence = []
        self.grid_origin_pose = None
        self.assembly_active = False
        self.assembly_start_time = None
        
        # Initialize piece states from layout
        self.initialize_piece_states()
        
        # Subscribers
        self.sequencer_state_sub = self.create_subscription(
            String,
            '/sequencer/state',
            self.sequencer_state_callback,
            10
        )
        
        self.stage_complete_sub = self.create_subscription(
            String,
            '/sequencer/stage_complete',
            self.stage_complete_callback,
            10
        )
        
        self.start_assembly_sub = self.create_subscription(
            Bool,
            '/layer1_manager/start_assembly',
            self.start_assembly_callback,
            10
        )
        
        self.piece_detection_sub = self.create_subscription(
            PointCloud2,
            '/pc_preprocess/output',
            self.piece_detection_callback,
            10
        )
        
        # Publishers
        self.target_pose_pub = self.create_publisher(
            PoseStamped,
            '/layer1_manager/target_pose',
            10
        )
        
        self.current_piece_pub = self.create_publisher(
            Int32,
            '/layer1_manager/current_piece',
            10
        )
        
        self.assembly_status_pub = self.create_publisher(
            String,
            '/layer1_manager/assembly_status',
            10
        )
        
        self.next_piece_ready_pub = self.create_publisher(
            Bool,
            '/layer1_manager/next_piece_ready',
            10
        )
        
        self.grid_markers_pub = self.create_publisher(
            MarkerArray,
            '/grid/markers',
            10
        )
        
        self.assembly_metrics_pub = self.create_publisher(
            String,  # JSON metrics
            '/layer1_manager/metrics',
            10
        )
        
        # Timer for management updates
        management_rate_hz = 5  # 5Hz management updates
        self.management_timer = self.create_timer(1.0 / management_rate_hz, self.management_callback)
        
        # Timer for visualization
        vis_rate_hz = 2  # 2Hz visualization updates
        self.visualization_timer = self.create_timer(1.0 / vis_rate_hz, self.visualization_callback)
        
        self.get_logger().info('Layer 1 Manager node initialized')

    def load_configurations(self):
        """Load grid and layout configurations"""
        # In a real implementation, these would be loaded from the config files
        # For now, define them here based on the YAML content
        
        self.grid_config = {
            'origin': {
                'frame_id': 'base',
                'position': [0.45, 0.0, 0.15],
                'orientation': [0.0, 0.0, 0.0]
            },
            'cell': {
                'size_m': 0.025,
                'units_x': 4,
                'units_y': 4,
                'units_z': 2
            },
            'basis': {
                'ex': [1.0, 0.0, 0.0],
                'ey': [0.0, 1.0, 0.0],
                'ez': [0.0, 0.0, 1.0]
            }
        }
        
        self.layout_config = {
            'layer1': {
                'z_offset_m': 0.002,
                'sequence': [
                    {
                        'piece_id': 1,
                        'type': 'triplet',
                        'target_cell': [0, 0],
                        'preferred_orientation_deg': [0, 90, 180, 270],
                        'stability_priority': 'high',
                        'depends_on': []
                    },
                    {
                        'piece_id': 2,
                        'type': 'triplet',
                        'target_cell': [1, 0],
                        'preferred_orientation_deg': [0, 90],
                        'stability_priority': 'high',
                        'depends_on': []
                    },
                    {
                        'piece_id': 3,
                        'type': 'tetrad',
                        'target_cell': [0, 1],
                        'preferred_orientation_deg': [0, 90, 180, 270],
                        'stability_priority': 'medium',
                        'depends_on': [1]
                    },
                    {
                        'piece_id': 4,
                        'type': 'tetrad',
                        'target_cell': [1, 1],
                        'preferred_orientation_deg': [0, 90, 180, 270],
                        'stability_priority': 'medium',
                        'depends_on': [1, 2]
                    },
                    {
                        'piece_id': 5,
                        'type': 'tetrad',
                        'target_cell': [0, 2],
                        'preferred_orientation_deg': [0, 90, 180, 270],
                        'stability_priority': 'low',
                        'depends_on': [3]
                    },
                    {
                        'piece_id': 6,
                        'type': 'tetrad',
                        'target_cell': [1, 2],
                        'preferred_orientation_deg': [0, 90, 180, 270],
                        'stability_priority': 'low',
                        'depends_on': [4]
                    },
                    {
                        'piece_id': 7,
                        'type': 'unit',
                        'target_cell': [2, 1],
                        'preferred_orientation_deg': [0],
                        'stability_priority': 'minimal',
                        'depends_on': [1, 2, 3, 4, 5, 6]
                    }
                ]
            }
        }

    def initialize_piece_states(self):
        """Initialize piece states from layout configuration"""
        sequence = self.layout_config['layer1']['sequence']
        
        for piece_info in sequence:
            piece_id = piece_info['piece_id']
            self.piece_states[piece_id] = {
                'state': PieceState.PENDING,
                'info': piece_info,
                'placement_attempts': 0,
                'last_attempt_time': None,
                'target_pose': None,
                'orientation_index': 0  # Current orientation being tried
            }
            self.placement_sequence.append(piece_id)
        
        self.get_logger().info(f'Initialized {len(self.piece_states)} pieces for Layer 1 assembly')

    def sequencer_state_callback(self, msg):
        """Handle sequencer state updates"""
        sequencer_state = msg.data
        
        # Update piece states based on sequencer progress
        if sequencer_state == "complete" and self.current_piece_id is not None:
            # Current piece has been successfully placed
            self.mark_piece_placed(self.current_piece_id)

    def stage_complete_callback(self, msg):
        """Handle stage completion notifications"""
        stage = msg.data
        
        if stage == "SEQUENCE_COMPLETE" and self.current_piece_id is not None:
            self.mark_piece_placed(self.current_piece_id)
            self.advance_to_next_piece()

    def start_assembly_callback(self, msg):
        """Handle assembly start command"""
        if msg.data and not self.assembly_active:
            self.start_assembly()
        elif not msg.data and self.assembly_active:
            self.stop_assembly()

    def piece_detection_callback(self, msg):
        """Handle piece detection from vision (placeholder)"""
        # In a real implementation, this would process detected pieces
        # and update their availability for grasping
        pass

    def management_callback(self):
        """Main management loop"""
        current_time = time.time()
        
        try:
            if self.assembly_active:
                # Update piece readiness
                self.update_piece_readiness()
                
                # Check if we need to select next piece
                if self.current_piece_id is None:
                    self.select_next_piece()
                
                # Publish target pose for current piece
                if self.current_piece_id is not None:
                    self.publish_target_pose()
                
                # Check assembly completion
                self.check_assembly_completion()
                
                # Publish assembly status
                self.publish_assembly_status()
                
        except Exception as e:
            self.get_logger().error(f'Management error: {e}')

    def visualization_callback(self):
        """Publish visualization markers"""
        try:
            if self.grid_config.get('visualization', {}).get('publish_grid_markers', False):
                self.publish_grid_markers()
        except Exception as e:
            self.get_logger().warn(f'Visualization error: {e}')

    def start_assembly(self):
        """Start Layer 1 assembly process"""
        self.assembly_active = True
        self.assembly_start_time = time.time()
        self.current_piece_id = None
        
        # Reset all piece states
        for piece_id in self.piece_states:
            self.piece_states[piece_id]['state'] = PieceState.PENDING
            self.piece_states[piece_id]['placement_attempts'] = 0
        
        self.get_logger().info('Layer 1 assembly started')

    def stop_assembly(self):
        """Stop assembly process"""
        self.assembly_active = False
        self.current_piece_id = None
        self.get_logger().info('Layer 1 assembly stopped')

    def update_piece_readiness(self):
        """Update which pieces are ready for placement"""
        for piece_id, piece_state in self.piece_states.items():
            if piece_state['state'] == PieceState.PENDING:
                # Check if dependencies are satisfied
                depends_on = piece_state['info'].get('depends_on', [])
                dependencies_met = all(
                    self.piece_states[dep_id]['state'] == PieceState.PLACED
                    for dep_id in depends_on
                )
                
                if dependencies_met:
                    piece_state['state'] = PieceState.READY
                    self.get_logger().info(f'Piece {piece_id} is now ready for placement')

    def select_next_piece(self):
        """Select the next piece to be placed"""
        # Find highest priority ready piece
        ready_pieces = [
            piece_id for piece_id, piece_state in self.piece_states.items()
            if piece_state['state'] == PieceState.READY
        ]
        
        if not ready_pieces:
            return  # No pieces ready
        
        # Sort by placement sequence order and priority
        def piece_priority(piece_id):
            piece_info = self.piece_states[piece_id]['info']
            sequence_index = self.placement_sequence.index(piece_id)
            priority_map = {'high': 0, 'medium': 1, 'low': 2, 'minimal': 3}
            stability_priority = priority_map.get(piece_info.get('stability_priority', 'low'), 2)
            return (sequence_index, stability_priority)
        
        ready_pieces.sort(key=piece_priority)
        selected_piece = ready_pieces[0]
        
        # Mark as active
        self.piece_states[selected_piece]['state'] = PieceState.ACTIVE
        self.current_piece_id = selected_piece
        
        # Generate target pose
        self.generate_target_pose(selected_piece)
        
        self.get_logger().info(f'Selected piece {selected_piece} for placement')
        
        # Publish current piece
        current_piece_msg = Int32()
        current_piece_msg.data = selected_piece
        self.current_piece_pub.publish(current_piece_msg)

    def generate_target_pose(self, piece_id):
        """Generate target pose for a piece"""
        piece_state = self.piece_states[piece_id]
        piece_info = piece_state['info']
        
        # Get grid cell position
        target_cell = piece_info['target_cell']
        cell_x, cell_y = target_cell
        
        # Calculate world position
        cell_size = self.grid_config['cell']['size_m']
        grid_origin = self.grid_config['origin']['position']
        z_offset = self.layout_config['layer1']['z_offset_m']
        
        world_x = grid_origin[0] + cell_x * cell_size
        world_y = grid_origin[1] + cell_y * cell_size
        world_z = grid_origin[2] + z_offset
        
        # Select orientation
        preferred_orientations = piece_info['preferred_orientation_deg']
        orientation_index = piece_state['orientation_index']
        
        if orientation_index >= len(preferred_orientations):
            # Cycle through orientations or mark as failed
            orientation_index = 0
            piece_state['placement_attempts'] += 1
            
            if piece_state['placement_attempts'] > 3:
                self.mark_piece_failed(piece_id)
                return
        
        selected_orientation_deg = preferred_orientations[orientation_index]
        
        # Create pose
        target_pose = PoseStamped()
        target_pose.header.stamp = self.get_clock().now().to_msg()
        target_pose.header.frame_id = self.grid_config['origin']['frame_id']
        
        target_pose.pose.position.x = world_x
        target_pose.pose.position.y = world_y
        target_pose.pose.position.z = world_z
        
        # Set orientation (rotation around Z-axis)
        orientation_quat = R.from_euler('z', np.deg2rad(selected_orientation_deg)).as_quat()
        target_pose.pose.orientation.x = orientation_quat[0]
        target_pose.pose.orientation.y = orientation_quat[1]
        target_pose.pose.orientation.z = orientation_quat[2]
        target_pose.pose.orientation.w = orientation_quat[3]
        
        piece_state['target_pose'] = target_pose
        piece_state['orientation_index'] = orientation_index

    def publish_target_pose(self):
        """Publish target pose for current piece"""
        if self.current_piece_id is None:
            return
        
        piece_state = self.piece_states[self.current_piece_id]
        target_pose = piece_state.get('target_pose')
        
        if target_pose:
            self.target_pose_pub.publish(target_pose)

    def mark_piece_placed(self, piece_id):
        """Mark piece as successfully placed"""
        if piece_id in self.piece_states:
            self.piece_states[piece_id]['state'] = PieceState.PLACED
            self.get_logger().info(f'Piece {piece_id} successfully placed')
            
            # Log placement metrics
            self.log_piece_placement(piece_id, success=True)

    def mark_piece_failed(self, piece_id):
        """Mark piece as failed placement"""
        if piece_id in self.piece_states:
            self.piece_states[piece_id]['state'] = PieceState.FAILED
            self.get_logger().error(f'Piece {piece_id} failed placement after multiple attempts')
            
            # Log placement metrics
            self.log_piece_placement(piece_id, success=False)

    def advance_to_next_piece(self):
        """Advance to the next piece in the sequence"""
        self.current_piece_id = None
        
        # Signal that we're ready for next piece
        ready_msg = Bool()
        ready_msg.data = True
        self.next_piece_ready_pub.publish(ready_msg)

    def check_assembly_completion(self):
        """Check if assembly is complete"""
        if not self.assembly_active:
            return
        
        placed_pieces = [
            piece_id for piece_id, piece_state in self.piece_states.items()
            if piece_state['state'] == PieceState.PLACED
        ]
        
        total_pieces = len(self.piece_states)
        
        if len(placed_pieces) == total_pieces:
            self.complete_assembly()
        elif any(state['state'] == PieceState.FAILED for state in self.piece_states.values()):
            # Check if we can continue without failed pieces
            self.handle_assembly_failure()

    def complete_assembly(self):
        """Complete assembly process"""
        assembly_time = time.time() - self.assembly_start_time
        self.assembly_active = False
        
        self.get_logger().info(f'Layer 1 assembly completed in {assembly_time:.1f} seconds')
        
        # Log completion metrics
        self.log_assembly_completion(assembly_time)

    def handle_assembly_failure(self):
        """Handle assembly failure scenarios"""
        failed_pieces = [
            piece_id for piece_id, piece_state in self.piece_states.items()
            if piece_state['state'] == PieceState.FAILED
        ]
        
        self.get_logger().error(f'Assembly failure: {len(failed_pieces)} pieces failed')
        
        # Could implement recovery strategies here
        # For now, just stop assembly
        self.assembly_active = False

    def publish_assembly_status(self):
        """Publish current assembly status"""
        if not self.assembly_active:
            status = "IDLE"
        else:
            placed_count = sum(1 for state in self.piece_states.values() if state['state'] == PieceState.PLACED)
            total_count = len(self.piece_states)
            
            if self.current_piece_id is not None:
                status = f"ACTIVE_PIECE_{self.current_piece_id}_PROGRESS_{placed_count}_{total_count}"
            else:
                status = f"SELECTING_NEXT_PROGRESS_{placed_count}_{total_count}"
        
        status_msg = String()
        status_msg.data = status
        self.assembly_status_pub.publish(status_msg)

    def publish_grid_markers(self):
        """Publish grid visualization markers"""
        marker_array = MarkerArray()
        
        # Grid cell markers
        cell_size = self.grid_config['cell']['size_m']
        grid_origin = self.grid_config['origin']['position']
        units_x = self.grid_config['cell']['units_x']
        units_y = self.grid_config['cell']['units_y']
        
        for x in range(units_x):
            for y in range(units_y):
                marker = Marker()
                marker.header.frame_id = self.grid_config['origin']['frame_id']
                marker.header.stamp = self.get_clock().now().to_msg()
                marker.id = x * units_y + y
                marker.type = Marker.CUBE
                marker.action = Marker.ADD
                
                # Position
                marker.pose.position.x = grid_origin[0] + x * cell_size
                marker.pose.position.y = grid_origin[1] + y * cell_size
                marker.pose.position.z = grid_origin[2]
                
                # Orientation
                marker.pose.orientation.w = 1.0
                
                # Scale
                marker.scale.x = cell_size
                marker.scale.y = cell_size
                marker.scale.z = 0.001  # Thin markers
                
                # Color - different for occupied vs empty
                if self.is_cell_occupied(x, y):
                    marker.color.r = 0.0
                    marker.color.g = 1.0
                    marker.color.b = 0.0
                    marker.color.a = 0.6
                else:
                    marker.color.r = 0.5
                    marker.color.g = 0.5
                    marker.color.b = 0.5
                    marker.color.a = 0.3
                
                marker_array.markers.append(marker)
        
        self.grid_markers_pub.publish(marker_array)

    def is_cell_occupied(self, cell_x, cell_y):
        """Check if a grid cell is occupied by a placed piece"""
        for piece_state in self.piece_states.values():
            if piece_state['state'] == PieceState.PLACED:
                target_cell = piece_state['info']['target_cell']
                if target_cell[0] == cell_x and target_cell[1] == cell_y:
                    return True
        return False

    def log_piece_placement(self, piece_id, success):
        """Log piece placement attempt"""
        piece_state = self.piece_states[piece_id]
        
        log_data = {
            'timestamp': time.time(),
            'event': 'piece_placement',
            'piece_id': piece_id,
            'success': success,
            'attempts': piece_state['placement_attempts'],
            'piece_type': piece_state['info']['type'],
            'target_cell': piece_state['info']['target_cell'],
            'orientation_tried': piece_state['orientation_index']
        }
        
        metrics_msg = String()
        metrics_msg.data = json.dumps(log_data)
        self.assembly_metrics_pub.publish(metrics_msg)

    def log_assembly_completion(self, assembly_time):
        """Log assembly completion metrics"""
        placed_count = sum(1 for state in self.piece_states.values() if state['state'] == PieceState.PLACED)
        failed_count = sum(1 for state in self.piece_states.values() if state['state'] == PieceState.FAILED)
        total_attempts = sum(state['placement_attempts'] for state in self.piece_states.values())
        
        log_data = {
            'timestamp': time.time(),
            'event': 'assembly_complete',
            'total_time_s': assembly_time,
            'pieces_placed': placed_count,
            'pieces_failed': failed_count,
            'total_pieces': len(self.piece_states),
            'total_placement_attempts': total_attempts,
            'success_rate': placed_count / len(self.piece_states) if self.piece_states else 0.0
        }
        
        metrics_msg = String()
        metrics_msg.data = json.dumps(log_data)
        self.assembly_metrics_pub.publish(metrics_msg)

    def get_assembly_metrics(self):
        """Get current assembly metrics"""
        if not self.assembly_active:
            return {}
        
        placed_count = sum(1 for state in self.piece_states.values() if state['state'] == PieceState.PLACED)
        active_count = sum(1 for state in self.piece_states.values() if state['state'] == PieceState.ACTIVE)
        failed_count = sum(1 for state in self.piece_states.values() if state['state'] == PieceState.FAILED)
        
        elapsed_time = time.time() - self.assembly_start_time if self.assembly_start_time else 0
        
        return {
            'elapsed_time_s': elapsed_time,
            'pieces_placed': placed_count,
            'pieces_active': active_count,
            'pieces_failed': failed_count,
            'total_pieces': len(self.piece_states),
            'current_piece_id': self.current_piece_id,
            'completion_percentage': (placed_count / len(self.piece_states)) * 100 if self.piece_states else 0
        }


def main(args=None):
    rclpy.init(args=args)
    node = Layer1ManagerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()