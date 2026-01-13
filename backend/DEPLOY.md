# Backend Deployment Guide

This FastAPI backend needs to be deployed to a platform that supports:
- Python 3.10+
- WebSocket connections
- System packages for audio processing (ffmpeg)

## Recommended Platforms

### Option 1: Railway (Recommended)

1. Create account at [railway.app](https://railway.app)
2. Create new project → Deploy from GitHub
3. Configure environment variables:
   ```
   OPENROUTER_API_KEY=your-key-here
   VOICE_STT_PROVIDER=local_whisper
   VOICE_LLM_PROVIDER=openrouter
   VOICE_TTS_PROVIDER=gtts
   ```
4. Railway auto-detects Python and deploys

### Option 2: Render

1. Create account at [render.com](https://render.com)
2. New → Web Service → Connect your repo
3. Configure:
   - Build Command: `pip install -r backend/requirements.txt`
   - Start Command: `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`
4. Add environment variables in dashboard

### Option 3: Fly.io

1. Install flyctl: `brew install flyctl`
2. Login: `fly auth login`
3. Create app: `fly apps create your-app-name`
4. Deploy: `fly deploy`

## Required Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENROUTER_API_KEY` | OpenRouter API key for LLM | Yes |
| `VOICE_STT_PROVIDER` | STT provider (local_whisper/openai) | Yes |
| `VOICE_LLM_PROVIDER` | LLM provider (openrouter/openai) | Yes |
| `VOICE_TTS_PROVIDER` | TTS provider (gtts/openai) | Yes |
| `OPENAI_API_KEY` | OpenAI key (if using OpenAI providers) | Optional |

## Testing

After deployment, verify backend is running:
```bash
curl https://your-backend-url/health
# Expected: {"ok":true,"message":"backend alive",...}
```

## WebSocket Support

Ensure your platform supports WebSocket connections. The app uses:
- `/ws` - Chained voice chat (STT → LLM → TTS)
- `/ws/realtime` - Realtime speech-to-speech
