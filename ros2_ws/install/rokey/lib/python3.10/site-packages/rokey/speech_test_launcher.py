#!/usr/bin/env python3

# Korean Speech-to-Text Test Launcher
# This script launches both speech-to-text and test nodes for easy testing

# Import system modules
import os
import sys
import subprocess
import time
import signal
import argparse
# Import ROS2 modules
import rclpy
from rclpy.executors import MultiThreadedExecutor
# Import our nodes
from rokey.speech_to_text import SpeechToTextNode
from rokey.start_signal_test import StartSignalTestNode


class SpeechTestLauncher:
    """
    Launcher class that manages both speech-to-text and test nodes.
    Provides easy testing and debugging for the Korean speech recognition system.
    """
    
    def __init__(self):
        # Store node instances
        self.speech_node = None
        self.test_node = None
        self.executor = None
        self.shutdown_requested = False
        
    def signal_handler(self, signum, frame):
        """
        Handle shutdown signals gracefully.
        """
        print(f"\n🛑 Received signal {signum} - shutting down launcher...")
        self.shutdown_requested = True
        
        if self.speech_node:
            self.speech_node.request_shutdown()
        if self.test_node:
            self.test_node.request_shutdown()
            
        sys.exit(0)
    
    def print_banner(self):
        """
        Print startup banner with instructions.
        """
        print("\n" + "="*80)
        print("🎤 KOREAN SPEECH-TO-TEXT TEST LAUNCHER")
        print("="*80)
        print("🚀 Starting both speech recognition and test nodes...")
        print("🎯 Say '시작해' clearly to trigger the start signal")
        print("🔍 Real-time debugging: See what the system hears")
        print("🔒 Strict mode: Only '시작해' or '시작하' will trigger")
        print("🛑 Press Ctrl+C to stop all nodes")
        print("="*80 + "\n")
    
    def check_environment(self):
        """
        Check if the environment is properly set up.
        """
        print("🔍 Checking environment...")
        
        # Check if .env file exists
        env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
        if not os.path.exists(env_path):
            print("❌ .env file not found")
            print("   Please create .env file with your OpenAI API key")
            return False
            
        # Check if API key is set
        with open(env_path, 'r') as f:
            content = f.read()
            if 'your_openai_api_key_here' in content:
                print("⚠️  Warning: OpenAI API key appears to be placeholder")
                print("   Please set your actual API key in .env file")
                
        print("✅ Environment check completed")
        return True
    
    def launch_nodes(self):
        """
        Launch both nodes using MultiThreadedExecutor.
        """
        try:
            # Initialize ROS2
            rclpy.init()
            
            # Create both nodes
            print("🎤 Creating speech-to-text node...")
            self.speech_node = SpeechToTextNode()
            
            print("🎯 Creating test signal node...")
            self.test_node = StartSignalTestNode()
            
            # Create multi-threaded executor
            self.executor = MultiThreadedExecutor()
            self.executor.add_node(self.speech_node)
            self.executor.add_node(self.test_node)
            
            print("✅ Both nodes created successfully")
            print("\n🎙️  Ready to process Korean speech!")
            print("📢 Say '시작해' clearly into your microphone\n")
            
            # Spin the executor
            while rclpy.ok() and not self.shutdown_requested:
                try:
                    self.executor.spin_once(timeout_sec=1.0)
                except KeyboardInterrupt:
                    break
                    
        except Exception as e:
            print(f"❌ Error during node execution: {str(e)}")
            
        finally:
            self.cleanup()
    
    def cleanup(self):
        """
        Clean up nodes and shutdown ROS2.
        """
        print("\n🧹 Cleaning up nodes...")
        
        try:
            if self.speech_node:
                # Get final statistics
                stats = self.speech_node.get_node_statistics()
                print(f"📊 Speech Node Statistics:")
                print(f"   - Audio chunks processed: {stats['chunk_count']}")
                print(f"   - Audio failures: {stats['consecutive_audio_failures']}")
                print(f"   - API failures: {stats['consecutive_api_failures']}")
                
                self.speech_node.cleanup_temp_files()
                self.speech_node.destroy_node()
                
            if self.test_node:
                # Get test statistics
                test_stats = self.test_node.get_statistics()
                print(f"📊 Test Node Statistics:")
                print(f"   - Start signals received: {test_stats['total_signals_received']}")
                
                self.test_node.destroy_node()
                
            if self.executor:
                self.executor.shutdown()
                
        except Exception as e:
            print(f"⚠️  Error during cleanup: {str(e)}")
            
        finally:
            try:
                rclpy.shutdown()
                print("✅ ROS2 shutdown complete")
            except Exception as e:
                print(f"⚠️  Error during ROS2 shutdown: {str(e)}")
                
        print("👋 Speech Test Launcher terminated\n")


def main(args=None):
    """
    Main function for the speech test launcher.
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Korean Speech-to-Text Test Launcher')
    parser.add_argument('--check-only', action='store_true',
                       help='Only check environment, do not start nodes')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose output')
    
    parsed_args = parser.parse_args(args)
    
    # Create launcher instance
    launcher = SpeechTestLauncher()
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, launcher.signal_handler)
    signal.signal(signal.SIGTERM, launcher.signal_handler)
    
    try:
        # Print banner
        launcher.print_banner()
        
        # Check environment
        if not launcher.check_environment():
            print("❌ Environment check failed. Please fix the issues above.")
            sys.exit(1)
            
        # If check-only mode, exit here
        if parsed_args.check_only:
            print("✅ Environment check passed. Ready to launch!")
            sys.exit(0)
            
        # Launch nodes
        launcher.launch_nodes()
        
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        sys.exit(1)


# Entry point when script is run directly
if __name__ == '__main__':
    main()