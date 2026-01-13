"""Session management for Vikalp AI Voice Tutor"""
import os
import uuid
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field, asdict
import json
import asyncio

# Directory for data files
ROOT = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(ROOT, "..", ".."))
DATA_DIR = os.path.join(PROJECT_ROOT, "backend", "data")
os.makedirs(DATA_DIR, exist_ok=True)

# Leads file path
LEADS_FILE = os.path.join(DATA_DIR, os.getenv("LEADS_FILE", "leads.json"))

# Email configuration
LEAD_NOTIFICATION_EMAIL = os.getenv("LEAD_NOTIFICATION_EMAIL", "")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", "")
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "Vikalp Online School")

# Sessions stored in memory (can be replaced with DB later)
_sessions: Dict[str, "Session"] = {}

@dataclass
class ConversationTurn:
    """Single turn in conversation"""
    role: str  # "user" or "assistant"
    text: str
    audio_file: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    language: Optional[str] = None

@dataclass
class Session:
    """User session with lead info and conversation history"""
    session_id: str
    grade: str
    name: str
    email: str
    mobile: str
    intent: str  # What they are looking for (Admission, Fees, Demo, Syllabus)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    conversation: List[ConversationTurn] = field(default_factory=list)
    detected_language: Optional[str] = None
    
    def add_turn(self, role: str, text: str, audio_file: Optional[str] = None, language: Optional[str] = None):
        """Add a conversation turn"""
        turn = ConversationTurn(role=role, text=text, audio_file=audio_file, language=language)
        self.conversation.append(turn)
        self.updated_at = datetime.utcnow().isoformat() + "Z"
        if language:
            self.detected_language = language
        return turn

    def get_memory_snippets(self, max_turns: int = 10) -> str:
        """Get recent conversation history as formatted string"""
        recent = self.conversation[-max_turns:] if len(self.conversation) > max_turns else self.conversation
        if not recent:
            return "(No conversation history yet)"
        
        lines = []
        for turn in recent:
            role_label = "Parent/Student" if turn.role == "user" else "Vikalp AI"
            lines.append(f"{role_label}: {turn.text}")
        return "\n".join(lines)
    
    def to_dict(self) -> dict:
        """Convert session to dictionary"""
        return {
            "session_id": self.session_id,
            "grade": self.grade,
            "name": self.name,
            "email": self.email,
            "mobile": self.mobile,
            "intent": self.intent,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "detected_language": self.detected_language,
            "conversation": [asdict(t) for t in self.conversation]
        }

def _save_lead_to_json(lead_data: dict):
    """Save lead data to JSON file"""
    try:
        # Load existing leads
        leads = []
        if os.path.exists(LEADS_FILE):
            with open(LEADS_FILE, "r", encoding="utf-8") as f:
                try:
                    leads = json.load(f)
                except json.JSONDecodeError:
                    leads = []

        # Append new lead
        leads.append(lead_data)

        # Save back to file
        with open(LEADS_FILE, "w", encoding="utf-8") as f:
            json.dump(leads, f, indent=2, ensure_ascii=False)

        print(f"[LEAD] Saved lead to {LEADS_FILE}")
        return True
    except Exception as e:
        print(f"[LEAD] Error saving lead to JSON: {e}")
        return False


def _send_lead_email(lead_data: dict):
    """Send lead notification email"""
    if not LEAD_NOTIFICATION_EMAIL or not SMTP_USER or not SMTP_PASSWORD:
        print("[LEAD] Email notification skipped - SMTP not configured")
        return False

    try:
        # Create email content
        subject = f"New Lead: {lead_data['name']} - {lead_data['grade']} - {lead_data['intent']}"

        body_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #2563eb;">🎓 New Lead from Vikalp AI Voice Tutor</h2>
            <table style="border-collapse: collapse; width: 100%; max-width: 500px;">
                <tr style="background: #f3f4f6;">
                    <td style="padding: 10px; border: 1px solid #e5e7eb; font-weight: bold;">Name</td>
                    <td style="padding: 10px; border: 1px solid #e5e7eb;">{lead_data['name']}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #e5e7eb; font-weight: bold;">Email</td>
                    <td style="padding: 10px; border: 1px solid #e5e7eb;">{lead_data['email']}</td>
                </tr>
                <tr style="background: #f3f4f6;">
                    <td style="padding: 10px; border: 1px solid #e5e7eb; font-weight: bold;">Mobile</td>
                    <td style="padding: 10px; border: 1px solid #e5e7eb;">{lead_data['mobile']}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #e5e7eb; font-weight: bold;">Grade</td>
                    <td style="padding: 10px; border: 1px solid #e5e7eb;">{lead_data['grade']}</td>
                </tr>
                <tr style="background: #f3f4f6;">
                    <td style="padding: 10px; border: 1px solid #e5e7eb; font-weight: bold;">Looking For</td>
                    <td style="padding: 10px; border: 1px solid #e5e7eb;">{lead_data['intent']}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #e5e7eb; font-weight: bold;">Session ID</td>
                    <td style="padding: 10px; border: 1px solid #e5e7eb; font-size: 12px;">{lead_data['session_id']}</td>
                </tr>
                <tr style="background: #f3f4f6;">
                    <td style="padding: 10px; border: 1px solid #e5e7eb; font-weight: bold;">Date/Time</td>
                    <td style="padding: 10px; border: 1px solid #e5e7eb;">{lead_data['created_at']}</td>
                </tr>
            </table>
            <p style="margin-top: 20px; color: #6b7280; font-size: 12px;">
                This is an automated notification from Vikalp AI Voice Tutor.
            </p>
        </body>
        </html>
        """

        # Create message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{SMTP_FROM_NAME} <{SMTP_FROM or SMTP_USER}>"
        msg["To"] = LEAD_NOTIFICATION_EMAIL

        # Attach HTML content
        msg.attach(MIMEText(body_html, "html"))

        # Send email
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)

        print(f"[LEAD] Email notification sent to {LEAD_NOTIFICATION_EMAIL}")
        return True
    except Exception as e:
        print(f"[LEAD] Error sending email: {e}")
        return False


async def save_and_notify_lead(session: "Session"):
    """Save lead to JSON and send email notification (async)"""
    lead_data = {
        "session_id": session.session_id,
        "name": session.name,
        "email": session.email,
        "mobile": session.mobile,
        "grade": session.grade,
        "intent": session.intent,
        "created_at": session.created_at,
    }

    # Run IO operations in thread pool
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _save_lead_to_json, lead_data)
    await loop.run_in_executor(None, _send_lead_email, lead_data)


def create_session(grade: str, name: str, email: str, mobile: str, intent: str) -> Session:
    """Create a new session"""
    session_id = str(uuid.uuid4())
    session = Session(
        session_id=session_id,
        grade=grade,
        name=name,
        email=email,
        mobile=mobile,
        intent=intent
    )
    _sessions[session_id] = session
    return session

def get_session(session_id: str) -> Optional[Session]:
    """Get session by ID"""
    return _sessions.get(session_id)

def update_session(session_id: str, **kwargs) -> Optional[Session]:
    """Update session fields"""
    session = _sessions.get(session_id)
    if session:
        for key, value in kwargs.items():
            if hasattr(session, key):
                setattr(session, key, value)
        session.updated_at = datetime.utcnow().isoformat() + "Z"
    return session

def delete_session(session_id: str) -> bool:
    """Delete a session"""
    if session_id in _sessions:
        del _sessions[session_id]
        return True
    return False

def list_sessions() -> List[Session]:
    """List all sessions"""
    return list(_sessions.values())

def get_transcript_text(session_id: str) -> Optional[str]:
    """Generate downloadable transcript text"""
    session = get_session(session_id)
    if not session:
        return None
    
    lines = [
        "=" * 60,
        "VIKALP ONLINE SCHOOL - VOICE CHAT TRANSCRIPT",
        "=" * 60,
        "",
        f"Session ID: {session.session_id}",
        f"Date: {session.created_at}",
        f"Grade: {session.grade}",
        f"Name: {session.name}",
        f"Email: {session.email}",
        f"Mobile: {session.mobile}",
        f"Looking for: {session.intent}",
        "",
        "-" * 60,
        "CONVERSATION",
        "-" * 60,
        ""
    ]
    
    for turn in session.conversation:
        role_label = "Parent/Student" if turn.role == "user" else "Vikalp AI"
        lines.append(f"[{turn.timestamp}] {role_label}:")
        lines.append(turn.text)
        lines.append("")
    
    lines.extend([
        "-" * 60,
        "End of Transcript",
        "-" * 60
    ])
    
    return "\n".join(lines)

