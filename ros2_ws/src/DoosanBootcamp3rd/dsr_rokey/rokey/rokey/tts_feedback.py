#!/usr/bin/env python3

# Text-to-Speech Feedback Module for Korean Speech-to-Text System
# Provides audio feedback when triggers are detected

# Import system modules
import os
import tempfile
import threading
import time
from typing import Optional, Dict, Any

# Import TTS libraries
try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False

try:
    from gtts import gTTS
    import pygame
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False


class TTSFeedback:
    """
    Text-to-Speech feedback system for speech recognition events.
    Supports both Korean and English with multiple TTS engines.
    """
    
    def __init__(self, logger=None):
        # Store logger for debugging
        self.logger = logger
        
        # TTS configuration
        self.tts_enabled = True
        self.language = "auto"  # "ko", "en", or "auto"
        self.engine_preference = "pyttsx3"  # "pyttsx3" or "gtts"
        self.volume = 0.8
        
        # Initialize TTS engines
        self.pyttsx3_engine = None
        self.pygame_initialized = False
        
        # Thread safety
        self.tts_lock = threading.Lock()
        self.temp_dir = tempfile.mkdtemp(prefix='tts_audio_')
        
        # Initialize engines
        self._initialize_engines()
        
        # Predefined messages
        self.messages = {
            "trigger_detected_ko": "시작해가 인식되었습니다",
            "trigger_detected_en": "Start trigger detected",
            "system_ready_ko": "음성 인식 시스템이 준비되었습니다",
            "system_ready_en": "Speech recognition system ready",
            "api_error_ko": "음성 인식 오류가 발생했습니다",
            "api_error_en": "Speech recognition error occurred",
            "audio_error_ko": "마이크 오류가 발생했습니다",
            "audio_error_en": "Microphone error occurred"
        }
        
        if self.logger:
            self.logger.info(f"🔊 TTS Feedback initialized:")
            self.logger.info(f"   - pyttsx3 available: {PYTTSX3_AVAILABLE}")
            self.logger.info(f"   - gTTS available: {GTTS_AVAILABLE}")
            self.logger.info(f"   - Preferred engine: {self.engine_preference}")
            self.logger.info(f"   - Language mode: {self.language}")
    
    def _initialize_engines(self):
        """
        Initialize available TTS engines.
        """
        # Initialize pyttsx3 (offline TTS)
        if PYTTSX3_AVAILABLE:
            try:
                self.pyttsx3_engine = pyttsx3.init()
                # Configure pyttsx3 settings
                self.pyttsx3_engine.setProperty('rate', 150)  # Speech rate
                self.pyttsx3_engine.setProperty('volume', self.volume)
                
                # Try to set Korean voice if available
                voices = self.pyttsx3_engine.getProperty('voices')
                for voice in voices:
                    if 'korean' in voice.name.lower() or 'ko' in voice.id.lower():
                        self.pyttsx3_engine.setProperty('voice', voice.id)
                        break
                
                if self.logger:
                    self.logger.debug("✅ pyttsx3 engine initialized")
                    
            except Exception as e:
                if self.logger:
                    self.logger.error(f"❌ Failed to initialize pyttsx3: {str(e)}")
                self.pyttsx3_engine = None
        
        # Initialize pygame for gTTS playback
        if GTTS_AVAILABLE:
            try:
                pygame.mixer.init()
                self.pygame_initialized = True
                if self.logger:
                    self.logger.debug("✅ pygame mixer initialized for gTTS")
            except Exception as e:
                if self.logger:
                    self.logger.error(f"❌ Failed to initialize pygame: {str(e)}")
                self.pygame_initialized = False
    
    def _detect_language(self, text: str) -> str:
        """
        Detect if text is Korean or English.
        
        Args:
            text (str): Text to analyze
            
        Returns:
            str: "ko" for Korean, "en" for English
        """
        # Count Korean characters (Hangul)
        korean_chars = 0
        total_chars = 0
        
        for char in text:
            if char.isalpha():
                total_chars += 1
                # Korean Unicode ranges: 가-힣 (syllables), ㄱ-ㅎ (consonants), ㅏ-ㅣ (vowels)
                if '\uac00' <= char <= '\ud7af' or '\u3131' <= char <= '\u318e':
                    korean_chars += 1
        
        if total_chars == 0:
            return "en"  # Default to English if no letters
            
        korean_ratio = korean_chars / total_chars
        return "ko" if korean_ratio > 0.5 else "en"
    
    def _speak_with_pyttsx3(self, text: str, language: str = "auto") -> bool:
        """
        Speak text using pyttsx3 engine.
        
        Args:
            text (str): Text to speak
            language (str): Language code ("ko", "en", or "auto")
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.pyttsx3_engine:
            return False
            
        try:
            with self.tts_lock:
                # pyttsx3 doesn't handle Korean well, so prefer it for English
                detected_lang = self._detect_language(text) if language == "auto" else language
                
                if detected_lang == "ko":
                    # For Korean, convert to English equivalent if possible
                    if "시작해가 인식되었습니다" in text:
                        text = "Start trigger detected"
                    elif "음성 인식 시스템이 준비되었습니다" in text:
                        text = "Speech recognition system ready"
                    elif "오류" in text:
                        text = "Error occurred"
                
                self.pyttsx3_engine.say(text)
                self.pyttsx3_engine.runAndWait()
                
                if self.logger:
                    self.logger.debug(f"🔊 pyttsx3 spoke: '{text}'")
                return True
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ pyttsx3 speech failed: {str(e)}")
            return False
    
    def _speak_with_gtts(self, text: str, language: str = "auto") -> bool:
        """
        Speak text using Google TTS.
        
        Args:
            text (str): Text to speak
            language (str): Language code ("ko", "en", or "auto")
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not GTTS_AVAILABLE or not self.pygame_initialized:
            return False
            
        try:
            # Detect language
            detected_lang = self._detect_language(text) if language == "auto" else language
            
            # Create gTTS object
            tts = gTTS(text=text, lang=detected_lang, slow=False)
            
            # Save to temporary file
            temp_file = os.path.join(self.temp_dir, f'tts_{int(time.time())}.mp3')
            tts.save(temp_file)
            
            # Play the audio file
            with self.tts_lock:
                pygame.mixer.music.load(temp_file)
                pygame.mixer.music.play()
                
                # Wait for playback to finish
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
            
            # Clean up temporary file
            try:
                os.remove(temp_file)
            except OSError:
                pass
                
            if self.logger:
                self.logger.debug(f"🔊 gTTS spoke ({detected_lang}): '{text}'")
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ gTTS speech failed: {str(e)}")
            return False
    
    def speak(self, text: str, language: str = "auto", async_play: bool = True) -> bool:
        """
        Speak the given text using the best available TTS engine.
        
        Args:
            text (str): Text to speak
            language (str): Language code ("ko", "en", or "auto")
            async_play (bool): Whether to play asynchronously
            
        Returns:
            bool: True if speech was initiated successfully
        """
        if not self.tts_enabled:
            return False
            
        if not text.strip():
            return False
        
        # Function to perform TTS
        def _do_tts():
            success = False
            
            # Detect language if auto
            target_lang = self._detect_language(text) if language == "auto" else language
            
            # Try preferred engine first
            if self.engine_preference == "gtts" and target_lang == "ko":
                # gTTS is better for Korean
                success = self._speak_with_gtts(text, target_lang)
                if not success and self.pyttsx3_engine:
                    success = self._speak_with_pyttsx3(text, target_lang)
            else:
                # pyttsx3 is better for English
                if self.pyttsx3_engine:
                    success = self._speak_with_pyttsx3(text, target_lang)
                if not success:
                    success = self._speak_with_gtts(text, target_lang)
            
            if not success and self.logger:
                self.logger.warn(f"🔇 TTS failed for text: '{text}'")
                
            return success
        
        # Execute TTS
        if async_play:
            # Run in background thread to avoid blocking
            tts_thread = threading.Thread(target=_do_tts, daemon=True)
            tts_thread.start()
            return True
        else:
            return _do_tts()
    
    def speak_trigger_detected(self, language: str = "auto") -> bool:
        """
        Announce that the trigger phrase was detected.
        
        Args:
            language (str): Language for announcement
            
        Returns:
            bool: True if successful
        """
        if language == "ko" or (language == "auto" and self.language == "ko"):
            message = self.messages["trigger_detected_ko"]
        else:
            message = self.messages["trigger_detected_en"]
            
        return self.speak(message, language)
    
    def speak_system_ready(self, language: str = "auto") -> bool:
        """
        Announce that the system is ready.
        
        Args:
            language (str): Language for announcement
            
        Returns:
            bool: True if successful
        """
        if language == "ko" or (language == "auto" and self.language == "ko"):
            message = self.messages["system_ready_ko"]
        else:
            message = self.messages["system_ready_en"]
            
        return self.speak(message, language)
    
    def speak_error(self, error_type: str = "general", language: str = "auto") -> bool:
        """
        Announce an error occurred.
        
        Args:
            error_type (str): Type of error ("api", "audio", "general")
            language (str): Language for announcement
            
        Returns:
            bool: True if successful
        """
        if language == "ko" or (language == "auto" and self.language == "ko"):
            if error_type == "api":
                message = self.messages["api_error_ko"]
            elif error_type == "audio":
                message = self.messages["audio_error_ko"]
            else:
                message = "오류가 발생했습니다"
        else:
            if error_type == "api":
                message = self.messages["api_error_en"]
            elif error_type == "audio":
                message = self.messages["audio_error_en"]
            else:
                message = "An error occurred"
                
        return self.speak(message, language)
    
    def set_language(self, language: str):
        """
        Set the default language for TTS.
        
        Args:
            language (str): "ko", "en", or "auto"
        """
        if language in ["ko", "en", "auto"]:
            self.language = language
            if self.logger:
                self.logger.info(f"🌐 TTS language set to: {language}")
    
    def set_volume(self, volume: float):
        """
        Set TTS volume (0.0 to 1.0).
        
        Args:
            volume (float): Volume level
        """
        self.volume = max(0.0, min(1.0, volume))
        
        if self.pyttsx3_engine:
            self.pyttsx3_engine.setProperty('volume', self.volume)
            
        if self.logger:
            self.logger.info(f"🔊 TTS volume set to: {self.volume}")
    
    def enable_tts(self, enabled: bool = True):
        """
        Enable or disable TTS feedback.
        
        Args:
            enabled (bool): Whether to enable TTS
        """
        self.tts_enabled = enabled
        if self.logger:
            status = "enabled" if enabled else "disabled"
            self.logger.info(f"🔊 TTS feedback {status}")
    
    def cleanup(self):
        """
        Clean up TTS resources.
        """
        try:
            # Clean up pygame
            if self.pygame_initialized:
                pygame.mixer.quit()
                
            # Clean up pyttsx3
            if self.pyttsx3_engine:
                self.pyttsx3_engine.stop()
                
            # Clean up temporary directory
            import shutil
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                
            if self.logger:
                self.logger.info("🧹 TTS cleanup completed")
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"⚠️ TTS cleanup error: {str(e)}")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current TTS system status.
        
        Returns:
            dict: Status information
        """
        return {
            "tts_enabled": self.tts_enabled,
            "language": self.language,
            "pyttsx3_available": PYTTSX3_AVAILABLE and self.pyttsx3_engine is not None,
            "gtts_available": GTTS_AVAILABLE and self.pygame_initialized,
            "volume": self.volume,
            "temp_dir": self.temp_dir
        }