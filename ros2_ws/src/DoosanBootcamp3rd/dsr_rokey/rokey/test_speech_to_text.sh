#!/bin/bash

# Test script for speech-to-text functionality
# This script helps test the complete speech-to-text pipeline

echo "=========================================="
echo "🎤 Speech-to-Text Test Script"
echo "=========================================="

# Check if we're in the right directory
if [ ! -f "setup.py" ]; then
    echo "❌ Error: Please run this script from the package root directory"
    echo "   Expected location: /home/jack/ros2_ws/src/DoosanBootcamp3rd/dsr_rokey/rokey/"
    exit 1
fi

# Check if .env file exists and has API key
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found"
    echo "   Please create .env file with your OpenAI API key"
    exit 1
fi

# Check if API key is set
if grep -q "your_openai_api_key_here" .env; then
    echo "⚠️  Warning: Please set your actual OpenAI API key in .env file"
    echo "   Current key appears to be the placeholder"
fi

echo ""
echo "📋 Test Instructions:"
echo "1. Make sure your microphone is connected and working"
echo "2. The speech-to-text node will capture audio every 3 seconds"
echo "3. Say '시작해' clearly into the microphone"
echo "4. Watch for 'START RECEIVED' message in the test node output"
echo "5. Press Ctrl+C to stop both nodes"
echo ""
echo "🔍 Debugging Features:"
echo "- Real-time speech recognition display: See what the system hears"
echo "- Detailed analysis for each attempt: Why it triggered or didn't"
echo "- Strict mode enabled: Only '시작해' or '시작하' will trigger"
echo ""

# Build the package first
echo "🔨 Building package..."
cd /home/jack/ros2_ws
colcon build --packages-select rokey
source install/setup.bash

echo ""
echo "🚀 Starting both nodes..."
echo "   - speech_to_text: Captures audio and detects '시작해'"
echo "   - start_signal_test: Listens for start signals"
echo ""

# Start both nodes in the background and foreground
echo "Starting test subscriber node..."
ros2 run rokey start_signal_test &
TEST_NODE_PID=$!

sleep 2

echo ""
echo "Starting speech-to-text node..."
echo "Say '시작해' to test trigger detection!"
echo ""

# Start the main node in foreground
ros2 run rokey speech_to_text

# Clean up background process when main node exits
echo ""
echo "🛑 Stopping test node..."
kill $TEST_NODE_PID 2>/dev/null

echo "✅ Test completed"