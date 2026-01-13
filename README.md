# Vikalp AI Voice Tutor

AI-powered voice assistant for Vikalp Online School. Helps parents and students with admissions, fees, curriculum, and demo class information through natural voice and text conversations.

## Features

- 🎙️ **Voice Chat** - Speak naturally in English or Hindi
- 💬 **Text Chat** - Type questions and get instant responses
- 📚 **Grade Support** - Nursery to Grade 12 curriculum information
- 🎓 **Online Classes** - 12 course categories (Languages, Coding, Music, etc.)
- 🔊 **Text-to-Speech** - AI responses with audio playback
- 📱 **Responsive Design** - Works on desktop, tablet, and mobile

## Tech Stack

### Backend
- **FastAPI** - Python web framework
- **OpenRouter** - LLM API (Llama 3.2)
- **Faster-Whisper** - Local speech-to-text
- **gTTS** - Google Text-to-Speech
- **WebSocket** - Real-time communication

### Frontend
- **Next.js 14** - React framework
- **Tailwind CSS** - Styling
- **TypeScript** - Type safety

## Quick Start

### 1. Backend Setup

```bash
# Create virtual environment
cd ai-agent-2
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your OPENROUTER_API_KEY

# Start backend
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Frontend Setup

```bash
# Install dependencies
cd frontend
npm install

# Start development server
npm run dev
```

### 3. Access the App

Open http://localhost:3000 in your browser.

## Project Structure

```
ai-agent-2/
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI application
│   │   ├── prompting.py      # LLM prompt engineering
│   │   ├── session_manager.py # User session handling
│   │   ├── voice_config.py   # Provider configuration
│   │   └── voice_openai.py   # OpenAI/OpenRouter integration
│   ├── grade_data/           # Curriculum markdown files
│   └── course_data/          # Online classes data
├── frontend/
│   └── src/
│       ├── app/              # Next.js pages
│       └── components/       # React components
├── .env.example              # Environment template
└── README.md                 # This file
```

## Configuration

See `.env.example` for all configuration options:

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENROUTER_API_KEY` | OpenRouter API key | Required |
| `VOICE_STT_PROVIDER` | Speech-to-text provider | `local_whisper` |
| `VOICE_LLM_PROVIDER` | LLM provider | `openrouter` |
| `VOICE_TTS_PROVIDER` | Text-to-speech provider | `gtts` |

## License

Private - Vikalp Online School
