#!/usr/bin/env python3
"""
Speech Utilities for Behavioral Analysis System
Provides text-to-speech functionality without disrupting existing functionality
"""

import pyttsx3
import threading
import re
from typing import Optional

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

class SpeechEngine:
    """Thread-safe speech engine for converting text to speech"""
    
    def __init__(self):
        self.engine = None
        self.is_enabled = True
        self.is_initialized = False
        self.speech_lock = threading.Lock()
        self._initialize_engine()
    
    def _initialize_engine(self):
        """Initialize the pyttsx3 engine with error handling"""
        try:
            self.engine = pyttsx3.init()
            
            # Configure speech properties for better experience
            if self.engine:
                # Set speech rate (words per minute) - moderate speed
                self.engine.setProperty('rate', 150)
                
                # Set volume (0.0 to 1.0)
                self.engine.setProperty('volume', 0.8)
                
                # Try to set a pleasant voice (prefer female voice if available)
                voices = self.engine.getProperty('voices')
                if voices and len(voices) > 1:
                    # Use female voice (index 1) if available, otherwise use default
                    self.engine.setProperty('voice', voices[1].id)
                
                self.is_initialized = True
                print(f"{Colors.GREEN}✅ Speech engine initialized successfully{Colors.RESET}")
            else:
                print(f"{Colors.YELLOW}⚠️ Speech engine could not be initialized{Colors.RESET}")
                
        except Exception as e:
            print(f"{Colors.YELLOW}⚠️ Speech engine initialization failed: {e}{Colors.RESET}")
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
        """Speak text asynchronously without blocking the main thread"""
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
        """Internal method to speak text (runs in separate thread)"""
        try:
            with self.speech_lock:
                if self.engine and self.is_enabled:
                    self.engine.say(text)
                    self.engine.runAndWait()
        except Exception as e:
            print(f"{Colors.YELLOW}⚠️ Speech synthesis error: {e}{Colors.RESET}")
    
    def speak_sync(self, text: str) -> None:
        """Speak text synchronously (blocks until speech is complete)"""
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
        """Stop current speech (if any)"""
        try:
            if self.engine:
                self.engine.stop()
        except Exception as e:
            print(f"{Colors.YELLOW}⚠️ Error stopping speech: {e}{Colors.RESET}")

# Global speech engine instance
_speech_engine: Optional[SpeechEngine] = None

def get_speech_engine() -> SpeechEngine:
    """Get the global speech engine instance (singleton pattern)"""
    global _speech_engine
    if _speech_engine is None:
        _speech_engine = SpeechEngine()
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
