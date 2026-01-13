"""Conversation Suggestions for Vikalp AI Voice Tutor
Provides grade-specific and intent-specific conversation starters and contextual suggestions
"""

# Grade-specific conversation starters
GRADE_STARTERS = {
    "Nursery": [
        {"text": "What will my child learn?", "emoji": "📚"},
        {"text": "Tell me about daily activities", "emoji": "🎨"},
        {"text": "How do online classes work?", "emoji": "💻"},
        {"text": "What is the fee structure?", "emoji": "💰"},
    ],
    "LKG": [
        {"text": "What subjects are taught?", "emoji": "📖"},
        {"text": "How is learning made fun?", "emoji": "🎮"},
        {"text": "Tell me about class timings", "emoji": "⏰"},
        {"text": "Can I get a demo class?", "emoji": "🎥"},
    ],
    "UKG": [
        {"text": "What is the curriculum?", "emoji": "📚"},
        {"text": "How do you prepare for Grade 1?", "emoji": "🎯"},
        {"text": "What are the admission steps?", "emoji": "📝"},
        {"text": "Tell me about teachers", "emoji": "👩‍🏫"},
    ],
}

# Default starters for Grades 1-12
DEFAULT_GRADE_STARTERS = [
    {"text": "What subjects are covered?", "emoji": "📚"},
    {"text": "How does online learning work?", "emoji": "💻"},
    {"text": "Tell me about admission process", "emoji": "📝"},
    {"text": "What are the fees?", "emoji": "💰"},
    {"text": "Can I get a demo class?", "emoji": "🎥"},
]

# Intent-specific starters
INTENT_STARTERS = {
    "Admission": [
        {"text": "What documents are needed?", "emoji": "📄"},
        {"text": "When can I enroll?", "emoji": "📅"},
        {"text": "Is there an entrance test?", "emoji": "✍️"},
        {"text": "How long does admission take?", "emoji": "⏱️"},
    ],
    "Fees": [
        {"text": "What is the total fee?", "emoji": "💰"},
        {"text": "Are there payment plans?", "emoji": "💳"},
        {"text": "Any discounts available?", "emoji": "🎁"},
        {"text": "What does the fee include?", "emoji": "📦"},
    ],
    "Demo": [
        {"text": "How do I book a demo?", "emoji": "📅"},
        {"text": "What happens in a demo class?", "emoji": "🎥"},
        {"text": "Is the demo free?", "emoji": "💰"},
        {"text": "Can I attend multiple demos?", "emoji": "🔄"},
    ],
    "Syllabus": [
        {"text": "Is it CBSE or NIOS?", "emoji": "📚"},
        {"text": "What topics are covered?", "emoji": "📖"},
        {"text": "How is assessment done?", "emoji": "✅"},
        {"text": "Are there practical classes?", "emoji": "🔬"},
    ],
    "Other": [
        {"text": "Tell me about Vikalp School", "emoji": "🏫"},
        {"text": "What makes you different?", "emoji": "⭐"},
        {"text": "How are teachers trained?", "emoji": "👩‍🏫"},
        {"text": "What are school timings?", "emoji": "⏰"},
    ],
}

# Contextual quick replies (shown after AI response)
CONTEXTUAL_SUGGESTIONS = [
    {"text": "Tell me more", "emoji": "💬"},
    {"text": "Can you explain in Hindi?", "emoji": "🇮🇳"},
    {"text": "What about fees?", "emoji": "💰"},
    {"text": "How do I enroll?", "emoji": "📝"},
    {"text": "Book a demo class", "emoji": "🎥"},
]

# Multilingual welcome suggestions
MULTILINGUAL_STARTERS = [
    {"text": "नमस्ते! प्रवेश के बारे में बताएं", "emoji": "🇮🇳"},
    {"text": "Hello! Tell me about admission", "emoji": "🇬🇧"},
    {"text": "విద్యార్థి ప్రవేశం గురించి చెప్పండి", "emoji": "🇮🇳"},
    {"text": "சேர்க்கை பற்றி சொல்லுங்கள்", "emoji": "🇮🇳"},
]


def get_conversation_starters(grade: str, intent: str) -> list[dict]:
    """Get initial conversation starters based on grade and intent"""
    starters = []
    
    # Add grade-specific starters
    if grade in GRADE_STARTERS:
        starters.extend(GRADE_STARTERS[grade])
    else:
        # For Grade 1-12, use default starters
        starters.extend(DEFAULT_GRADE_STARTERS[:4])
    
    # Add 2 intent-specific starters
    if intent in INTENT_STARTERS:
        starters.extend(INTENT_STARTERS[intent][:2])
    
    # Limit to 6 suggestions
    return starters[:6]


def get_contextual_suggestions(conversation_history: list = None) -> list[dict]:
    """Get contextual quick reply suggestions after AI response"""
    # For now, return standard contextual suggestions
    # In future, can analyze conversation_history to provide smarter suggestions
    return CONTEXTUAL_SUGGESTIONS[:4]


def get_multilingual_starters() -> list[dict]:
    """Get multilingual welcome suggestions"""
    return MULTILINGUAL_STARTERS
