import sqlite3
import os
from datetime import datetime
from typing import Optional

ROOT = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(ROOT, "..", ".."))
DATA_DIR = os.path.join(PROJECT_ROOT, "backend", "data")
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, "agent.db")

def _conn():
    return sqlite3.connect(DB_PATH, timeout=10, check_same_thread=False)

def init_db():
    c = _conn()
    cur = c.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS messages (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      ts TEXT,
      role TEXT,
      text TEXT,
      filename TEXT,
      url TEXT,
      model TEXT
    );
    """)
    c.commit()
    c.close()
    return True

def insert_message(role: str, text: Optional[str]=None, filename: Optional[str]=None, url: Optional[str]=None, model: Optional[str]=None):
    c = _conn()
    cur = c.cursor()
    cur.execute(
        "INSERT INTO messages (ts, role, text, filename, url, model) VALUES (?, ?, ?, ?, ?, ?)",
        (datetime.utcnow().isoformat() + "Z", role, text, filename, url, model)
    )
    c.commit()
    rowid = cur.lastrowid
    c.close()
    return rowid

def list_messages(limit=100):
    c = _conn()
    cur = c.cursor()
    cur.execute("SELECT id, ts, role, substr(text,1,120) as text_preview, filename, url, model FROM messages ORDER BY id DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
    c.close()
    return rows
