# backend/utils/constants.py
"""
Constants and static data for Mazungumzo AI
"""

from typing import List, Dict, Set

# Crisis detection keywords
CRISIS_KEYWORDS = {
    "english": [
        "suicide", "kill myself", "end it all", "no point living", "want to die",
        "harm myself", "cut myself", "overdose", "jump off", "hanging",
        "can't go on", "worthless", "hopeless", "end the pain", "better off dead",
        "nobody cares", "give up", "finish it", "escape", "permanent solution"
    ],
    "swahili": [
        "kujiua", "kufa", "kujikatia", "hakuna maana", "sijui la kufanya",
        "maumivu mengi", "sijaweza tena", "ninataka kufa", "sina maana",
        "hakuna mtu anayenijali", "nimekataa", "mimi ni mchafu",
        "sina tumaini", "maisha ni magumu", "sisemi naye"
    ]
}

# Get all crisis keywords as a flat list
ALL_CRISIS_KEYWORDS = []
for lang_keywords in CRISIS_KEYWORDS.values():
    ALL_CRISIS_KEYWORDS.extend(lang_keywords)

# Mental health topics for context recognition
MENTAL_HEALTH_TOPICS = {
    "depression": ["sad", "hopeless", "empty", "worthless", "tired", "sleep", "energy"],
    "anxiety": ["worry", "fear", "panic", "nervous", "stress", "overthinking", "restless"],
    "trauma": ["flashback", "nightmare", "abuse", "violence", "accident", "ptsd"],
    "relationships": ["lonely", "isolated", "family", "friends", "partner", "breakup"],
    "work_stress": ["job", "work", "pressure", "boss", "unemployed", "career"],
    "financial": ["money", "debt", "poor", "poverty", "bills", "expenses"]
}

# Response templates for different scenarios
RESPONSE_TEMPLATES = {
    "crisis_detected": {
        "en": "I'm very concerned about what you've shared. Please know that you're not alone and help is available. Would you like me to share some immediate support contacts?",
        "sw": "Nimehuzunishwa na ulichongea. Jua kwamba huko peke yako na msaada unapatikana. Je, ungependa nishiriki nambari za msaada wa haraka?"
    },
    "empathy_response": {
        "en": "I hear that you're going through a difficult time. Your feelings are valid, and it's okay to not be okay.",
        "sw": "Nasikia kwamba unapitia wakati mgumu. Hisia zako ni za kweli, na ni sawa kutokuwa sawa."
    },
    "encouragement": {
        "en": "You've shown strength by reaching out. That takes courage, and it's an important first step.",
        "sw": "Umeonyesha nguvu kwa kufikia. Hiyo inachukua ujasiri, na ni hatua muhimu ya kwanza."
    }
}

# System prompts for different contexts
SYSTEM_PROMPTS = {
    "default": """You are Mazungumzo, a compassionate mental health companion for people in Kenya. 

Key guidelines:
- Be warm, empathetic, and culturally sensitive
- Provide emotional support and coping strategies
- If someone seems in crisis, gently suggest professional help
- Respect Kenyan cultural values and context
- You can respond in both English and Swahili as needed
- Keep responses concise but meaningful
- Never provide medical diagnosis or replace professional therapy

Your goal is to be a supportive friend who listens and provides hope.""",

    "crisis": """You are Mazungumzo, responding to someone who may be in crisis. 

CRITICAL GUIDELINES:
- Express immediate concern and empathy
- Validate their feelings without judgment
- Gently encourage professional help
- Provide specific crisis resources for Kenya
- Stay calm and supportive
- Do not dismiss or minimize their feelings
- Emphasize that help is available and they are not alone

Remember: You are a bridge to professional help, not a replacement.""",

    "multilingual": """You are Mazungumzo, a bilingual mental health companion for Kenya.

LANGUAGE GUIDELINES:
- Detect the user's preferred language (English/Swahili)
- Respond in the same language when possible
- Use appropriate cultural context for each language
- Be sensitive to code-switching between languages
- Maintain warmth and empathy in both languages
- Adapt expressions to be culturally relevant"""
}

# Common Kenyan expressions and their contexts
KENYAN_EXPRESSIONS = {
    "greetings": {
        "habari": "how are you",
        "mambo": "what's up", 
        "poa": "cool/fine",
        "sawa": "okay",
        "salama": "peaceful"
    },
    "emotions": {
        "najiskia vibaya": "I feel bad",
        "nina wasiwasi": "I'm worried",
        "nimechoka": "I'm tired",
        "sina amani": "I have no peace",
        "moyo wangu unaumwa": "my heart hurts"
    }
}

# Professional help categories
HELP_CATEGORIES = {
    "immediate_crisis": [
        "suicidal thoughts",
        "self-harm urges", 
        "psychotic episodes",
        "severe panic attacks",
        "domestic violence"
    ],
    "urgent_care": [
        "severe depression",
        "anxiety disorders", 
        "trauma symptoms",
        "substance abuse",
        "eating disorders"
    ],
    "routine_support": [
        "stress management",
        "relationship issues",
        "work problems",
        "grief and loss",
        "life transitions"
    ]
}

# Resource contact formatting
CONTACT_FORMATS = {
    "phone": r"^\+254\d{9}$|^\d{3,4}$",  # Kenya phone numbers
    "email": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
    "website": r"^https?://|^www\.|\.org$|\.ke$|\.com$"
}

# Message formatting limits
MESSAGE_LIMITS = {
    "whatsapp_max_length": 1600,
    "sms_max_length": 160,
    "web_max_length": 2000,
    "crisis_alert_max": 500
}

# Supported languages
SUPPORTED_LANGUAGES = {
    "en": {"name": "English", "code": "en", "rtl": False},
    "sw": {"name": "Kiswahili", "code": "sw", "rtl": False}
}

# Time-based responses
TIME_BASED_RESPONSES = {
    "morning": {
        "en": "Good morning! How are you feeling today?",
        "sw": "Habari za asubuhi! Unajisikiaje leo?"
    },
    "afternoon": {
        "en": "Good afternoon! How has your day been?",
        "sw": "Habari za mchana! Je, siku yako imekuwaje?"
    },
    "evening": {
        "en": "Good evening! How are you doing?",
        "sw": "Habari za jioni! Unajisikiaje?"
    },
    "late_night": {
        "en": "It's quite late. How are you feeling right now?",
        "sw": "Ni usiku wa manane. Unajisikiaje sasa hivi?"
    }
}

# Default conversation starters
CONVERSATION_STARTERS = [
    "How are you feeling today?",
    "What's on your mind?", 
    "I'm here to listen. What would you like to talk about?",
    "How has your day been?",
    "What's bringing you here today?"
]
