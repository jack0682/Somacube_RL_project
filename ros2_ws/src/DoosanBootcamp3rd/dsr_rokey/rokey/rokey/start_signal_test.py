#!/usr/bin/env python3

# Import ROS2 Python client library for creating nodes
import rclpy
# Import the base Node class for creating ROS2 nodes
from rclpy.node import Node
# Import Int32 message type for subscribing to start signal
from std_msgs.msg import Int32
# Import QoS for reliable message delivery configuration
from rclpy.qos import QoSProfile, ReliabilityPolicy
# Import time for timestamping received messages
import time
# Import datetime for human-readable timestamps
from datetime import datetime
# Import signal for graceful shutdown handling
import signal
# Import sys for system operations
import sys


class StartSignalTestNode(Node):
    """
    ROS2 test node that subscribes to /start_signal topic.
    Prints "START RECEIVED" when receiving Int32 value=1.
    Used to verify the speech-to-text trigger functionality.
    """

    def __init__(self):
        # Initialize the parent Node class with node name 'start_signal_test_node'
        super().__init__('start_signal_test_node')
        
        # Create QoS profile matching the publisher (Reliable delivery, depth=10)
        start_signal_qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,  # Reliable delivery as required
            depth=10                                # Queue depth of 10 as required
        )
        
        # Create a subscriber for Int32 messages on '/start_signal' topic
        # This will receive start signals from the speech-to-text node
        self.subscription = self.create_subscription(
            Int32,                          # Message type
            '/start_signal',               # Topic name
            self.start_signal_callback,    # Callback function
            start_signal_qos              # QoS profile
        )
        
        # Counter to track how many start signals have been received
        self.signal_count = 0
        
        # Shutdown flag for clean termination
        self.shutdown_requested = False
        
        # Store the subscription to prevent garbage collection
        self.subscription  # prevent unused variable warning
        
        # Log node initialization
        self.get_logger().info('Start Signal Test Node initialized')
        self.get_logger().info('Listening for start signals on /start_signal topic...')
        self.get_logger().info('QoS: Reliable delivery, depth=10')

    def start_signal_callback(self, msg):
        """
        Callback function executed when a message is received on /start_signal topic.
        Prints "START RECEIVED" when value=1 and logs all received messages.
        
        Args:
            msg (Int32): The received message containing the start signal value
        """
        # Get current timestamp for logging
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        
        # Increment the signal counter
        self.signal_count += 1
        
        # Log all received messages for debugging
        self.get_logger().info(f'[{timestamp}] Received signal #{self.signal_count}: value={msg.data}')
        
        # Check if the received value is 1 (the trigger signal)
        if msg.data == 1:
            # Print the required message to console
            print(f"\n🚀 START RECEIVED (#{self.signal_count}) at {timestamp} 🚀")
            
            # Also log it for ROS2 logging system
            self.get_logger().warn(f'START SIGNAL TRIGGERED: #{self.signal_count} at {timestamp}')
            
        else:
            # Log non-trigger values for debugging
            self.get_logger().debug(f'Non-trigger value received: {msg.data}')

    def get_statistics(self):
        """
        Get statistics about received start signals.
        
        Returns:
            dict: Dictionary containing signal statistics
        """
        return {
            'total_signals_received': self.signal_count,
            'node_name': self.get_name(),
            'topic_name': '/start_signal',
            'shutdown_requested': self.shutdown_requested
        }

    def request_shutdown(self):
        """
        Request clean shutdown of the test node.
        """
        self.get_logger().info('🛑 Shutdown requested for test node')
        self.shutdown_requested = True


def signal_handler_test(signum, frame, node):
    """
    Signal handler for graceful shutdown of test node.
    
    Args:
        signum: Signal number
        frame: Current stack frame
        node: StartSignalTestNode instance
    """
    print(f"\n🛑 Test node received signal {signum} - shutting down...")
    if node:
        node.request_shutdown()
    sys.exit(0)


def main(args=None):
    """
    Main function to initialize ROS2, create and spin the test node with optimized shutdown.
    """
    # Initialize the ROS2 Python client library
    rclpy.init(args=args)
    
    # Create an instance of the StartSignalTestNode
    start_signal_test_node = None
    
    try:
        # Create the test node instance
        start_signal_test_node = StartSignalTestNode()
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, lambda s, f: signal_handler_test(s, f, start_signal_test_node))
        signal.signal(signal.SIGTERM, lambda s, f: signal_handler_test(s, f, start_signal_test_node))
        
        # Print initial status message
        print("\n" + "="*70)
        print("🎯 START SIGNAL TEST NODE RUNNING")
        print("🔊 Waiting for start signals from speech-to-text node...")
        print("🎤 Say '시작해' into the microphone to test!")
        print("🛑 Press Ctrl+C to stop")
        print("="*70 + "\n")
        
        # Keep the node running and processing callbacks
        # Use spin_once with timeout for better shutdown handling
        while rclpy.ok() and not start_signal_test_node.shutdown_requested:
            rclpy.spin_once(start_signal_test_node, timeout_sec=1.0)
        
    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        print("\n🛑 Keyboard interrupt received")
        if start_signal_test_node:
            start_signal_test_node.get_logger().info('Test node stopped by user (Ctrl+C)')
        
    except Exception as e:
        # Handle unexpected errors
        print(f"\n❌ Unexpected error in test node: {str(e)}")
        if start_signal_test_node:
            start_signal_test_node.get_logger().error(f'Unexpected error: {str(e)}')
        
    finally:
        print("\n🧹 Test node cleanup...")
        
        # Display final statistics
        if start_signal_test_node:
            try:
                stats = start_signal_test_node.get_statistics()
                print("📊 Test Session Summary:")
                print(f"   - Total start signals received: {stats['total_signals_received']}")
                print(f"   - Node name: {stats['node_name']}")
                print(f"   - Topic monitored: {stats['topic_name']}")
                
                # Destroy the node
                start_signal_test_node.destroy_node()
                
            except Exception as e:
                print(f"⚠️  Error during test node cleanup: {str(e)}")
        
        # Shutdown ROS2
        try:
            rclpy.shutdown()
            print("✅ Test node shutdown complete")
        except Exception as e:
            print(f"⚠️  Error during ROS2 shutdown: {str(e)}")
        
        print("👋 Start Signal Test Node terminated\n")


# Entry point when script is run directly
if __name__ == '__main__':
    main()