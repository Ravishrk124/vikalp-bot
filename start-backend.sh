cd "$(dirname "$0")"
source .venv/bin/activate

export $(grep -v '^#' .env | xargs)

uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
