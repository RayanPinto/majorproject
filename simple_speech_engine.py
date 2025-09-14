#!/usr/bin/env python3
"""
Simple Speech-to-Speech Engine using separate STT and TTS
Alternative approach when Live API isn't working properly
"""

import asyncio
import threading
import queue
import time
import io
import wave
import tempfile
import os
from typing import Optional, Callable, Dict, Any
from datetime import datetime

import pyaudio
import numpy as np
from google import genai
from google.genai import types
import speech_recognition as sr
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
    WHITE = '\033[97m'       # White
    GRAY = '\033[90m'        # Gray
    RESET = '\033[0m'        # Reset to default

class SimpleSpeechEngine:
    """
    Simple speech engine using separate STT and TTS components
    """
    
    def __init__(self):
        self.client = None
        self.is_listening = False
        self.is_speech_mode_enabled = False
        self.audio_stream = None
        self.pyaudio_instance = None
        self.is_playing_audio = False
        self.on_speech_recognized = None
        
        # Speech recognition
        self.recognizer = sr.Recognizer()
        self.microphone = None
        
        # Audio configuration
        self.sample_rate = 16000
        self.chunk_size = 1024
        self.channels = 1
        self.format = pyaudio.paInt16
        
        # VAD settings
        self.vad_threshold = 300
        self.silence_frames = 0
        self.max_silence_frames = 32  # 2 seconds
        self.speech_detected = False
        
        # Audio queue for recording
        self.audio_queue = queue.Queue()
        self.recording_thread = None
        self.is_recording = False
        
        # Initialize components
        self._initialize_audio()
        self._initialize_genai_client()
        self._initialize_speech_recognition()
        
        print(f"{Colors.GREEN}✅ Simple Speech Engine initialized{Colors.RESET}")
    
    def _initialize_audio(self):
        """Initialize PyAudio for microphone input and speaker output"""
        try:
            self.audio = pyaudio.PyAudio()
            
            # Test microphone availability
            device_count = self.audio.get_device_count()
            print(f"{Colors.CYAN}🎤 Found {device_count} audio devices{Colors.RESET}")
            
            # Find default input device
            default_input = self.audio.get_default_input_device_info()
            print(f"{Colors.CYAN}🎤 Default input: {default_input['name']}{Colors.RESET}")
            
        except Exception as e:
            print(f"{Colors.RED}❌ Failed to initialize audio: {e}{Colors.RESET}")
            self.audio = None
    
    def _initialize_genai_client(self):
        """Initialize Google GenAI client for text generation and TTS"""
        try:
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("GOOGLE_API_KEY not found in environment variables")
            
            self.client = genai.Client(api_key=api_key)
            print(f"{Colors.GREEN}✅ Google GenAI client initialized{Colors.RESET}")
            
        except Exception as e:
            print(f"{Colors.RED}❌ Failed to initialize GenAI client: {e}{Colors.RESET}")
            self.client = None
    
    def _initialize_speech_recognition(self):
        """Initialize speech recognition with microphone"""
        try:
            self.microphone = sr.Microphone()
            
            # Adjust for ambient noise
            print(f"{Colors.CYAN}🎤 Adjusting for ambient noise...{Colors.RESET}")
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
            
            print(f"{Colors.GREEN}✅ Speech recognition initialized{Colors.RESET}")
            
        except Exception as e:
            print(f"{Colors.RED}❌ Failed to initialize speech recognition: {e}{Colors.RESET}")
            self.microphone = None
    
    def enable_speech_mode(self) -> bool:
        """Enable speech mode"""
        if not self.audio or not self.client or not self.microphone:
            print(f"{Colors.RED}❌ Required components not available{Colors.RESET}")
            return False
        
        try:
            self.is_speech_mode_enabled = True
            print(f"{Colors.GREEN}🔊 Speech mode enabled{Colors.RESET}")
            return True
            
        except Exception as e:
            print(f"{Colors.RED}❌ Failed to enable speech mode: {e}{Colors.RESET}")
            self.is_speech_mode_enabled = False
            return False
    
    def disable_speech_mode(self):
        """Disable speech mode"""
        self.stop_listening()
        self.is_speech_mode_enabled = False
        print(f"{Colors.GRAY}🔇 Speech mode disabled{Colors.RESET}")
    
    async def start_conversation_session(self, system_instruction: str = None):
        """Start conversation session (simplified for this approach)"""
        if not self.client:
            return False
        
        self.system_instruction = system_instruction or "You are a helpful behavioral analysis assistant. Respond naturally and conversationally."
        print(f"{Colors.GREEN}🔗 Conversation session ready{Colors.RESET}")
        return True
    
    def start_listening(self):
        """Start listening for speech input using continuous recognition"""
        if not self.is_speech_mode_enabled or self.is_listening:
            return
        
        if not self.microphone:
            print(f"{Colors.RED}❌ Microphone not available{Colors.RESET}")
            return
        
        try:
            self.is_listening = True
            self.is_recording = True
            
            # Start background listening
            self.stop_listening_event = threading.Event()
            self.listening_thread = threading.Thread(target=self._listen_continuously, daemon=True)
            self.listening_thread.start()
            
            print(f"{Colors.CYAN}🎤 Listening... (Speak naturally){Colors.RESET}")
            
        except Exception as e:
            print(f"{Colors.RED}❌ Failed to start listening: {e}{Colors.RESET}")
            self.is_listening = False
    
    def stop_listening(self):
        """Stop listening for speech input"""
        if not self.is_listening:
            return
        
        self.is_listening = False
        self.is_recording = False
        
        if hasattr(self, 'stop_listening_event'):
            self.stop_listening_event.set()
        
        if hasattr(self, 'listening_thread') and self.listening_thread.is_alive():
            self.listening_thread.join(timeout=2)
        
        print(f"{Colors.GRAY}🔇 Stopped listening{Colors.RESET}")
    
    def _listen_continuously(self):
        """Continuously listen for speech in background thread"""
        while self.is_listening and not self.stop_listening_event.is_set():
            try:
                with self.microphone as source:
                    # Listen for speech with timeout
                    audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=5)
                
                # Process the audio in a separate thread to avoid blocking
                threading.Thread(target=self._process_audio, args=(audio,), daemon=True).start()
                
            except sr.WaitTimeoutError:
                # No speech detected, continue listening
                continue
            except Exception as e:
                if self.is_listening:  # Only show error if we're still supposed to be listening
                    print(f"{Colors.RED}❌ Listening error: {e}{Colors.RESET}")
                break
    
    def _process_audio(self, audio):
        """Process recognized audio"""
        try:
            # Use Google Speech Recognition
            text = self.recognizer.recognize_google(audio)
            
            if text.strip():
                print(f"{Colors.BLUE}👤 You said: {text}{Colors.RESET}")
                
                # Call the speech recognition callback if provided
                if self.on_speech_recognized:
                    self.on_speech_recognized(text)
                
        except sr.UnknownValueError:
            # Speech was unintelligible
            print(f"{Colors.GRAY}🤔 Could not understand audio{Colors.RESET}")
        except sr.RequestError as e:
            print(f"{Colors.RED}❌ Speech recognition error: {e}{Colors.RESET}")
        except Exception as e:
            print(f"{Colors.RED}❌ Audio processing error: {e}{Colors.RESET}")
    
    async def send_text_to_session(self, text: str):
        """Send text to the AI model and get response"""
        if not self.client:
            return
        
        try:
            # Generate response using Gemini
            model = self.client.models.generate_content(
                model="gemini-1.5-flash",
                contents=[
                    {"role": "system", "parts": [{"text": self.system_instruction}]},
                    {"role": "user", "parts": [{"text": text}]}
                ]
            )
            
            response_text = model.text
            if response_text:
                print(f"{Colors.BLUE}🤖 Agent: {response_text}{Colors.RESET}")
                
                # Generate and play audio response
                await self._generate_and_play_audio(response_text)
            
        except Exception as e:
            print(f"{Colors.RED}❌ Failed to process text: {e}{Colors.RESET}")
    
    async def _generate_and_play_audio(self, text: str):
        """Generate and play audio response using TTS"""
        try:
            # Use Google TTS (you might need to implement this with gTTS or similar)
            # For now, just show the text response
            print(f"{Colors.GREEN}🔊 Playing audio response: {text[:50]}...{Colors.RESET}")
            
            # TODO: Implement actual TTS playback here
            # This could use gTTS, pyttsx3, or Google Cloud TTS
            
        except Exception as e:
            print(f"{Colors.RED}❌ Failed to generate audio: {e}{Colors.RESET}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current engine status"""
        return {
            "speech_mode_enabled": self.is_speech_mode_enabled,
            "is_listening": self.is_listening,
            "audio_available": self.audio is not None,
            "client_available": self.client is not None,
            "microphone_available": self.microphone is not None
        }

# Global instance for easy access
_simple_speech_engine: Optional[SimpleSpeechEngine] = None

def get_simple_speech_engine(on_speech_recognized: Optional[Callable[[str], None]] = None) -> SimpleSpeechEngine:
    """Get the global Simple Speech Engine instance (singleton pattern)"""
    global _simple_speech_engine
    if _simple_speech_engine is None:
        _simple_speech_engine = SimpleSpeechEngine()
    if on_speech_recognized:
        _simple_speech_engine.on_speech_recognized = on_speech_recognized
    return _simple_speech_engine

def enable_simple_speech_mode() -> bool:
    """Enable simple speech mode"""
    engine = get_simple_speech_engine()
    return engine.enable_speech_mode()

def disable_simple_speech_mode():
    """Disable simple speech mode"""
    engine = get_simple_speech_engine()
    engine.disable_speech_mode()

def is_simple_speech_mode_enabled() -> bool:
    """Check if simple speech mode is enabled"""
    engine = get_simple_speech_engine()
    return engine.is_speech_mode_enabled

def get_simple_speech_status() -> Dict[str, Any]:
    """Get simple speech engine status"""
    engine = get_simple_speech_engine()
    return engine.get_status()
