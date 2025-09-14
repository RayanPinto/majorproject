#!/usr/bin/env python3
"""
Enhanced Speech-to-Speech Engine for Behavioral Analysis System
Integrates Google ADK Live API for bidirectional speech communication
Maintains compatibility with existing system architecture
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

class LiveSpeechEngine:
    """
    Enhanced speech engine with bidirectional Live API support
    Integrates with existing behavioral analysis system
    """
    
    def __init__(self, on_speech_recognized: Optional[Callable[[str], None]] = None):
        self.is_speech_mode_enabled = False
        self.is_listening = False
        self.is_speaking = False
        self.session = None
        self.client = None
        self.audio_queue = queue.Queue()
        self.response_queue = queue.Queue()
        
        # Audio configuration
        self.CHUNK_SIZE = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000  # 16kHz for input
        self.OUTPUT_RATE = 24000  # 24kHz for output
        
        # Callbacks
        self.on_speech_recognized = on_speech_recognized
        
        # Threading
        self.audio_thread = None
        self.session_thread = None
        self.playback_thread = None
        self.speech_lock = threading.Lock()
        
        # PyAudio instance
        self.audio = None
        self.input_stream = None
        self.output_stream = None
        
        # Initialize components
        self._initialize_audio()
        self._initialize_genai_client()
        
        print(f"{Colors.GREEN}✅ Live Speech Engine initialized{Colors.RESET}")
    
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
            print(f"{Colors.RED}❌ Audio initialization failed: {e}{Colors.RESET}")
            self.audio = None
    
    def _initialize_genai_client(self):
        """Initialize Google GenAI client for Live API"""
        try:
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("GOOGLE_API_KEY not found in environment")
            
            genai.configure(api_key=api_key)
            self.client = genai.Client()
            print(f"{Colors.GREEN}✅ Google GenAI client initialized{Colors.RESET}")
            
        except Exception as e:
            print(f"{Colors.RED}❌ GenAI client initialization failed: {e}{Colors.RESET}")
            self.client = None
    
    def enable_speech_mode(self):
        """Enable bidirectional speech mode"""
        if not self.client or not self.audio:
            print(f"{Colors.RED}❌ Cannot enable speech mode: missing dependencies{Colors.RESET}")
            return False
        
        if self.is_speech_mode_enabled:
            print(f"{Colors.YELLOW}⚠️ Speech mode already enabled{Colors.RESET}")
            return True
        
        try:
            self.is_speech_mode_enabled = True
            print(f"{Colors.GREEN}🔊 Speech mode enabled - You can now speak naturally{Colors.RESET}")
            print(f"{Colors.CYAN}💡 Say something to start a conversation...{Colors.RESET}")
            return True
            
        except Exception as e:
            print(f"{Colors.RED}❌ Failed to enable speech mode: {e}{Colors.RESET}")
            self.is_speech_mode_enabled = False
            return False
    
    def disable_speech_mode(self):
        """Disable speech mode and return to text input"""
        if not self.is_speech_mode_enabled:
            print(f"{Colors.GRAY}Speech mode already disabled{Colors.RESET}")
            return
        
        self.stop_listening()
        self.is_speech_mode_enabled = False
        print(f"{Colors.GRAY}🔇 Speech mode disabled - Back to text input{Colors.RESET}")
    
    async def start_conversation_session(self, system_instruction: str = None):
        """Start a Live API conversation session"""
        if not self.client:
            raise RuntimeError("GenAI client not initialized")
        
        # Configuration for bidirectional speech
        config = {
            "response_modalities": ["AUDIO", "TEXT"],
            "system_instruction": system_instruction or "You are a helpful behavioral analysis assistant. Respond naturally and conversationally.",
            "speech_config": {
                "voice_config": {
                    "prebuilt_voice_config": {
                        "voice_name": "Puck"
                    }
                }
            }
        }
        
        try:
            # Use the Live API model that supports bidirectional audio
            model = "gemini-2.0-flash-live-001"
            self.session = await self.client.aio.live.connect(model=model, config=config)
            print(f"{Colors.GREEN}🔗 Live conversation session started{Colors.RESET}")
            return True
            
        except Exception as e:
            print(f"{Colors.RED}❌ Failed to start conversation session: {e}{Colors.RESET}")
            return False
    
    def start_listening(self):
        """Start listening for speech input"""
        if not self.is_speech_mode_enabled or self.is_listening:
            return
        
        if not self.audio:
            print(f"{Colors.RED}❌ Audio system not available{Colors.RESET}")
            return
        
        try:
            # Open input stream
            self.input_stream = self.audio.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                frames_per_buffer=self.CHUNK_SIZE,
                stream_callback=self._audio_callback
            )
            
            self.is_listening = True
            self.input_stream.start_stream()
            
            print(f"{Colors.CYAN}🎤 Listening... (Speak naturally){Colors.RESET}")
            
        except Exception as e:
            print(f"{Colors.RED}❌ Failed to start listening: {e}{Colors.RESET}")
    
    def stop_listening(self):
        """Stop listening for speech input"""
        if not self.is_listening:
            return
        
        self.is_listening = False
        
        if self.input_stream:
            self.input_stream.stop_stream()
            self.input_stream.close()
            self.input_stream = None
        
        print(f"{Colors.GRAY}🔇 Stopped listening{Colors.RESET}")
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Callback for audio input stream"""
        if self.is_listening and self.session:
            # Convert audio data to numpy array for processing
            audio_data = np.frombuffer(in_data, dtype=np.int16)
            
            # Simple voice activity detection (energy-based)
            energy = np.sum(audio_data.astype(np.float32) ** 2) / len(audio_data)
            
            # If there's significant energy, queue the audio
            if energy > 1000:  # Threshold for voice activity
                self.audio_queue.put(in_data)
        
        return (None, pyaudio.paContinue)
    
    async def process_audio_stream(self):
        """Process queued audio data and send to Live API"""
        if not self.session:
            return
        
        try:
            while self.is_listening:
                try:
                    # Get audio data from queue (non-blocking)
                    audio_data = self.audio_queue.get_nowait()
                    
                    # Send audio to Live API
                    await self.session.send_realtime_input(
                        audio=types.Blob(
                            data=audio_data,
                            mime_type="audio/pcm;rate=16000"
                        )
                    )
                    
                except queue.Empty:
                    # No audio data available, continue
                    await asyncio.sleep(0.01)
                    continue
                    
        except Exception as e:
            print(f"{Colors.RED}❌ Audio processing error: {e}{Colors.RESET}")
    
    async def handle_responses(self):
        """Handle responses from Live API"""
        if not self.session:
            return
        
        try:
            async for response in self.session.receive():
                # Handle interruption
                if hasattr(response, 'server_content') and response.server_content and response.server_content.interrupted:
                    print(f"{Colors.YELLOW}⚠️ Speech interrupted{Colors.RESET}")
                    self.stop_current_playback()
                
                # Handle text response
                if response.text:
                    print(f"{Colors.BLUE}🤖 Agent: {response.text}{Colors.RESET}")
                    
                    # Call the speech recognition callback if provided
                    if self.on_speech_recognized:
                        self.on_speech_recognized(response.text)
                
                # Handle audio response
                if response.data:
                    self._play_audio_response(response.data)
                    
        except Exception as e:
            print(f"{Colors.RED}❌ Response handling error: {e}{Colors.RESET}")
    
    def _play_audio_response(self, audio_data: bytes):
        """Play audio response from the agent"""
        try:
            # Create temporary WAV file for playback
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                # Write PCM data as WAV file
                with wave.open(temp_file.name, 'wb') as wav_file:
                    wav_file.setnchannels(1)  # Mono
                    wav_file.setsampwidth(2)  # 16-bit
                    wav_file.setframerate(self.OUTPUT_RATE)  # 24kHz
                    wav_file.writeframes(audio_data)
                
                temp_file_path = temp_file.name
            
            # Play using PyAudio (non-blocking)
            self._play_wav_file(temp_file_path)
            
            # Clean up temporary file
            os.unlink(temp_file_path)
            
        except Exception as e:
            print(f"{Colors.RED}❌ Audio playback error: {e}{Colors.RESET}")
    
    def _play_wav_file(self, file_path: str):
        """Play WAV file using PyAudio"""
        try:
            # Open WAV file
            with wave.open(file_path, 'rb') as wf:
                # Open output stream
                output_stream = self.audio.open(
                    format=self.audio.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True
                )
                
                # Play audio
                self.is_speaking = True
                data = wf.readframes(self.CHUNK_SIZE)
                while data and self.is_speaking:
                    output_stream.write(data)
                    data = wf.readframes(self.CHUNK_SIZE)
                
                output_stream.stop_stream()
                output_stream.close()
                self.is_speaking = False
                
        except Exception as e:
            print(f"{Colors.RED}❌ WAV playback error: {e}{Colors.RESET}")
            self.is_speaking = False
    
    def stop_current_playback(self):
        """Stop current audio playback (for interruption)"""
        self.is_speaking = False
    
    async def send_text_to_session(self, text: str):
        """Send text message to the Live API session"""
        if not self.session:
            return False
        
        try:
            turns = [{
                "role": "user",
                "parts": [{"text": text}]
            }]
            
            await self.session.send_client_content(turns=turns, turn_complete=True)
            return True
            
        except Exception as e:
            print(f"{Colors.RED}❌ Failed to send text: {e}{Colors.RESET}")
            return False
    
    async def close_session(self):
        """Close the Live API session"""
        if self.session:
            try:
                await self.session.close()
                self.session = None
                print(f"{Colors.GRAY}🔌 Live session closed{Colors.RESET}")
            except Exception as e:
                print(f"{Colors.RED}❌ Error closing session: {e}{Colors.RESET}")
    
    def cleanup(self):
        """Clean up resources"""
        self.stop_listening()
        self.disable_speech_mode()
        
        if self.audio:
            self.audio.terminate()
            self.audio = None
        
        print(f"{Colors.GRAY}🧹 Live Speech Engine cleaned up{Colors.RESET}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of the speech engine"""
        return {
            "speech_mode_enabled": self.is_speech_mode_enabled,
            "is_listening": self.is_listening,
            "is_speaking": self.is_speaking,
            "session_active": self.session is not None,
            "audio_available": self.audio is not None,
            "client_available": self.client is not None
        }

# Global instance for easy access
_live_speech_engine: Optional[LiveSpeechEngine] = None

def get_live_speech_engine(on_speech_recognized: Optional[Callable[[str], None]] = None) -> LiveSpeechEngine:
    """Get the global Live Speech Engine instance (singleton pattern)"""
    global _live_speech_engine
    if _live_speech_engine is None:
        _live_speech_engine = LiveSpeechEngine(on_speech_recognized)
    return _live_speech_engine

def enable_speech_mode() -> bool:
    """Enable speech mode"""
    engine = get_live_speech_engine()
    return engine.enable_speech_mode()

def disable_speech_mode():
    """Disable speech mode"""
    engine = get_live_speech_engine()
    engine.disable_speech_mode()

def is_speech_mode_enabled() -> bool:
    """Check if speech mode is enabled"""
    engine = get_live_speech_engine()
    return engine.is_speech_mode_enabled

def get_speech_status() -> Dict[str, Any]:
    """Get speech engine status"""
    engine = get_live_speech_engine()
    return engine.get_status()
