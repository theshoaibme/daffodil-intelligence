import re
from typing import Optional


def sanitize_input(text: str) -> str:
    return text.strip()[:5000]


def extract_intent(message: str) -> str:
    message = message.lower()
    intents = {
        "academic": ["cgpa", "grade", "result", "course", "exam", "syllabus"],
        "library": ["book", "borrow", "journal", "pdf"],
        "campus": ["shuttle", "room", "notice", "event", "campus"],
        "career": ["job", "internship", "cv", "resume", "career"],
        "coding": ["code", "debug", "programming", "error", "bug"],
        "research": ["paper", "thesis", "research", "citation"],
        "wellness": ["stress", "mental", "anxiety", "study"],
        "finance": ["fee", "payment", "waiver", "scholarship"],
    }

    for intent, keywords in intents.items():
        if any(kw in message for kw in keywords):
            return intent
    return "general"


def format_response(text: str) -> str:
    text = re.sub(r'\*\*([^*]+)\*\*', r'**\1**', text)
    text = re.sub(r'\*([^*]+)\*', r'*\1*', text)
    return text


def truncate(text: str, length: int = 1000) -> str:
    return text[:length] + "..." if len(text) > length else text