"""
OpenAI Realtime API Handler for Speech-to-Speech Architecture

Uses WebSocket connection to OpenAI's Realtime API for:
- Direct audio input processing
- Real-time speech generation
- Low-latency conversation

Model: gpt-4o-realtime-preview
Transport: WebSocket
"""
import os
import json
import asyncio
import base64
from typing import Optional, Callable, Any
from dataclasses import dataclass
import websockets
from .voice_config import get_config
from .session_manager import Session


# OpenAI Realtime API WebSocket endpoint
OPENAI_REALTIME_WS = "wss://api.openai.com/v1/realtime"


@dataclass
class RealtimeSession:
    """Manages a realtime session with OpenAI"""
    session_id: str
    ws_connection: Any = None
    is_connected: bool = False
    current_audio_buffer: bytes = b""


class RealtimeHandler:
    """
    Handler for OpenAI Realtime API
    
    Implements speech-to-speech architecture with:
    - WebSocket connection management
    - Audio streaming
    - Event handling
    """
    
    def __init__(self, session: Session):
        self.session = session
        self.config = get_config()
        self.ws: Any = None
        self.is_connected = False
        self._audio_callback: Optional[Callable[[bytes], Any]] = None
        self._text_callback: Optional[Callable[[str], Any]] = None
    
    async def connect(self) -> bool:
        """Establish WebSocket connection to OpenAI Realtime API"""
        if not self.config.openai_api_key:
            return False
        
        url = f"{OPENAI_REALTIME_WS}?model={self.config.realtime_model}"
        headers = {
            "Authorization": f"Bearer {self.config.openai_api_key}",
            "OpenAI-Beta": "realtime=v1",
        }
        
        try:
            self.ws = await websockets.connect(url, extra_headers=headers)
            self.is_connected = True
            
            # Configure session
            await self._configure_session()
            
            return True
        except Exception as e:
            print(f"[Realtime] Connection failed: {e}")
            self.is_connected = False
            return False
    
    async def _configure_session(self):
        """Send session configuration to Realtime API"""
        from .prompting import build_system_prompt
        
        system_prompt = build_system_prompt(self.session, "")
        
        config_event = {
            "type": "session.update",
            "session": {
                "modalities": ["text", "audio"],
                "instructions": system_prompt,
                "voice": self.config.realtime_voice,
                "input_audio_format": "pcm16",
                "output_audio_format": "pcm16",
                "input_audio_transcription": {
                    "model": "whisper-1"
                },
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.5,
                    "prefix_padding_ms": 300,
                    "silence_duration_ms": 500
                }
            }
        }
        
        await self.ws.send(json.dumps(config_event))
    
    async def send_audio(self, audio_data: bytes):
        """Send audio data to Realtime API"""
        if not self.is_connected or not self.ws:
            return
        
        # Encode audio as base64
        audio_b64 = base64.b64encode(audio_data).decode("utf-8")
        
        event = {
            "type": "input_audio_buffer.append",
            "audio": audio_b64
        }
        
        await self.ws.send(json.dumps(event))
    
    async def commit_audio(self):
        """Commit audio buffer and request response"""
        if not self.is_connected or not self.ws:
            return
        
        # Commit the audio buffer
        await self.ws.send(json.dumps({"type": "input_audio_buffer.commit"}))
        
        # Request response
        await self.ws.send(json.dumps({"type": "response.create"}))
    
    async def send_text(self, text: str):
        """Send text message to Realtime API"""
        if not self.is_connected or not self.ws:
            return
        
        event = {
            "type": "conversation.item.create",
            "item": {
                "type": "message",
                "role": "user",
                "content": [{"type": "input_text", "text": text}]
            }
        }
        await self.ws.send(json.dumps(event))
        await self.ws.send(json.dumps({"type": "response.create"}))
    
    def on_audio(self, callback: Callable[[bytes], Any]):
        """Set callback for audio output"""
        self._audio_callback = callback

    def on_text(self, callback: Callable[[str], Any]):
        """Set callback for text output"""
        self._text_callback = callback

    async def listen(self):
        """Listen for events from Realtime API"""
        if not self.is_connected or not self.ws:
            return

        audio_buffer = b""
        transcript = ""

        try:
            async for message in self.ws:
                event = json.loads(message)
                event_type = event.get("type", "")

                # Handle different event types
                if event_type == "response.audio.delta":
                    # Audio chunk received
                    audio_b64 = event.get("delta", "")
                    if audio_b64:
                        audio_chunk = base64.b64decode(audio_b64)
                        audio_buffer += audio_chunk
                        if self._audio_callback:
                            await self._audio_callback(audio_chunk)

                elif event_type == "response.audio.done":
                    # Full audio response complete
                    pass

                elif event_type == "response.audio_transcript.delta":
                    # Transcript delta
                    transcript += event.get("delta", "")

                elif event_type == "response.audio_transcript.done":
                    # Full transcript
                    full_transcript = event.get("transcript", transcript)
                    if self._text_callback:
                        await self._text_callback(full_transcript)
                    transcript = ""

                elif event_type == "response.done":
                    # Response complete
                    audio_buffer = b""

                elif event_type == "error":
                    print(f"[Realtime] Error: {event.get('error', {})}")

                elif event_type == "input_audio_buffer.speech_started":
                    # User started speaking (VAD detected)
                    pass

                elif event_type == "input_audio_buffer.speech_stopped":
                    # User stopped speaking (VAD detected)
                    pass

        except websockets.exceptions.ConnectionClosed:
            self.is_connected = False
        except Exception as e:
            print(f"[Realtime] Listen error: {e}")
            self.is_connected = False

    async def disconnect(self):
        """Close WebSocket connection"""
        if self.ws:
            await self.ws.close()
        self.is_connected = False


async def create_realtime_session(session: Session) -> RealtimeHandler:
    """Create and connect a new realtime session"""
    handler = RealtimeHandler(session)
    await handler.connect()
    return handler

