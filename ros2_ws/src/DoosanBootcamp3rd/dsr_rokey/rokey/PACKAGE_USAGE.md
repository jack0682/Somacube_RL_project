# ROKEY Korean Speech-to-Text Package Usage Guide

## Quick Installation

```bash
cd /home/jack/ros2_ws/src/DoosanBootcamp3rd/dsr_rokey/rokey
./install_package.sh
```

Choose option 2 (virtual environment) for safe installation.

## Available Commands After Installation

### 🎤 Main Commands
- `rokey-speech` - Korean speech-to-text recognition node
- `rokey-test` - Start signal test subscriber  
- `rokey-speech-test` - Launch both nodes for complete testing

### 🔧 Quick Commands
```bash
# Check environment setup
rokey-speech-test --check-only

# Full test with debugging
rokey-speech-test

# Run speech recognition only
rokey-speech

# Run test subscriber only  
rokey-test
```

## Setup Steps

### 1. Set OpenAI API Key
Edit the `.env` file:
```bash
nano .env
```
Replace `your_openai_api_key_here` with your actual OpenAI API key.

### 2. Test Your Setup
```bash
rokey-speech-test --check-only
```

### 3. Run Full Test
```bash
rokey-speech-test
```

## What You'll See

### 🎙️ Audio Capture
```
🎙️  [#001] 3초간 음성 캡처 중... (명확히 말하세요)
```

### 🎤 Speech Recognition  
```
🎤 [음성인식 #001] 들린 말: '시작해'
🚀 >>> 트리거 발생! '시작해' -> START SIGNAL 전송 <<<
```

### 🔊 TTS Feedback
You'll hear voice announcements:
- **System start**: "음성 인식 시스템이 준비되었습니다" (Korean) or "Speech recognition system ready" (English)
- **Trigger detected**: "시작해가 인식되었습니다" (Korean) or "Start trigger detected" (English)

### ❌ Failed Attempts
```
🎤 [음성인식 #002] 들린 말: '시각해'  
❌ 트리거 아님: '시각해' (정확히 '시작해'만 인식됨)
   🔍 분석 결과: 단어수=1, 길이=3, 정확매칭=X, 단어경계=X, 유사도=X, 길이검증=O
```

### 🎯 Test Node Confirmation
```
🚀 START RECEIVED (#1) at 2024-XX-XX XX:XX:XX.XXX 🚀
```

## Trigger Words

### ✅ Accepted
- "시작해" (exact match)
- "시작하" (approved variation)

### ❌ Rejected  
- "시작해요" (too long)
- "그냥 시작해" (multiple words)
- "시각해" (different word)
- Any other variations

## Troubleshooting

### Command Not Found
If commands like `rokey-speech` are not found:
```bash
# Restart terminal or re-source your shell
source ~/.bashrc

# Or activate virtual environment if you used option 2
source venv/bin/activate
```

### API Key Issues
```bash
# Check your .env file
cat .env

# Make sure the key starts with 'sk-'
# and doesn't contain 'your_openai_api_key_here'
```

### Audio Issues
```bash
# Test your microphone
python3 -c "import sounddevice; print(sounddevice.query_devices())"

# Check if the default input device is correct
```

## Development Mode

If you want to modify the code:
```bash
# Install in development mode  
./install_package.sh
# Choose option 3

# Your changes will be reflected immediately
# without reinstalling
```

## Integration with ROS2

The package is fully compatible with ROS2:
```bash
# Use ROS2 commands directly
ros2 run rokey speech_to_text
ros2 run rokey start_signal_test

# Monitor topics
ros2 topic echo /start_signal
ros2 topic echo /speech_text

# Check node info
ros2 node info /speech_to_text_node
```

## System Requirements

- **Python**: 3.8 or higher
- **ROS2**: Humble or compatible
- **OpenAI API**: Valid API key
- **Microphone**: Working audio input device
- **Internet**: For Whisper API calls

## Package Features

- 🎤 Real-time Korean speech recognition
- 🎯 Precise "시작해" trigger detection  
- 🔊 **TTS voice feedback** in Korean and English
- 🔍 Comprehensive debugging output
- 🛡️ Robust error handling and recovery
- 📊 Performance monitoring and statistics
- 🔒 Strict mode to prevent false positives
- ♻️ Memory optimization and cleanup
- 🚀 Easy installation and usage
- 🌐 Multi-language TTS support (gTTS + pyttsx3)