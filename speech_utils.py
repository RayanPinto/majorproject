#!/usr/bin/env python3
"""
Speech Utilities for Behavioral Analysis System
Provides real audio speech functionality using Google ADK
"""

import threading
import re
import os
import tempfile
import pygame
import io
import asyncio
from typing import Optional
import google.generativeai as genai
from google.genai import types
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ANSI Color Codes for console output
class Colors:
    HEADER = '\033[95m'      # Purple
    BLUE = '\033[94m'        # Blue
    CYAN = '\033[96m'        # Cyan
    GREEN = '\033[92m'       # Green
    YELLOW = '\033[93m'      # Yellow
    RED = '\033[91m'         # Red
    BOLD = '\033[1m'         # Bold
    UNDERLINE = '\033[4m'    # Underline
    WHITE = '\033[97m'       # White
    GRAY = '\033[90m'        # Gray
    BG_RED = '\033[41m'      # Background Red
    BG_GREEN = '\033[42m'    # Background Green
    BG_YELLOW = '\033[43m'   # Background Yellow
    BG_BLUE = '\033[44m'     # Background Blue
    BG_PURPLE = '\033[45m'   # Background Purple
    BG_CYAN = '\033[46m'     # Background Cyan
    BG_WHITE = '\033[47m'    # Background White
    RESET = '\033[0m'        # Reset to default

class GoogleADKSpeechEngine:
    """Real speech engine using Google ADK built-in speech synthesis"""
    
    def __init__(self):
        self.is_enabled = True
        self.is_initialized = False
        self.speech_lock = threading.Lock()
        self.model = None
        self._initialize_engine()
    
    def _initialize_engine(self):
        """Initialize the Google ADK speech engine"""
        try:
            # Initialize pygame mixer for audio playback
            pygame.mixer.init(frequency=24000, size=-16, channels=1, buffer=512)
            
            # Configure Gemini API for speech synthesis
            api_key = os.getenv("GOOGLE_API_KEY")
            if api_key:
                genai.configure(api_key=api_key)
                # Initialize model for speech synthesis
                self.model = genai.GenerativeModel('gemini-2.0-flash-live-001')
                print(f"{Colors.GREEN}✅ Google ADK speech engine initialized successfully{Colors.RESET}")
                print(f"{Colors.CYAN}🔊 Using Google ADK built-in speech synthesis{Colors.RESET}")
            else:
                print(f"{Colors.RED}❌ No Google API key found{Colors.RESET}")
                self.is_enabled = False
                return
            
            self.is_initialized = True
                
        except Exception as e:
            print(f"{Colors.YELLOW}⚠️ Google ADK speech engine initialization failed: {e}{Colors.RESET}")
            print(f"{Colors.GRAY}Speech functionality will be disabled{Colors.RESET}")
            self.is_enabled = False
    
    def _clean_text_for_speech(self, text: str) -> str:
        """Clean text for better speech synthesis"""
        if not text:
            return ""
        
        # Remove markdown formatting
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # Remove bold
        text = re.sub(r'\*(.*?)\*', r'\1', text)      # Remove italic
        text = re.sub(r'`(.*?)`', r'\1', text)        # Remove code blocks
        text = re.sub(r'#{1,6}\s*', '', text)         # Remove headers
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)  # Remove links
        
        # Remove emojis and special characters that don't speak well
        text = re.sub(r'[🤖📊💡🎯🔥😰💭📈📅⚠️✅❌🔄🪟📤📥🚀⏹️🛑🔍]', '', text)
        
        # Replace common symbols with words
        text = text.replace('&', 'and')
        text = text.replace('@', 'at')
        text = text.replace('%', 'percent')
        text = text.replace('#', 'number')
        text = text.replace('→', 'to')
        text = text.replace('←', 'from')
        text = text.replace('↑', 'up')
        text = text.replace('↓', 'down')
        
        # Clean up multiple spaces and newlines
        text = re.sub(r'\n+', '. ', text)
        text = re.sub(r'\s+', ' ', text)
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        return text
    
    def speak_async(self, text: str) -> None:
        """Speak text asynchronously with real audio output"""
        if not self.is_enabled or not self.is_initialized or not text:
            return
        
        # Clean text for speech
        clean_text = self._clean_text_for_speech(text)
        if not clean_text:
            return
        
        # Limit text length for reasonable speech duration
        if len(clean_text) > 500:
            clean_text = clean_text[:500] + "..."
        
        # Start speech in a separate thread
        speech_thread = threading.Thread(
            target=self._speak_text, 
            args=(clean_text,), 
            daemon=True
        )
        speech_thread.start()
    
    def _speak_text(self, text: str) -> None:
        """Internal method to generate and play real speech audio"""
        try:
            with self.speech_lock:
                if not self.is_enabled:
                    return
                
                print(f"{Colors.CYAN}🔊 Speaking: {text[:50]}...{Colors.RESET}")
                
                # Generate speech audio
                audio_data = self._generate_speech_audio(text)
                if audio_data:
                    self._play_audio(audio_data)
                else:
                    print(f"{Colors.YELLOW}⚠️ Failed to generate speech audio{Colors.RESET}")
                    
        except Exception as e:
            print(f"{Colors.YELLOW}⚠️ Speech synthesis error: {e}{Colors.RESET}")
    
    def _generate_speech_audio(self, text: str) -> Optional[bytes]:
        """Generate speech audio using Google ADK speech synthesis"""
        try:
            if not self.model:
                return None
            
            # Use dictionary format instead of types objects (this is what the API expects)
            generation_config = {
                "response_modalities": ["AUDIO"],
                "speech_config": {
                    "voice_config": {
                        "prebuilt_voice_config": {
                            "voice_name": "Puck"
                        }
                    }
                }
            }
            
            # Generate speech
            response = self.model.generate_content(
                text,
                generation_config=generation_config
            )
            
            # Extract audio data from response
            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if (hasattr(part, 'inline_data') and 
                        part.inline_data and 
                        part.inline_data.mime_type and 
                        part.inline_data.mime_type.startswith("audio/")):
                        return part.inline_data.data
            
            return None
                
        except Exception as e:
            print(f"{Colors.YELLOW}⚠️ Google ADK speech generation error: {e}{Colors.RESET}")
            return None
    
    def _play_audio(self, audio_data: bytes) -> None:
        """Play audio data using pygame (Google ADK returns PCM audio)"""
        try:
            # Create a temporary file for the audio (Google ADK typically returns PCM)
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                # Write raw PCM data as WAV file
                import wave
                with wave.open(temp_file.name, 'wb') as wav_file:
                    wav_file.setnchannels(1)  # Mono
                    wav_file.setsampwidth(2)  # 16-bit
                    wav_file.setframerate(24000)  # 24kHz sample rate
                    wav_file.writeframes(audio_data)
                
                temp_file_path = temp_file.name
            
            # Load and play the audio
            pygame.mixer.music.load(temp_file_path)
            pygame.mixer.music.play()
            
            # Wait for playback to complete
            while pygame.mixer.music.get_busy():
                pygame.time.wait(100)
            
            # Clean up temporary file
            os.unlink(temp_file_path)
            
        except Exception as e:
            print(f"{Colors.YELLOW}⚠️ Audio playback error: {e}{Colors.RESET}")
            # Try direct playback as backup
            try:
                # Alternative: save as raw audio and play
                with tempfile.NamedTemporaryFile(suffix='.raw', delete=False) as temp_file:
                    temp_file.write(audio_data)
                    temp_file_path = temp_file.name
                
                # Use pygame to play raw audio
                sound = pygame.sndarray.make_sound(audio_data)
                sound.play()
                
                os.unlink(temp_file_path)
            except Exception as e2:
                print(f"{Colors.YELLOW}⚠️ Backup audio playback also failed: {e2}{Colors.RESET}")
    
    def speak_sync(self, text: str) -> None:
        """Speak text synchronously with real audio output"""
        if not self.is_enabled or not self.is_initialized or not text:
            return
        
        clean_text = self._clean_text_for_speech(text)
        if not clean_text:
            return
        
        self._speak_text(clean_text)
    
    def enable_speech(self) -> None:
        """Enable speech output"""
        self.is_enabled = True
        print(f"{Colors.GREEN}🔊 Speech output enabled{Colors.RESET}")
    
    def disable_speech(self) -> None:
        """Disable speech output"""
        self.is_enabled = False
        print(f"{Colors.GRAY}🔇 Speech output disabled{Colors.RESET}")
    
    def toggle_speech(self) -> bool:
        """Toggle speech on/off and return new state"""
        if self.is_enabled:
            self.disable_speech()
        else:
            self.enable_speech()
        return self.is_enabled
    
    def is_speech_enabled(self) -> bool:
        """Check if speech is enabled and working"""
        return self.is_enabled and self.is_initialized
    
    def get_speech_status(self) -> str:
        """Get current speech status as a formatted string"""
        if not self.is_initialized:
            return f"{Colors.RED}❌ Speech engine not initialized{Colors.RESET}"
        elif self.is_enabled:
            return f"{Colors.GREEN}🔊 Speech enabled{Colors.RESET}"
        else:
            return f"{Colors.GRAY}🔇 Speech disabled{Colors.RESET}"
    
    def stop_speech(self) -> None:
        """Stop current speech playback"""
        try:
            pygame.mixer.music.stop()
            print(f"{Colors.GRAY}🛑 Speech stopped{Colors.RESET}")
        except Exception as e:
            print(f"{Colors.YELLOW}⚠️ Error stopping speech: {e}{Colors.RESET}")

# Global speech engine instance
_speech_engine: Optional[GoogleADKSpeechEngine] = None

def get_speech_engine() -> GoogleADKSpeechEngine:
    """Get the global Google ADK speech engine instance (singleton pattern)"""
    global _speech_engine
    if _speech_engine is None:
        _speech_engine = GoogleADKSpeechEngine()
    return _speech_engine

def speak_text(text: str, async_speech: bool = True) -> None:
    """
    Convenience function to speak text
    
    Args:
        text: Text to speak
        async_speech: If True, speak asynchronously (non-blocking)
    """
    engine = get_speech_engine()
    if async_speech:
        engine.speak_async(text)
    else:
        engine.speak_sync(text)

def toggle_speech() -> bool:
    """Toggle speech on/off and return new state"""
    engine = get_speech_engine()
    return engine.toggle_speech()

def is_speech_enabled() -> bool:
    """Check if speech is enabled"""
    engine = get_speech_engine()
    return engine.is_speech_enabled()

def get_speech_status() -> str:
    """Get speech status"""
    engine = get_speech_engine()
    return engine.get_speech_status()

def stop_speech() -> None:
    """Stop current speech"""
    engine = get_speech_engine()
    engine.stop_speech()

# Speech-enhanced display functions
def speak_and_display_agent_response(response_text: str, agent_name: str = "Agent"):
    """Display agent response with speech output"""
    from utils import display_agent_response
    
    # Display text response (existing functionality)
    display_agent_response(response_text, agent_name)
    
    # Add speech output (new functionality)
    speak_text(response_text, async_speech=True)

def speak_and_display_success(message: str, title: str = "Success"):
    """Display success message with speech output"""
    from utils import display_success
    
    # Display text message (existing functionality)
    display_success(message, title)
    
    # Add speech output (new functionality)
    speak_text(f"{title}: {message}", async_speech=True)

def speak_and_display_error(error_message: str, error_type: str = "Error"):
    """Display error message with speech output"""
    from utils import display_error
    
    # Display text error (existing functionality)
    display_error(error_message, error_type)
    
    # Add speech output (new functionality)
    speak_text(f"{error_type}: {error_message}", async_speech=True)
