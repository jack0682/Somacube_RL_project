#!/bin/bash

# ROKEY Speech-to-Text Package Installation Script
# This script installs the package and makes it available as system commands

echo "=================================================================="
echo "🎤 ROKEY Korean Speech-to-Text Package Installer"
echo "=================================================================="

# Check if we're in the right directory
if [ ! -f "setup.py" ]; then
    echo "❌ Error: Please run this script from the package root directory"
    echo "   Expected location: /home/jack/ros2_ws/src/DoosanBootcamp3rd/dsr_rokey/rokey/"
    exit 1
fi

# Check Python version
python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "🐍 Python version: $python_version"

if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
    echo "❌ Error: Python 3.8 or higher is required"
    exit 1
fi

echo "✅ Python version check passed"

# Check if virtual environment is recommended
echo ""
echo "💡 Installation Options:"
echo "1. Install globally (requires sudo, affects system Python)"
echo "2. Install in virtual environment (recommended)"
echo "3. Install in development mode (for developers)"
echo ""

read -p "Choose installation type (1/2/3): " choice

case $choice in
    1)
        echo "🔧 Installing globally..."
        sudo pip3 install -e .
        ;;
    2)
        echo "🔧 Setting up virtual environment..."
        python3 -m venv venv
        source venv/bin/activate
        echo "📦 Installing dependencies..."
        pip install -e .
        echo ""
        echo "✅ Installation complete!"
        echo "🔧 To use the package, activate the virtual environment first:"
        echo "   source $(pwd)/venv/bin/activate"
        ;;
    3)
        echo "🔧 Installing in development mode..."
        pip3 install -e .
        ;;
    *)
        echo "❌ Invalid choice. Exiting."
        exit 1
        ;;
esac

echo ""
echo "🎉 Package installation completed!"
echo ""
echo "📋 Available Commands:"
echo "   rokey-speech         - Start Korean speech-to-text node"
echo "   rokey-test          - Start signal test subscriber"
echo "   rokey-speech-test   - Launch both nodes for testing"
echo ""
echo "🔧 Usage Examples:"
echo "   rokey-speech-test                    # Launch full test environment"
echo "   rokey-speech-test --check-only       # Check environment only"
echo "   rokey-speech                         # Run speech recognition only"
echo "   rokey-test                          # Run test subscriber only"
echo ""
echo "📚 For more information, see SPEECH_TO_TEXT_README.md"
echo ""

# Test if commands are available
echo "🧪 Testing installed commands..."
if command -v rokey-speech &> /dev/null; then
    echo "✅ rokey-speech command available"
else
    echo "⚠️  rokey-speech command not found in PATH"
    echo "   You may need to restart your terminal or update PATH"
fi

if command -v rokey-speech-test &> /dev/null; then
    echo "✅ rokey-speech-test command available"
else
    echo "⚠️  rokey-speech-test command not found in PATH"
fi

echo ""
echo "🎯 Quick Start:"
echo "   1. Set your OpenAI API key in .env file"
echo "   2. Run: rokey-speech-test"
echo "   3. Say '시작해' into your microphone"
echo ""
echo "🎉 Ready to use Korean Speech-to-Text! 🇰🇷"