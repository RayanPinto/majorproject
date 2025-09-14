#!/usr/bin/env python3
"""
Speech Conversation Handler for Behavioral Analysis System
Integrates Live API speech-to-speech with existing agent system
"""

import asyncio
import threading
from typing import Optional, Callable
from speech_to_speech_engine import get_live_speech_engine
from utils import call_agent_async

# ANSI Color Codes
class Colors:
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    GRAY = '\033[90m'
    RESET = '\033[0m'

class SpeechConversationHandler:
    """Handles speech-to-speech conversations with the behavioral analysis agent"""
    
    def __init__(self, runner, user_id: str, session_id: str):
        self.runner = runner
        self.user_id = user_id
        self.session_id = session_id
        self.is_conversation_active = False
        self.speech_engine = None
        self.conversation_task = None
        
    async def start_speech_conversation(self):
        """Start a speech-to-speech conversation"""
        if self.is_conversation_active:
            print(f"{Colors.YELLOW}⚠️ Speech conversation already active{Colors.RESET}")
            return
        
        print(f"{Colors.CYAN}🎤 Starting speech conversation...{Colors.RESET}")
        
        # Initialize speech engine with callback
        def on_speech_recognized(recognized_text: str):
            # Handle recognized speech by sending to agent
            asyncio.create_task(self._handle_speech_input(recognized_text))
        
        self.speech_engine = get_live_speech_engine(on_speech_recognized)
        
        # Start the Live API session
        system_instruction = """You are a behavioral analysis assistant for interview scenarios. 
        Respond naturally and conversationally. Keep responses concise but helpful.
        You can analyze behavioral patterns, provide insights, and answer questions about interview performance.
        Be friendly and professional."""
        
        try:
            # Start conversation session
            success = await self.speech_engine.start_conversation_session(system_instruction)
            if not success:
                print(f"{Colors.RED}❌ Failed to start Live API session{Colors.RESET}")
                return
            
            self.is_conversation_active = True
            
            # Start listening for speech
            self.speech_engine.start_listening()
            
            # Start the conversation loop
            self.conversation_task = asyncio.create_task(self._conversation_loop())
            
            print(f"{Colors.GREEN}✅ Speech conversation started!{Colors.RESET}")
            print(f"{Colors.CYAN}💬 Speak naturally - I'll respond with voice{Colors.RESET}")
            print(f"{Colors.YELLOW}⚡ You can interrupt me at any time{Colors.RESET}")
            print(f"{Colors.GRAY}🛑 Say 'stop conversation' or type 'stop conversation' to end{Colors.RESET}")
            
        except Exception as e:
            print(f"{Colors.RED}❌ Failed to start speech conversation: {e}{Colors.RESET}")
            self.is_conversation_active = False
    
    async def _conversation_loop(self):
        """Main conversation loop handling Live API responses"""
        try:
            # Process audio stream and handle responses concurrently
            audio_task = asyncio.create_task(self.speech_engine.process_audio_stream())
            response_task = asyncio.create_task(self.speech_engine.handle_responses())
            
            # Wait for either task to complete or conversation to end
            while self.is_conversation_active:
                await asyncio.sleep(0.1)
            
            # Cancel tasks when conversation ends
            audio_task.cancel()
            response_task.cancel()
            
        except Exception as e:
            print(f"{Colors.RED}❌ Conversation loop error: {e}{Colors.RESET}")
        finally:
            await self._cleanup_conversation()
    
    async def _handle_speech_input(self, recognized_text: str):
        """Handle recognized speech input"""
        if not recognized_text.strip():
            return
        
        print(f"{Colors.BLUE}👤 You said: {recognized_text}{Colors.RESET}")
        
        # Check for stop commands
        if any(phrase in recognized_text.lower() for phrase in ["stop conversation", "end conversation", "quit", "exit"]):
            await self.stop_speech_conversation()
            return
        
        # Send to Live API session for processing
        if self.speech_engine and self.speech_engine.session:
            try:
                await self.speech_engine.send_text_to_session(recognized_text)
            except Exception as e:
                print(f"{Colors.RED}❌ Failed to send speech to session: {e}{Colors.RESET}")
    
    async def stop_speech_conversation(self):
        """Stop the speech conversation"""
        if not self.is_conversation_active:
            return
        
        print(f"{Colors.GRAY}🛑 Stopping speech conversation...{Colors.RESET}")
        
        self.is_conversation_active = False
        
        if self.speech_engine:
            self.speech_engine.stop_listening()
        
        if self.conversation_task:
            self.conversation_task.cancel()
            try:
                await self.conversation_task
            except asyncio.CancelledError:
                pass
        
        await self._cleanup_conversation()
        print(f"{Colors.GRAY}✅ Speech conversation stopped{Colors.RESET}")
    
    async def _cleanup_conversation(self):
        """Clean up conversation resources"""
        if self.speech_engine:
            await self.speech_engine.close_session()
    
    def is_active(self) -> bool:
        """Check if speech conversation is active"""
        return self.is_conversation_active

# Global conversation handler
_conversation_handler: Optional[SpeechConversationHandler] = None

def get_conversation_handler(runner, user_id: str, session_id: str) -> SpeechConversationHandler:
    """Get the global conversation handler instance"""
    global _conversation_handler
    if _conversation_handler is None:
        _conversation_handler = SpeechConversationHandler(runner, user_id, session_id)
    return _conversation_handler

async def start_speech_conversation(runner, user_id: str, session_id: str):
    """Start speech conversation"""
    handler = get_conversation_handler(runner, user_id, session_id)
    await handler.start_speech_conversation()

async def stop_speech_conversation():
    """Stop speech conversation"""
    global _conversation_handler
    if _conversation_handler:
        await _conversation_handler.stop_speech_conversation()

def is_speech_conversation_active() -> bool:
    """Check if speech conversation is active"""
    global _conversation_handler
    return _conversation_handler.is_active() if _conversation_handler else False
