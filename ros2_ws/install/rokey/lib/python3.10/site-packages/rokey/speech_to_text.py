#!/usr/bin/env python3

# Import ROS2 Python client library for creating nodes
import rclpy
# Import the base Node class for creating ROS2 nodes
from rclpy.node import Node
# Import QoS for reliable message delivery configuration
from rclpy.qos import QoSProfile, ReliabilityPolicy
# Import String message type for publishing text messages
from std_msgs.msg import String
# Import Int32 message type for publishing start signal
from std_msgs.msg import Int32
# Import sounddevice for audio capture from microphone
import sounddevice as sd
# Import numpy for audio data processing
import numpy as np
# Import scipy.io.wavfile for saving audio files
from scipy.io.wavfile import write
# Import os for file operations
import os
# Import tempfile for creating temporary audio files
import tempfile
# Import OpenAI client for Whisper API integration
from openai import OpenAI
# Import dotenv for loading environment variables from .env file
from dotenv import load_dotenv
# Import time for retry delays and timing operations
import time
# Import logging for more detailed error tracking
import logging
# Import signal for handling Ctrl+C gracefully
import signal
# Import sys for system-related operations
import sys
# Import gc for garbage collection optimization
import gc
# Import TTS feedback system
from rokey.tts_feedback import TTSFeedback


class SpeechToTextNode(Node):
    """
    ROS2 node that handles speech-to-text functionality.
    Stage 7: Optimized and refactored with robust error handling and clean shutdown.
    
    Features:
    - Real-time audio capture (16kHz, mono, PCM 16-bit)
    - OpenAI Whisper API integration for Korean transcription
    - Korean trigger phrase detection ("시작해")
    - Reliable start signal publishing (Int32, value=1)
    - Comprehensive error handling and recovery
    - Memory optimization and clean shutdown
    """

    def __init__(self):
        # Initialize the parent Node class with node name 'speech_to_text_node'
        super().__init__('speech_to_text_node')
        
        # Load environment variables from .env file in package root
        # Get the directory containing this script
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Navigate to package root (one level up from rokey/rokey/)
        package_root = os.path.dirname(current_dir)
        # Load .env file from package root
        env_path = os.path.join(package_root, '.env')
        load_dotenv(env_path)
        
        # Initialize OpenAI client with API key from environment
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key or api_key == 'your_openai_api_key_here':
            self.get_logger().error('OpenAI API key not found or not set in .env file')
            self.openai_client = None
        else:
            # Create OpenAI client instance for API calls
            self.openai_client = OpenAI(api_key=api_key)
            self.get_logger().info('OpenAI client initialized successfully')
        
        # Create a publisher for String messages on '/speech_text' topic
        # QoS: queue size of 10 for message buffering
        self.publisher_ = self.create_publisher(String, '/speech_text', 10)
        
        # Create QoS profile for start signal with Reliable delivery and depth=10
        start_signal_qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,  # Reliable delivery as required
            depth=10                                # Queue depth of 10 as required
        )
        
        # Create a publisher for Int32 messages on '/start_signal' topic
        # This will publish value=1 when Korean phrase "시작해" is detected
        self.start_signal_publisher = self.create_publisher(
            Int32, 
            '/start_signal', 
            start_signal_qos
        )
        
        # Audio configuration constants as per requirements
        self.sample_rate = 16000  # 16kHz sampling rate for Whisper compatibility
        self.channels = 1  # Mono audio recording
        self.chunk_duration = 3.0  # 3-second audio chunks
        self.dtype = np.int16  # PCM 16-bit audio format
        
        # Korean trigger phrase for start signal detection
        self.trigger_phrase = "시작해"  # Korean phrase meaning "start"
        
        # Strict detection mode to reduce false positives
        self.strict_detection = True    # Enable strict matching rules
        self.min_confidence_length = 2  # Minimum characters for confidence
        self.max_words_allowed = 2      # Maximum words in valid transcription
        
        # Error tracking and recovery variables
        self.consecutive_audio_failures = 0  # Track consecutive audio capture failures
        self.consecutive_api_failures = 0    # Track consecutive API call failures
        self.max_consecutive_failures = 5    # Maximum failures before taking action
        self.retry_delay = 1.0               # Delay between retries (seconds)
        self.audio_device_available = True   # Track audio device availability
        self.api_available = True            # Track API availability
        
        # Performance optimization and shutdown variables
        self.shutdown_requested = False      # Flag for clean shutdown handling
        self.cleanup_interval = 50           # Clean up temp files every N chunks
        self.last_gc_time = time.time()      # Last garbage collection time
        self.gc_interval = 30.0              # Garbage collection interval (seconds)
        self.max_temp_files = 10             # Maximum temporary files to keep
        
        # Initialize TTS feedback system
        self.tts = TTSFeedback(logger=self.get_logger())
        self.tts_enabled = True              # Enable TTS feedback by default
        self.tts_language = "auto"           # Auto-detect language ("ko", "en", "auto")
        
        # Calculate the number of samples per chunk
        self.samples_per_chunk = int(self.sample_rate * self.chunk_duration)
        
        # Initialize a counter to track processed audio chunks
        self.chunk_count = 0
        
        # Create temporary directory for storing audio files
        self.temp_dir = tempfile.mkdtemp(prefix='speech_audio_')
        
        # Validate audio device availability at startup
        self.validate_audio_device()
        
        # Create a timer that calls audio_capture_callback every 3.0 seconds
        # This triggers the audio capture and processing pipeline
        self.timer = self.create_timer(self.chunk_duration, self.audio_capture_callback)
        
        # Log node initialization with audio parameters
        self.get_logger().info('🎤 Speech-to-Text Node initialized - Stage 7: Optimized & Robust')
        self.get_logger().info(f'📊 Audio config: {self.sample_rate}Hz, {self.channels} channel(s), {self.chunk_duration}s chunks')
        self.get_logger().info(f'🎯 Trigger phrase: "{self.trigger_phrase}"')
        self.get_logger().info(f'🔒 Detection mode: {"STRICT (reduced false positives)" if self.strict_detection else "NORMAL"}')
        self.get_logger().info(f'📡 Start signal topic: /start_signal (Int32, QoS: Reliable, depth=10)')
        self.get_logger().info(f'🛡️  Error handling: max {self.max_consecutive_failures} consecutive failures')
        self.get_logger().info(f'🗂️  Temp directory: {self.temp_dir}')
        self.get_logger().info(f'⚙️  Environment file: {env_path}')
        self.get_logger().info(f'🎧 Audio device available: {self.audio_device_available}')
        self.get_logger().info(f'🤖 API available: {self.api_available}')
        self.get_logger().info(f'♻️  Memory optimization: GC every {self.gc_interval}s, max {self.max_temp_files} temp files')
        
        # Log TTS status
        tts_status = self.tts.get_status()
        self.get_logger().info(f'🔊 TTS Feedback: {"enabled" if self.tts_enabled else "disabled"}')
        self.get_logger().info(f'🌐 TTS Language: {self.tts_language}')
        self.get_logger().info(f'🎵 TTS Engines: pyttsx3={tts_status["pyttsx3_available"]}, gTTS={tts_status["gtts_available"]}')
        
        self.get_logger().warn('✅ Node ready - Say "시작해" clearly and alone to trigger start signal!')
        if self.strict_detection:
            self.get_logger().warn('🔒 STRICT MODE: Only exact "시작해" or "시작하" will trigger (reduces false positives)')
            
        # Announce system ready with TTS
        if self.tts_enabled:
            self.tts.speak_system_ready(self.tts_language)

    def audio_capture_callback(self):
        """
        Callback function executed every 3 seconds by the timer.
        Captures audio with comprehensive error handling, memory optimization, and clean shutdown.
        """
        # Check if shutdown has been requested
        if self.shutdown_requested:
            self.get_logger().info('🛑 Shutdown requested - stopping audio capture')
            return
            
        # Skip if audio device is not available
        if not self.audio_device_available:
            self.get_logger().warn(f'⏭️  Skipping audio capture #{self.chunk_count + 1} - audio device unavailable')
            return
            
        # Perform memory optimization if needed
        self.optimize_memory_usage()
            
        try:
            # Increment the chunk counter
            self.chunk_count += 1
            
            # Visual feedback for audio capture start
            print(f"\n🎙️  [#{self.chunk_count:03d}] 3초간 음성 캡처 중... (명확히 말하세요)")
            
            # Log start of audio capture
            self.get_logger().debug(f'Starting audio capture #{self.chunk_count}...')
            
            # Attempt audio capture with error handling
            audio_filename = self.capture_audio_with_retry()
            
            if not audio_filename:
                # Audio capture failed after retries
                self.handle_audio_failure()
                return
                
            # Reset consecutive audio failure counter on success
            self.consecutive_audio_failures = 0
            self.audio_device_available = True
            
            # Attempt transcription with error handling
            transcription = self.transcribe_audio_with_retry(audio_filename)
            
            # Create and publish the transcription result
            msg = String()
            if transcription:
                # Successfully transcribed audio - always show what was heard
                print(f"\n🎤 [음성인식 #{self.chunk_count:03d}] 들린 말: '{transcription}'")
                
                msg.data = f'Transcription #{self.chunk_count}: "{transcription}"'
                self.get_logger().info(f'📝 Transcribed: "{transcription}"')
                
                # Reset consecutive API failure counter on success
                self.consecutive_api_failures = 0
                self.api_available = True
                
                # Check if transcription contains the Korean trigger phrase
                trigger_detected = self.detect_trigger_phrase(transcription)
                if trigger_detected:
                    # Publish start signal when trigger phrase is detected
                    print(f"🚀 >>> 트리거 발생! '{transcription}' -> START SIGNAL 전송 <<<")
                    self.publish_start_signal()
                    
                    # Provide TTS feedback for successful trigger detection
                    if self.tts_enabled:
                        self.tts.speak_trigger_detected(self.tts_language)
                else:
                    # Show why it wasn't triggered for debugging
                    print(f"❌ 트리거 아님: '{transcription}' (정확히 '시작해'만 인식됨)")
                    
            else:
                # Transcription failed after retries
                print(f"\n🔇 [음성인식 #{self.chunk_count:03d}] 인식 실패 - API 문제")
                msg.data = f'Transcription failed for chunk #{self.chunk_count} (API issues)'
                self.handle_api_failure()
                
                # Provide TTS feedback for API errors (less frequent)
                if self.tts_enabled and self.chunk_count % 5 == 0:  # Only every 5th failure
                    self.tts.speak_error("api", self.tts_language)
                
            # Publish the transcription message
            self.publisher_.publish(msg)
            
        except Exception as e:
            # Handle unexpected errors
            self.get_logger().error(f'Unexpected error in audio processing: {str(e)}')
            self.handle_audio_failure()
            
            # Publish error message
            msg = String()
            msg.data = f'Unexpected error #{self.chunk_count}: {str(e)}'
            self.publisher_.publish(msg)

    def validate_audio_device(self):
        """
        Validate audio device availability at startup.
        """
        try:
            # Query available audio devices
            devices = sd.query_devices()
            self.get_logger().info(f'Found {len(devices)} audio devices')
            
            # Try to get default input device
            default_device = sd.default.device[0]
            device_info = sd.query_devices(default_device, 'input')
            
            self.get_logger().info(f'Default input device: {device_info["name"]}')
            self.audio_device_available = True
            
        except Exception as e:
            # Audio device validation failed
            self.get_logger().error(f'Audio device validation failed: {str(e)}')
            self.audio_device_available = False

    def capture_audio_with_retry(self):
        """
        Capture audio with retry logic for error recovery.
        
        Returns:
            str: Path to captured audio file, or None if failed
        """
        for attempt in range(3):  # Try up to 3 times
            try:
                # Capture audio from default microphone
                audio_data = sd.rec(
                    frames=self.samples_per_chunk,  # Number of frames to record
                    samplerate=self.sample_rate,    # Sampling rate (16kHz)
                    channels=self.channels,         # Number of channels (mono)
                    dtype=self.dtype               # Data type (16-bit PCM)
                )
                
                # Wait for the recording to complete
                sd.wait()
                
                # Create filename for the temporary audio file
                audio_filename = os.path.join(self.temp_dir, f'audio_chunk_{self.chunk_count:04d}.wav')
                
                # Save the recorded audio data to WAV file
                write(audio_filename, self.sample_rate, audio_data)
                
                # Validate file was created and has reasonable size
                if os.path.exists(audio_filename):
                    file_size = os.path.getsize(audio_filename)
                    if file_size > 1000:  # At least 1KB for valid audio
                        self.get_logger().info(f'Audio captured: {audio_filename} ({file_size} bytes)')
                        return audio_filename
                    else:
                        self.get_logger().warn(f'Audio file too small: {file_size} bytes')
                        
            except sd.PortAudioError as e:
                # Audio device specific errors
                self.get_logger().error(f'Audio device error (attempt {attempt + 1}/3): {str(e)}')
                if attempt < 2:  # Don't sleep on last attempt
                    time.sleep(self.retry_delay)
                    
            except Exception as e:
                # Other audio capture errors
                self.get_logger().error(f'Audio capture error (attempt {attempt + 1}/3): {str(e)}')
                if attempt < 2:  # Don't sleep on last attempt
                    time.sleep(self.retry_delay)
                    
        # All attempts failed
        self.get_logger().error('Audio capture failed after 3 attempts')
        return None

    def transcribe_audio_with_retry(self, audio_file_path):
        """
        Transcribe audio with retry logic for API error recovery.
        
        Args:
            audio_file_path (str): Path to the audio file to transcribe
            
        Returns:
            str: Transcribed text, or None if failed
        """
        # Skip if API is not available
        if not self.api_available:
            self.get_logger().warn('Skipping transcription - API unavailable')
            return None
            
        for attempt in range(3):  # Try up to 3 times
            try:
                transcription = self.transcribe_audio(audio_file_path)
                if transcription:
                    return transcription
                    
            except Exception as e:
                # API call failed
                self.get_logger().error(f'API transcription error (attempt {attempt + 1}/3): {str(e)}')
                if attempt < 2:  # Don't sleep on last attempt
                    time.sleep(self.retry_delay * (attempt + 1))  # Exponential backoff
                    
        # All attempts failed
        self.get_logger().error('Transcription failed after 3 attempts')
        return None

    def handle_audio_failure(self):
        """
        Handle consecutive audio failures and take appropriate action.
        """
        self.consecutive_audio_failures += 1
        self.get_logger().warn(f'Audio failure #{self.consecutive_audio_failures}/{self.max_consecutive_failures}')
        
        if self.consecutive_audio_failures >= self.max_consecutive_failures:
            # Too many consecutive failures - mark audio device as unavailable
            self.audio_device_available = False
            self.get_logger().error(f'Audio device marked unavailable after {self.max_consecutive_failures} failures')
            
            # Provide TTS feedback for audio device failure
            if self.tts_enabled:
                self.tts.speak_error("audio", self.tts_language)
            
            # Try to re-validate audio device after a delay
            self.create_timer(30.0, self.retry_audio_device_validation)

    def handle_api_failure(self):
        """
        Handle consecutive API failures and take appropriate action.
        """
        self.consecutive_api_failures += 1
        self.get_logger().warn(f'API failure #{self.consecutive_api_failures}/{self.max_consecutive_failures}')
        
        if self.consecutive_api_failures >= self.max_consecutive_failures:
            # Too many consecutive failures - mark API as unavailable
            self.api_available = False
            self.get_logger().error(f'API marked unavailable after {self.max_consecutive_failures} failures')
            
            # Try to re-validate API after a delay
            self.create_timer(60.0, self.retry_api_validation)

    def retry_audio_device_validation(self):
        """
        Retry audio device validation after failures.
        """
        self.get_logger().info('Retrying audio device validation...')
        self.validate_audio_device()
        if self.audio_device_available:
            self.consecutive_audio_failures = 0
            self.get_logger().info('Audio device recovered successfully')

    def retry_api_validation(self):
        """
        Retry API validation after failures.
        """
        self.get_logger().info('Retrying API validation...')
        if self.openai_client:
            self.api_available = True
            self.consecutive_api_failures = 0
            self.get_logger().info('API recovered successfully')

    def optimize_memory_usage(self):
        """
        Optimize memory usage by cleaning up old files and running garbage collection.
        Called during each audio capture cycle for proactive memory management.
        """
        current_time = time.time()
        
        # Perform garbage collection if interval has passed
        if current_time - self.last_gc_time > self.gc_interval:
            # Explicitly run garbage collection to free memory
            gc.collect()
            self.last_gc_time = current_time
            self.get_logger().debug('♻️  Garbage collection performed')
        
        # Clean up old temporary files if we have too many
        if self.chunk_count % self.cleanup_interval == 0:
            self.cleanup_old_temp_files()

    def cleanup_old_temp_files(self):
        """
        Clean up old temporary audio files to prevent disk space issues.
        Keeps only the most recent files up to max_temp_files limit.
        """
        try:
            # Get list of all audio files in temp directory
            if not os.path.exists(self.temp_dir):
                return
                
            # Find all audio chunk files
            audio_files = []
            for filename in os.listdir(self.temp_dir):
                if filename.startswith('audio_chunk_') and filename.endswith('.wav'):
                    filepath = os.path.join(self.temp_dir, filename)
                    # Get file modification time
                    mtime = os.path.getmtime(filepath)
                    audio_files.append((mtime, filepath))
            
            # Sort by modification time (newest first)
            audio_files.sort(reverse=True)
            
            # Remove old files if we have more than max_temp_files
            files_to_delete = audio_files[self.max_temp_files:]
            
            for _, filepath in files_to_delete:
                try:
                    os.remove(filepath)
                    self.get_logger().debug(f'🗑️  Removed old temp file: {os.path.basename(filepath)}')
                except OSError as e:
                    self.get_logger().warn(f'Failed to remove temp file {filepath}: {str(e)}')
                    
            if files_to_delete:
                self.get_logger().info(f'♻️  Cleaned up {len(files_to_delete)} old temp files')
                
        except Exception as e:
            self.get_logger().error(f'Error during temp file cleanup: {str(e)}')

    def request_shutdown(self):
        """
        Request clean shutdown of the node.
        Sets shutdown flag and stops audio capture gracefully.
        """
        self.get_logger().info('🛑 Shutdown requested - preparing for clean exit')
        self.shutdown_requested = True
        
        # Cancel the timer to stop new audio captures
        if hasattr(self, 'timer'):
            self.timer.cancel()
            self.get_logger().info('⏹️  Audio capture timer stopped')

    def get_node_statistics(self):
        """
        Get comprehensive statistics about node performance and status.
        
        Returns:
            dict: Dictionary containing node statistics
        """
        stats = {
            'chunk_count': self.chunk_count,
            'consecutive_audio_failures': self.consecutive_audio_failures,
            'consecutive_api_failures': self.consecutive_api_failures,
            'audio_device_available': self.audio_device_available,
            'api_available': self.api_available,
            'temp_directory': self.temp_dir,
            'trigger_phrase': self.trigger_phrase,
            'shutdown_requested': self.shutdown_requested,
            'sample_rate': self.sample_rate,
            'chunk_duration': self.chunk_duration,
            'tts_enabled': self.tts_enabled,
            'tts_language': self.tts_language
        }
        
        # Add TTS status if available
        if hasattr(self, 'tts') and self.tts:
            stats['tts_status'] = self.tts.get_status()
            
        return stats

    def transcribe_audio(self, audio_file_path):
        """
        Transcribe audio file using OpenAI Whisper API with enhanced error handling.
        
        Args:
            audio_file_path (str): Path to the audio file to transcribe
            
        Returns:
            str: Transcribed text, or None if transcription fails
        """
        # Check if OpenAI client is available
        if not self.openai_client:
            self.get_logger().warn('OpenAI client not available - skipping transcription')
            return None
            
        # Validate audio file exists and has reasonable size
        if not os.path.exists(audio_file_path):
            self.get_logger().error(f'Audio file not found: {audio_file_path}')
            return None
            
        file_size = os.path.getsize(audio_file_path)
        if file_size < 1000:  # Less than 1KB
            self.get_logger().warn(f'Audio file too small for transcription: {file_size} bytes')
            return None
            
        try:
            # Open the audio file for reading
            with open(audio_file_path, 'rb') as audio_file:
                # Call OpenAI Whisper API to transcribe the audio with improved settings
                response = self.openai_client.audio.transcriptions.create(
                    model="whisper-1",      # OpenAI Whisper model
                    file=audio_file,        # Audio file to transcribe
                    language="ko",          # Korean language for better accuracy
                    prompt="시작해, 시작하, 시작해요",  # Hint for expected phrases
                    temperature=0.0         # Lower temperature for more consistent results
                )
                
                # Extract transcribed text from response
                transcription = response.text.strip()
                
                # Validate transcription is not empty
                if not transcription:
                    self.get_logger().warn('Empty transcription received from API')
                    return None
                
                # Log successful transcription (first 100 chars for readability)
                preview = transcription[:100] + "..." if len(transcription) > 100 else transcription
                self.get_logger().debug(f'Whisper API response: "{preview}"')
                
                return transcription
                
        except FileNotFoundError:
            # Audio file was deleted or moved
            self.get_logger().error(f'Audio file disappeared: {audio_file_path}')
            return None
            
        except PermissionError:
            # File permission issues
            self.get_logger().error(f'Permission denied accessing audio file: {audio_file_path}')
            return None
            
        except Exception as e:
            # Check if it's an API-specific error
            error_str = str(e).lower()
            if 'api' in error_str or 'openai' in error_str or 'rate limit' in error_str:
                self.get_logger().error(f'OpenAI API error: {str(e)}')
            elif 'network' in error_str or 'connection' in error_str:
                self.get_logger().error(f'Network error during transcription: {str(e)}')
            else:
                self.get_logger().error(f'Unexpected transcription error: {str(e)}')
            return None

    def detect_trigger_phrase(self, transcription):
        """
        Detect if the Korean trigger phrase "시작해" is present in the transcription with improved accuracy.
        Uses multiple validation methods to reduce false positives.
        
        Args:
            transcription (str): The transcribed text to analyze
            
        Returns:
            bool: True if trigger phrase is detected, False otherwise
        """
        # Check if transcription text is valid
        if not transcription or not isinstance(transcription, str):
            return False
            
        # Clean the transcription text
        transcription_clean = transcription.strip()
        
        # Remove common punctuation and whitespace
        import re
        transcription_clean = re.sub(r'[.,!?;:\s]+', ' ', transcription_clean).strip()
        
        # Log the cleaned transcription for debugging
        self.get_logger().debug(f'Cleaned transcription: "{transcription_clean}"')
        
        # Multiple detection methods for better accuracy
        detection_methods = []
        
        # Method 1: Exact match (most strict)
        exact_match = transcription_clean == self.trigger_phrase
        detection_methods.append(("exact_match", exact_match))
        
        # Method 2: Word boundary match (prevents partial matches)
        word_boundary_match = False
        words = transcription_clean.split()
        for word in words:
            if word == self.trigger_phrase:
                word_boundary_match = True
                break
        detection_methods.append(("word_boundary", word_boundary_match))
        
        # Method 3: Similarity check for slight variations
        similarity_match = False
        if len(transcription_clean) <= 6:  # Only for short transcriptions
            # Check for common variations or mishearings
            variations = [
                "시작해",      # Exact target
                "시작하",      # Missing final syllable
                "시작해요",    # Polite form
                "시작합시다",  # More formal (but longer, should not match)
            ]
            
            for word in words:
                if word in variations[:3]:  # Only allow first 3 variations
                    similarity_match = True
                    break
        detection_methods.append(("similarity", similarity_match))
        
        # Method 4: Length validation (reject if too long or too short)
        length_valid = 2 <= len(transcription_clean) <= 8
        detection_methods.append(("length_valid", length_valid))
        
        # Log all detection method results
        for method_name, result in detection_methods:
            self.get_logger().debug(f'Detection method "{method_name}": {result}')
        
        # Final decision logic with strict validation
        trigger_found = False
        
        if self.strict_detection:
            # Strict mode: only accept very confident matches
            if exact_match:
                # Perfect exact match
                trigger_found = True
                self.get_logger().info(f'🎯 EXACT MATCH (STRICT): "{self.trigger_phrase}" == "{transcription_clean}"')
                
            elif word_boundary_match and length_valid and len(words) == 1:
                # Single word exact match only
                trigger_found = True
                self.get_logger().info(f'🎯 SINGLE WORD MATCH (STRICT): "{self.trigger_phrase}" as only word in "{transcription_clean}"')
                
            elif similarity_match and len(words) == 1 and len(transcription_clean) <= 4:
                # Only very short, single-word variations
                if transcription_clean in ["시작해", "시작하"]:  # Only allow these specific variations
                    trigger_found = True
                    self.get_logger().info(f'🎯 APPROVED VARIATION (STRICT): "{transcription_clean}" recognized as valid')
                else:
                    self.get_logger().debug(f'❌ REJECTED VARIATION (STRICT): "{transcription_clean}" not in approved list')
            else:
                # All other cases rejected in strict mode
                self.get_logger().debug(f'❌ STRICT MODE REJECTION: "{transcription_clean}" failed strict validation')
        else:
            # Original logic for non-strict mode
            if exact_match:
                trigger_found = True
                self.get_logger().info(f'🎯 EXACT MATCH: "{self.trigger_phrase}" == "{transcription_clean}"')
                
            elif word_boundary_match and length_valid and len(words) <= self.max_words_allowed:
                trigger_found = True
                self.get_logger().info(f'🎯 WORD BOUNDARY MATCH: "{self.trigger_phrase}" found as complete word in "{transcription_clean}"')
                
            elif similarity_match and length_valid and len(words) == 1:
                trigger_found = True
                self.get_logger().info(f'🎯 SIMILARITY MATCH: Recognized variation of "{self.trigger_phrase}" in "{transcription_clean}"')
        
        # Final validation: show detailed analysis for debugging
        if not trigger_found:
            # Provide detailed feedback for debugging
            analysis = f"분석 결과: "
            analysis += f"단어수={len(words)}, "
            analysis += f"길이={len(transcription_clean)}, "
            analysis += f"정확매칭={'O' if exact_match else 'X'}, "
            analysis += f"단어경계={'O' if word_boundary_match else 'X'}, "
            analysis += f"유사도={'O' if similarity_match else 'X'}, "
            analysis += f"길이검증={'O' if length_valid else 'X'}"
            
            print(f"   🔍 {analysis}")
            self.get_logger().debug(f'❌ NO TRIGGER: "{transcription_clean}" - {analysis}')
        
        return trigger_found

    def publish_start_signal(self):
        """
        Publish an Int32 message with value=1 to the /start_signal topic.
        Called when the Korean trigger phrase "시작해" is detected.
        """
        try:
            # Create Int32 message with value 1 as required
            start_msg = Int32()
            start_msg.data = 1
            
            # Publish the start signal message
            self.start_signal_publisher.publish(start_msg)
            
            # Log the successful start signal publication
            self.get_logger().warn(f'🚀 START SIGNAL PUBLISHED: value={start_msg.data} on topic /start_signal')
            
        except Exception as e:
            # Log any errors during start signal publishing
            self.get_logger().error(f'Failed to publish start signal: {str(e)}')

    def cleanup_temp_files(self):
        """
        Clean up temporary audio files and directory.
        Called when the node is being destroyed.
        """
        try:
            # Clean up TTS resources first
            if hasattr(self, 'tts') and self.tts:
                self.tts.cleanup()
            
            # Import shutil for directory removal
            import shutil
            
            # Remove the entire temporary directory and its contents
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                self.get_logger().info(f'Cleaned up temporary directory: {self.temp_dir}')
                
        except Exception as e:
            # Log cleanup errors but don't raise exceptions
            self.get_logger().error(f'Error cleaning up temp files: {str(e)}')


def signal_handler(signum, frame, node):
    """
    Signal handler for graceful shutdown on Ctrl+C or other signals.
    
    Args:
        signum: Signal number
        frame: Current stack frame
        node: SpeechToTextNode instance for cleanup
    """
    print(f"\n🛑 Received signal {signum} - initiating graceful shutdown...")
    
    # Request shutdown from the node
    if node:
        node.request_shutdown()
        
        # Print final statistics
        stats = node.get_node_statistics()
        print(f"📊 Final Statistics:")
        print(f"   - Audio chunks processed: {stats['chunk_count']}")
        print(f"   - Audio failures: {stats['consecutive_audio_failures']}")
        print(f"   - API failures: {stats['consecutive_api_failures']}")
        print(f"   - Audio device available: {stats['audio_device_available']}")
        print(f"   - API available: {stats['api_available']}")
        
    # Exit gracefully
    sys.exit(0)


def main(args=None):
    """
    Main function to initialize ROS2, create and spin the node with optimized shutdown handling.
    Includes signal handling for graceful shutdown and comprehensive error recovery.
    """
    # Initialize the ROS2 Python client library
    rclpy.init(args=args)
    
    # Create an instance of the SpeechToTextNode
    speech_to_text_node = None
    
    try:
        # Create the speech-to-text node instance
        speech_to_text_node = SpeechToTextNode()
        
        # Set up signal handlers for graceful shutdown
        # Handle Ctrl+C (SIGINT) and termination (SIGTERM)
        signal.signal(signal.SIGINT, lambda s, f: signal_handler(s, f, speech_to_text_node))
        signal.signal(signal.SIGTERM, lambda s, f: signal_handler(s, f, speech_to_text_node))
        
        # Print startup banner with debugging info
        print("\n" + "="*70)
        print("🎤 SPEECH-TO-TEXT NODE STARTED")
        print("✅ Ready to process Korean speech")
        print("🎯 Say '시작해' to trigger start signal")
        print("🔍 디버깅 모드: 모든 인식된 음성이 실시간으로 표시됩니다")
        print("📊 각 음성 캡처마다 상세한 분석 결과를 확인할 수 있습니다")
        if speech_to_text_node.strict_detection:
            print("🔒 엄격 모드: '시작해' 또는 '시작하'만 정확히 인식됩니다")
        if speech_to_text_node.tts_enabled:
            print("🔊 TTS 피드백: 트리거 감지 시 음성으로 알려드립니다")
        print("🛑 Press Ctrl+C for graceful shutdown")
        print("="*70 + "\n")
        
        # Keep the node running and processing callbacks
        # This will continue until shutdown is requested
        while rclpy.ok() and not speech_to_text_node.shutdown_requested:
            rclpy.spin_once(speech_to_text_node, timeout_sec=1.0)
            
    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        print("\n🛑 Keyboard interrupt received")
        if speech_to_text_node:
            speech_to_text_node.get_logger().info('Node stopped by user (Ctrl+C)')
            
    except Exception as e:
        # Handle unexpected errors
        print(f"\n❌ Unexpected error: {str(e)}")
        if speech_to_text_node:
            speech_to_text_node.get_logger().error(f'Unexpected error in main: {str(e)}')
            
    finally:
        print("\n🧹 Performing cleanup...")
        
        # Clean up temporary files and resources
        if speech_to_text_node:
            try:
                # Request shutdown if not already requested
                speech_to_text_node.request_shutdown()
                
                # Clean up temporary files
                speech_to_text_node.cleanup_temp_files()
                
                # Get final statistics
                stats = speech_to_text_node.get_node_statistics()
                print(f"📊 Session completed:")
                print(f"   - Total chunks processed: {stats['chunk_count']}")
                print(f"   - Temp directory cleaned: {stats['temp_directory']}")
                
                # Destroy the node
                speech_to_text_node.destroy_node()
                
            except Exception as e:
                print(f"⚠️  Error during cleanup: {str(e)}")
        
        # Shutdown ROS2
        try:
            rclpy.shutdown()
            print("✅ ROS2 shutdown complete")
        except Exception as e:
            print(f"⚠️  Error during ROS2 shutdown: {str(e)}")
        
        print("👋 Speech-to-Text node terminated\n")


# Entry point when script is run directly
if __name__ == '__main__':
    main()