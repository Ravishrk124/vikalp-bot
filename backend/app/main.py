# Load .env file before anything else
try:
    from dotenv import load_dotenv, find_dotenv
    load_dotenv(find_dotenv(), override=True)
except ImportError:
    pass  # dotenv optional

import os
import json
import asyncio
import shlex
import subprocess
import base64
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, File, UploadFile, Form, WebSocket, WebSocketDisconnect, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import PlainTextResponse, JSONResponse
from pydantic import BaseModel
from gtts import gTTS
import httpx

# Import our modules
from .session_manager import (
    create_session, get_session, update_session, delete_session,
    list_sessions, get_transcript_text, Session, save_and_notify_lead
)
from .grade_context import load_grade_context, get_available_grades
from .prompting import build_messages_for_llm

# Import voice architecture modules
from .voice_config import (
    get_config, update_config, ArchitectureMode,
    STTProvider, LLMProvider, TTSProvider
)
from .voice_openai import (
    transcribe_audio_openai, chat_completion_openai,
    text_to_speech_openai, chat_completion_openrouter
)
from .realtime_handler import RealtimeHandler, create_realtime_session

# ========== Directories ==========
ROOT = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(ROOT, "..", ".."))
LOG_DIR = os.path.join(PROJECT_ROOT, "backend", "logs")
DATA_DIR = os.path.join(PROJECT_ROOT, "backend", "data")
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

# ========== Helpers ==========
def now_str():
    return datetime.utcnow().isoformat() + "Z"

async def write_log(stage, payload):
    """Write JSONL log safely"""
    fn = os.path.join(LOG_DIR, f"log-{datetime.utcnow().date()}.jsonl")
    line = json.dumps({"timestamp": now_str(), "stage": stage, "payload": payload}, ensure_ascii=False) + "\n"
    try:
        async with asyncio.Lock():
            await asyncio.to_thread(lambda: open(fn, "a", encoding="utf-8").write(line))
    except Exception:
        pass

# ========== TTS (configurable) ==========
def _tts_gtts_sync(text, path):
    """gTTS fallback"""
    t = gTTS(text=text, lang="en")
    t.save(path)
    return os.path.exists(path)


async def tts_save(text: str, filename: str) -> str:
    """Save text as audio using configured TTS provider"""
    config = get_config()
    path = os.path.join(DATA_DIR, filename)

    try:
        if config.tts_provider == TTSProvider.OPENAI:
            # Use OpenAI TTS
            ok = await text_to_speech_openai(text, path)
            if ok:
                await write_log("tts_openai_done", {"file": filename})
                return path
            # Fallback to gTTS if OpenAI fails
            await write_log("tts_openai_fallback", {"reason": "OpenAI TTS failed"})

        # gTTS fallback
        ok = await asyncio.to_thread(_tts_gtts_sync, text, path)
        await write_log("tts_gtts_done", {"file": filename})
        return path if ok else ""
    except Exception as e:
        await write_log("tts_error", {"error": str(e)})
        return ""


# ========== LLM (configurable) ==========
async def call_llm(messages: list[dict]) -> str:
    """Call LLM using configured provider"""
    config = get_config()

    if config.llm_provider == LLMProvider.OPENAI:
        return await chat_completion_openai(messages)
    else:
        return await chat_completion_openrouter(messages)


async def call_llm_with_session(session: Session, user_query: str) -> str:
    """Call LLM with session context and prompting strategy"""
    messages = build_messages_for_llm(session, user_query)
    return await call_llm(messages)

# ========== STT: Local Whisper (fallback) ==========
_TRANSCRIBE_MODEL_OBJ = None


def _init_transcribe_model():
    """Initialize local Whisper model if needed"""
    global _TRANSCRIBE_MODEL_OBJ
    if _TRANSCRIBE_MODEL_OBJ:
        return
    config = get_config()
    try:
        from faster_whisper import WhisperModel
        _TRANSCRIBE_MODEL_OBJ = WhisperModel(
            config.local_whisper_model, device="cpu", compute_type="float32"
        )
        print(f"[INIT] faster-whisper loaded: {config.local_whisper_model}")
    except Exception as e:
        print(f"[INIT] faster-whisper failed: {e}")
        _TRANSCRIBE_MODEL_OBJ = None


async def transcribe_audio(audio_path: str) -> str:
    """Transcribe audio using configured STT provider"""
    config = get_config()

    if config.stt_provider == STTProvider.OPENAI:
        try:
            result = await transcribe_audio_openai(audio_path)
            if result and not result.startswith("(no "):
                await write_log("stt_openai_done", {"preview": result[:100]})
                return result
        except Exception as e:
            await write_log("stt_openai_error", {"error": str(e)})

    # Local Whisper fallback
    _init_transcribe_model()
    if _TRANSCRIBE_MODEL_OBJ:
        def _do_transcribe():
            segs, _ = _TRANSCRIBE_MODEL_OBJ.transcribe(audio_path, beam_size=5)
            return " ".join([s.text for s in segs]).strip()

        result = await asyncio.to_thread(_do_transcribe)
        await write_log("stt_local_done", {"preview": result[:100]})
        return result

    return "(transcription unavailable)"


# ========== FastAPI ==========
app = FastAPI(title="Vikalp AI Voice Agent", version="2.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.mount("/data", StaticFiles(directory=DATA_DIR), name="data")


@app.get("/")
async def root():
    config = get_config()
    return {
        "status": "ready",
        "time": now_str(),
        "architecture": config.architecture.value,
        "stt_provider": config.stt_provider.value,
        "llm_provider": config.llm_provider.value,
        "tts_provider": config.tts_provider.value,
    }


@app.get("/health")
async def health():
    return {"ok": True, "message": "backend alive", "time": now_str()}


# ========== CONFIGURATION ENDPOINTS ==========
@app.get("/config")
async def get_current_config():
    """Get current voice agent configuration"""
    config = get_config()
    return {
        "architecture": config.architecture.value,
        "stt_provider": config.stt_provider.value,
        "stt_model": config.stt_model,
        "llm_provider": config.llm_provider.value,
        "llm_model": config.llm_model,
        "tts_provider": config.tts_provider.value,
        "tts_model": config.tts_model,
        "tts_voice": config.tts_voice,
        "realtime_model": config.realtime_model,
        "realtime_voice": config.realtime_voice,
    }


class ConfigUpdate(BaseModel):
    architecture: Optional[str] = None
    stt_provider: Optional[str] = None
    llm_provider: Optional[str] = None
    tts_provider: Optional[str] = None


@app.post("/config")
async def update_config_endpoint(req: ConfigUpdate):
    """Update voice agent configuration at runtime"""
    updates = {}
    if req.architecture:
        updates["architecture"] = ArchitectureMode(req.architecture)
    if req.stt_provider:
        updates["stt_provider"] = STTProvider(req.stt_provider)
    if req.llm_provider:
        updates["llm_provider"] = LLMProvider(req.llm_provider)
    if req.tts_provider:
        updates["tts_provider"] = TTSProvider(req.tts_provider)

    update_config(**updates)
    await write_log("config_updated", updates)
    return {"ok": True, "config": await get_current_config()}


# ========== BACKGROUND TRANSCRIPTION ==========
async def transcribe_and_save(orig_path: str, safe_name: str, user_id: Optional[str]):
    """Convert, transcribe, log, save."""
    ts = int(datetime.utcnow().timestamp() * 1000)
    converted_path = os.path.join(DATA_DIR, f"conv-{ts}.wav")

    try:
        # Step 1: convert to 16k mono wav
        cmd = f'ffmpeg -y -i {shlex.quote(orig_path)} -ar 16000 -ac 1 -vn {shlex.quote(converted_path)}'
        await asyncio.to_thread(lambda: subprocess.run(cmd, shell=True, check=True))
        await write_log("ffmpeg_done", {"src": orig_path, "converted": converted_path})
    except Exception as e:
        await write_log("ffmpeg_error", {"error": str(e)})
        converted_path = orig_path

    # Step 2: transcribe using configured provider
    transcription = await transcribe_audio(converted_path)

    # Step 3: save transcription to file
    try:
        tpath = os.path.join(DATA_DIR, safe_name + ".txt")
        await asyncio.to_thread(lambda: open(tpath, "w").write(transcription))
        await write_log("transcription_saved_txt", {"file": tpath})
    except Exception as e:
        await write_log("save_txt_error", {"error": str(e)})

    await write_log("transcription_done", {"filename": safe_name, "preview": transcription[:200]})

@app.post("/upload_audio")
async def upload_audio(file: UploadFile = File(...), user_id: Optional[str] = Form(None)):
    ts = int(datetime.utcnow().timestamp() * 1000)
    safe_name = f"user-audio-{ts}-{file.filename.replace(' ', '_')}"
    path = os.path.join(DATA_DIR, safe_name)
    contents = await file.read()
    await asyncio.to_thread(lambda: open(path, "wb").write(contents))
    await write_log("audio_received", {"file": safe_name, "user": user_id})
    asyncio.create_task(transcribe_and_save(path, safe_name, user_id))
    return {"ok": True, "filename": safe_name, "processing": True}

@app.get("/transcription/{filename}")
async def get_transcription(filename: str):
    """Check if transcription text file exists."""
    txt_path = os.path.join(DATA_DIR, filename + ".txt")
    if os.path.exists(txt_path):
        text = await asyncio.to_thread(lambda: open(txt_path).read())
        return {"ok": True, "transcription": text, "source": "file"}
    else:
        return {"ok": False, "processing": True}


# ========== SESSION MANAGEMENT ==========
class CreateSessionRequest(BaseModel):
    """Request body for creating a session"""
    grade: str
    name: str
    email: str
    mobile: str
    intent: str  # Admission, Fees, Demo, Syllabus, Other


@app.post("/sessions")
async def create_session_endpoint(req: CreateSessionRequest):
    """Create a new session with lead capture info"""
    session = create_session(
        grade=req.grade,
        name=req.name,
        email=req.email,
        mobile=req.mobile,
        intent=req.intent
    )
    await write_log("session_created", {"session_id": session.session_id, "grade": req.grade})

    # Save lead to JSON and send email notification (background task)
    asyncio.create_task(save_and_notify_lead(session))

    return {
        "ok": True,
        "session_id": session.session_id,
        "grade": session.grade,
        "name": session.name
    }


@app.get("/sessions/{session_id}")
async def get_session_endpoint(session_id: str):
    """Get session details"""
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"ok": True, "session": session.to_dict()}


@app.get("/sessions/{session_id}/transcript")
async def get_session_transcript(session_id: str):
    """Download conversation transcript as text"""
    transcript = get_transcript_text(session_id)
    if not transcript:
        raise HTTPException(status_code=404, detail="Session not found")
    return PlainTextResponse(
        content=transcript,
        media_type="text/plain",
        headers={"Content-Disposition": f"attachment; filename=transcript-{session_id}.txt"}
    )


@app.get("/grades")
async def get_grades():
    """Get list of available grades"""
    grades = get_available_grades()
    return {"ok": True, "grades": grades}


@app.get("/grades/{grade}/context")
async def get_grade_context_endpoint(grade: str):
    """Get context for a specific grade"""
    context = load_grade_context(grade)
    if not context:
        raise HTTPException(status_code=404, detail="Grade context not found")
    return {"ok": True, "grade": grade, "context": context}


@app.get("/suggestions/{grade}/{intent}")
async def get_suggestions(grade: str, intent: str):
    """Get conversation starter suggestions based on grade and intent"""
    from .suggestions import get_conversation_starters
    suggestions = get_conversation_starters(grade, intent)
    return {"ok": True, "suggestions": suggestions}


# ========== WEBSOCKET: CHAINED ARCHITECTURE ==========
@app.websocket("/ws")
async def ws_handler_chained(ws: WebSocket, session_id: Optional[str] = Query(None)):
    """
    WebSocket handler for CHAINED architecture.
    Flow: text/audio → STT → LLM → TTS → audio
    """
    await ws.accept()
    session = get_session(session_id) if session_id else None
    config = get_config()
    await write_log("ws_chained_open", {
        "client": str(ws.client),
        "session_id": session_id,
        "architecture": "chained"
    })

    try:
        while True:
            msg = await ws.receive_json()
            msg_type = msg.get("type", "text")

            # Handle text message
            if msg_type == "text":
                text = msg.get("text", "")
                if not text:
                    continue
                await write_log("user_text", {"text": text, "session_id": session_id})

            # Handle audio message (base64 encoded)
            elif msg_type == "audio":
                audio_b64 = msg.get("audio", "")
                if not audio_b64:
                    continue

                # Decode and save audio
                ts = int(datetime.utcnow().timestamp() * 1000)
                audio_path = os.path.join(DATA_DIR, f"user-audio-{ts}.wav")
                audio_data = base64.b64decode(audio_b64)
                await asyncio.to_thread(lambda: open(audio_path, "wb").write(audio_data))

                # Transcribe audio
                text = await transcribe_audio(audio_path)
                await ws.send_json({"type": "transcription", "text": text})
                await write_log("user_audio_transcribed", {"text": text, "session_id": session_id})
            else:
                continue

            # Add user message to session history
            if session:
                session.add_turn("user", text)

            # Call LLM with full context
            try:
                reply = await call_llm_with_session(session, text) if session else await call_llm([
                    {"role": "user", "content": text}
                ])

                await write_log("llm_response", {"preview": reply[:200], "session_id": session_id})


                # Generate TTS audio
                # Clean text for TTS (remove emojis and markdown)
                import re
                def clean_text_for_tts(text: str) -> str:
                    # Remove emojis (regex for common ranges)
                    text = re.sub(r'[\U00010000-\U0010ffff]', '', text)
                    # Remove markdown asterisks (bold/italic) and hashes
                    text = text.replace('*', '').replace('#', '')
                    return text.strip()

                tts_text = clean_text_for_tts(reply)

                
                fname = None
                audio_url = None
                
                if tts_text:
                    ts = int(datetime.utcnow().timestamp() * 1000)
                    fname = f"ai-audio-{ts}.mp3"
                    try:
                        await tts_save(tts_text, fname)
                        audio_url = f"/data/{fname}"
                    except Exception as e:
                        await write_log("tts_error", {"error": str(e)})
                        fname = None

                # Add assistant response to session history
                if session:
                    session.add_turn("assistant", reply, audio_file=fname)

                await ws.send_json({
                    "type": "final",
                    "text": reply,
                    "audio_url": audio_url
                })
            except Exception as e:
                error_msg = str(e)
                await write_log("llm_tts_error", {"error": error_msg, "session_id": session_id})
                await ws.send_json({
                    "type": "error",
                    "message": f"AI processing error: {error_msg}"
                })

    except WebSocketDisconnect:
        await write_log("ws_chained_close", {"client": str(ws.client), "session_id": session_id})
    except Exception as e:
        await write_log("ws_chained_error", {"error": str(e), "session_id": session_id})
        try:
            await ws.send_json({"type": "error", "message": str(e)})
        except:
            pass


# ========== WEBSOCKET: REALTIME ARCHITECTURE ==========
@app.websocket("/ws/realtime")
async def ws_handler_realtime(ws: WebSocket, session_id: Optional[str] = Query(None)):
    """
    WebSocket handler for REALTIME (speech-to-speech) architecture.
    Proxies audio to/from OpenAI Realtime API.
    """
    await ws.accept()
    session = get_session(session_id) if session_id else None

    if not session:
        await ws.send_json({"type": "error", "message": "Session required for realtime mode"})
        await ws.close()
        return

    await write_log("ws_realtime_open", {
        "client": str(ws.client),
        "session_id": session_id,
        "architecture": "realtime"
    })

    # Create realtime handler
    realtime = RealtimeHandler(session)
    connected = await realtime.connect()

    if not connected:
        await ws.send_json({"type": "error", "message": "Failed to connect to OpenAI Realtime API"})
        await ws.close()
        return

    await ws.send_json({"type": "connected", "message": "Realtime session established"})

    # Set up callbacks to forward events to client
    async def on_audio(audio_chunk: bytes):
        audio_b64 = base64.b64encode(audio_chunk).decode("utf-8")
        await ws.send_json({"type": "audio", "audio": audio_b64})

    async def on_text(text: str):
        await ws.send_json({"type": "transcript", "text": text})
        if session:
            session.add_turn("assistant", text)

    realtime.on_audio(on_audio)
    realtime.on_text(on_text)

    # Start listening to realtime events in background
    listen_task = asyncio.create_task(realtime.listen())

    try:
        while True:
            msg = await ws.receive_json()
            msg_type = msg.get("type", "")

            if msg_type == "audio":
                # Forward audio to realtime API
                audio_b64 = msg.get("audio", "")
                if audio_b64:
                    audio_data = base64.b64decode(audio_b64)
                    await realtime.send_audio(audio_data)

            elif msg_type == "audio_commit":
                # Commit audio buffer
                await realtime.commit_audio()

            elif msg_type == "text":
                # Send text directly
                text = msg.get("text", "")
                if text:
                    if session:
                        session.add_turn("user", text)
                    await realtime.send_text(text)

    except WebSocketDisconnect:
        await write_log("ws_realtime_close", {"client": str(ws.client), "session_id": session_id})
    except Exception as e:
        await write_log("ws_realtime_error", {"error": str(e), "session_id": session_id})
    finally:
        listen_task.cancel()
        await realtime.disconnect()