"""
OpenAI Voice Services for Chained Architecture

Implements:
- STT: Speech-to-Text using whisper-1 or gpt-4o-transcribe
- LLM: Chat completion using gpt-4o, gpt-4.1
- TTS: Text-to-Speech using tts-1, tts-1-hd, gpt-4o-mini-tts
"""
import os
import asyncio
import httpx
from typing import Optional
from .voice_config import get_config, STTProvider, LLMProvider, TTSProvider


# OpenAI API endpoints
OPENAI_API_BASE = "https://api.openai.com/v1"
OPENAI_TRANSCRIPTION_ENDPOINT = f"{OPENAI_API_BASE}/audio/transcriptions"
OPENAI_CHAT_ENDPOINT = f"{OPENAI_API_BASE}/chat/completions"
OPENAI_TTS_ENDPOINT = f"{OPENAI_API_BASE}/audio/speech"


async def transcribe_audio_openai(audio_path: str, language: Optional[str] = None) -> str:
    """
    Transcribe audio using OpenAI's Whisper API.
    
    Models:
    - whisper-1: Standard Whisper model
    - gpt-4o-transcribe: Enhanced transcription (coming soon)
    """
    config = get_config()
    
    if not config.openai_api_key:
        return "(no OPENAI_API_KEY set)"
    
    headers = {
        "Authorization": f"Bearer {config.openai_api_key}",
    }
    
    # Read audio file
    with open(audio_path, "rb") as audio_file:
        files = {
            "file": (os.path.basename(audio_path), audio_file, "audio/wav"),
            "model": (None, config.stt_model),
        }
        if language:
            files["language"] = (None, language)
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                OPENAI_TRANSCRIPTION_ENDPOINT,
                headers=headers,
                files=files
            )
            response.raise_for_status()
            result = response.json()
    
    return result.get("text", "")


async def chat_completion_openai(messages: list[dict], temperature: float = 0.7) -> str:
    """
    Generate chat completion using OpenAI's API.
    
    Models:
    - gpt-4o: Latest multimodal model
    - gpt-4.1: Enhanced reasoning
    - gpt-4o-mini: Faster, cheaper
    """
    config = get_config()
    
    if not config.openai_api_key:
        return "(no OPENAI_API_KEY set)"
    
    headers = {
        "Authorization": f"Bearer {config.openai_api_key}",
        "Content-Type": "application/json",
    }
    
    data = {
        "model": config.llm_model,
        "messages": messages,
        "temperature": temperature,
    }
    
    async with httpx.AsyncClient(timeout=90.0) as client:
        response = await client.post(
            OPENAI_CHAT_ENDPOINT,
            headers=headers,
            json=data
        )
        response.raise_for_status()
        result = response.json()
    
    return result.get("choices", [{}])[0].get("message", {}).get("content", "")


async def text_to_speech_openai(text: str, output_path: str) -> bool:
    """
    Convert text to speech using OpenAI's TTS API.
    
    Models:
    - tts-1: Standard TTS (~100ms latency)
    - tts-1-hd: High-definition TTS
    - gpt-4o-mini-tts: Enhanced TTS with emotion
    
    Voices: alloy, echo, fable, onyx, nova, shimmer
    """
    config = get_config()
    
    if not config.openai_api_key:
        return False
    
    headers = {
        "Authorization": f"Bearer {config.openai_api_key}",
        "Content-Type": "application/json",
    }
    
    data = {
        "model": config.tts_model,
        "input": text,
        "voice": config.tts_voice,
        "response_format": "mp3",
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            OPENAI_TTS_ENDPOINT,
            headers=headers,
            json=data
        )
        response.raise_for_status()
        
        # Write audio to file
        with open(output_path, "wb") as f:
            f.write(response.content)
    
    return os.path.exists(output_path)


# OpenRouter fallback for LLM
async def chat_completion_openrouter(messages: list[dict], temperature: float = 0.7) -> str:
    """Fallback LLM using OpenRouter API"""
    config = get_config()
    
    if not config.openrouter_api_key:
        return "(no OPENROUTER_API_KEY set)"
    
    headers = {
        "Authorization": f"Bearer {config.openrouter_api_key}",
        "Content-Type": "application/json",
    }
    
    data = {
        "model": config.openrouter_model,
        "messages": messages,
        "temperature": temperature,
    }
    
    endpoint = f"{config.openrouter_base}/v1/chat/completions"
    
    async with httpx.AsyncClient(timeout=90.0) as client:
        response = await client.post(endpoint, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
    
    return result.get("choices", [{}])[0].get("message", {}).get("content", "")

