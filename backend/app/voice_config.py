"""
Voice Agent Configuration

Supports two architectures:
1. CHAINED: audio → transcription (STT) → LLM → TTS → audio
   Models: gpt-4o-transcribe/whisper-1 → gpt-4.1/gpt-4o → tts-1/gpt-4o-mini-tts

2. REALTIME: Direct speech-to-speech via OpenAI Realtime API
   Model: gpt-4o-realtime-preview
"""
import os
from enum import Enum
from dataclasses import dataclass
from typing import Literal


class ArchitectureMode(str, Enum):
    CHAINED = "chained"
    REALTIME = "realtime"


class STTProvider(str, Enum):
    OPENAI = "openai"  # whisper-1 or gpt-4o-transcribe
    LOCAL_WHISPER = "local_whisper"  # faster-whisper


class LLMProvider(str, Enum):
    OPENAI = "openai"  # gpt-4o, gpt-4.1
    OPENROUTER = "openrouter"  # mistral, etc.


class TTSProvider(str, Enum):
    OPENAI = "openai"  # tts-1, tts-1-hd, gpt-4o-mini-tts
    GTTS = "gtts"  # Google TTS (free fallback)


@dataclass
class VoiceConfig:
    """Configuration for voice agent"""
    # Architecture mode
    architecture: ArchitectureMode = ArchitectureMode.CHAINED
    
    # OpenAI API
    openai_api_key: str = ""
    
    # STT Configuration
    stt_provider: STTProvider = STTProvider.OPENAI
    stt_model: str = "whisper-1"  # Options: whisper-1, gpt-4o-transcribe
    
    # LLM Configuration
    llm_provider: LLMProvider = LLMProvider.OPENAI
    llm_model: str = "gpt-4o"  # Options: gpt-4o, gpt-4.1, gpt-4o-mini
    
    # TTS Configuration
    tts_provider: TTSProvider = TTSProvider.OPENAI
    tts_model: str = "tts-1"  # Options: tts-1, tts-1-hd, gpt-4o-mini-tts
    tts_voice: str = "alloy"  # Options: alloy, echo, fable, onyx, nova, shimmer
    
    # Realtime API Configuration
    realtime_model: str = "gpt-4o-realtime-preview"
    realtime_voice: str = "alloy"
    
    # OpenRouter Configuration (fallback)
    openrouter_api_key: str = ""
    openrouter_model: str = "mistralai/mistral-7b-instruct"
    openrouter_base: str = "https://openrouter.ai/api"
    
    # Local Whisper Configuration (fallback)
    local_whisper_model: str = "small"


def load_config() -> VoiceConfig:
    """Load configuration from environment variables"""
    return VoiceConfig(
        # Architecture
        architecture=ArchitectureMode(
            os.getenv("VOICE_ARCHITECTURE", "chained").lower().strip()
        ),
        
        # OpenAI
        openai_api_key=os.getenv("OPENAI_API_KEY", "").strip(),
        
        # STT
        stt_provider=STTProvider(os.getenv("STT_PROVIDER", "local_whisper").lower().strip()),
        stt_model=os.getenv("STT_MODEL", "whisper-1").strip(),
        
        # LLM
        llm_provider=LLMProvider(os.getenv("LLM_PROVIDER", "openrouter").lower().strip()),
        llm_model=os.getenv("LLM_MODEL", "gpt-4o").strip(),
        
        # TTS
        tts_provider=TTSProvider(os.getenv("TTS_PROVIDER", "gtts").lower().strip()),
        tts_model=os.getenv("TTS_MODEL", "tts-1").strip(),
        tts_voice=os.getenv("TTS_VOICE", "alloy").strip(),
        
        # Realtime
        realtime_model=os.getenv("REALTIME_MODEL", "gpt-4o-realtime-preview").strip(),
        realtime_voice=os.getenv("REALTIME_VOICE", "alloy").strip(),
        
        # OpenRouter (fallback)
        openrouter_api_key=os.getenv("OPENROUTER_API_KEY", "").strip(),
        openrouter_model=os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.2-3b-instruct:free").strip(),
        openrouter_base=os.getenv("OPENROUTER_BASE", "https://openrouter.ai/api").strip(),
        
        # Local Whisper (fallback)
        local_whisper_model=os.getenv("TRANSCRIBE_MODEL", "small").strip(),
    )


# Global config instance - always reload fresh for development
def get_config() -> VoiceConfig:
    """Get or create the global config instance - reloads each time for dev"""
    return load_config()


def update_config(**kwargs) -> VoiceConfig:
    """Update config at runtime (useful for API-driven changes)"""
    global _config
    config = get_config()
    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)
    return config

