import os, subprocess, json, tempfile, base64, sys, asyncio
from pathlib import Path
try:
    import openai
except Exception:
    openai = None
ROOT = Path(__file__).resolve().parents[1]
WHISPER_CPP = ROOT.joinpath("whisper.cpp","main")
MODELS_DIR = ROOT.joinpath("whisper.cpp","models")
def has_local_whisper():
    return WHISPER_CPP.exists() and MODELS_DIR.exists() and any(MODELS_DIR.glob("*.bin"))
def transcribe_with_whisper_cpp(path):
    model_files = list(MODELS_DIR.glob("*.bin"))
    if not model_files:
        return ""
    model = str(model_files[0])
    cmd = [str(WHISPER_CPP), "-m", model, "-f", str(path)]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        out = p.stdout.strip()
        lines = out.splitlines()
        if lines:
            return "\n".join(lines)
        return out
    except Exception as e:
        return ""
async def transcribe_file(path):
    if has_local_whisper():
        return transcribe_with_whisper_cpp(path)
    env_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_KEY")
    if openai and env_key:
        openai.api_key = env_key
        try:
            with open(path, "rb") as f:
                resp = await asyncio.to_thread(lambda: openai.Audio.transcribe("gpt-4o-mini-transcribe", f))
            if isinstance(resp, dict):
                return resp.get("text","")
            return str(resp)
        except Exception:
            return ""
    return ""
async def transcribe_b64(b64, fmt="wav"):
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=f".{fmt}")
    tmp.write(base64.b64decode(b64))
    tmp.flush()
    tmp.close()
    text = await transcribe_file(tmp.name)
    try:
        os.unlink(tmp.name)
    except Exception:
        pass
    return text
