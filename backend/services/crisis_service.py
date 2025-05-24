# backend/services/crisis_service.py
"""
Crisis Detection Service for Mazungumzo AI
Handles crisis keyword detection and risk assessment
"""

import re
from typing import Tuple, List, Dict, Any
from datetime import datetime

from ..utils.config import settings
from ..utils.logging_config import get_logger, log_crisis_detection, log_performance
from ..utils.constants import ALL_CRISIS_KEYWORDS, CRISIS_KEYWORDS, HELP_CATEGORIES
from ..models.session_models import UserSession


class CrisisDetectionService:
    """Service for detecting mental health crises in user messages"""
    
    def __init__(self):
        self.logger = get_logger("crisis_service")
        self.crisis_keywords = ALL_CRISIS_KEYWORDS
        self.severity_weights = {
            "immediate_crisis": ["suicide", "kill myself", "end it all", "kujiua", "ninataka kufa"],
            "high_risk": ["harm myself", "cut myself", "overdose", "kujikatia", "sijaweza tena"],
            "moderate_risk": ["hopeless", "worthless", "no point", "hakuna maana", "sina maana"],
            "low_risk": ["sad", "tired", "stressed", "huzuni", "uchovu"]
        }
        self.logger.info(f"✅ Crisis Detection Service initialized with {len(self.crisis_keywords)} keywords")
    
    @log_performance("crisis_detect")
    def detect_crisis(self, message: str, user_session: UserSession = None) -> Tuple[bool, float, List[str]]:
        """
        Detect crisis indicators in a message
        
        Args:
            message: User's message to analyze
            user_session: Optional user session for context
            
        Returns:
            Tuple of (is_crisis, confidence_score, detected_keywords)
        """
        
        message_lower = message.lower().strip()
        detected_keywords = []
        crisis_score = 0.0
        severity_multiplier = 1.0
        
        # Check for crisis keywords with severity weighting
        for severity, keywords in self.severity_weights.items():
            for keyword in keywords:
                if keyword.lower() in message_lower:
                    detected_keywords.append(keyword)
                    
                    # Apply severity-based scoring
                    if severity == "immediate_crisis":
                        crisis_score += 3.0
                        severity_multiplier = max(severity_multiplier, 2.0)
                    elif severity == "high_risk":
                        crisis_score += 2.0
                        severity_multiplier = max(severity_multiplier, 1.5)
                    elif severity == "moderate_risk":
                        crisis_score += 1.0
                    elif severity == "low_risk":
                        crisis_score += 0.5
        
        # Context-based risk assessment
        context_score = self._assess_contextual_risk(message_lower, user_session)
        crisis_score += context_score
        
        # Apply severity multiplier
        crisis_score *= severity_multiplier
        
        # Pattern-based detection
        pattern_score = self._detect_crisis_patterns(message_lower)
        crisis_score += pattern_score
        
        # Calculate confidence (normalize to 0-1 range)
        confidence = min(crisis_score * 0.15, 0.95)  # Max confidence 95%
        is_crisis = confidence >= settings.crisis_confidence_threshold
        
        # Log crisis detection
        if is_crisis:
            user_id = user_session.user_id if user_session else "unknown"
            log_crisis_detection(self.logger, user_id, confidence, detected_keywords)
            
            # Flag crisis in user session
            if user_session:
                user_session.flag_crisis(confidence, detected_keywords, message)
        
        self.logger.debug(f"Crisis detection: score={crisis_score:.2f}, confidence={confidence:.2f}, is_crisis={is_crisis}")
        
        return is_crisis, confidence, detected_keywords
    
    def _assess_contextual_risk(self, message: str, user_session: UserSession = None) -> float:
        """Assess risk based on message context and history"""
        
        risk_score = 0.0
        
        # Check for time-based indicators (late night messages)
        current_hour = datetime.now().hour
        if 0 <= current_hour <= 5:  # Late night/early morning
            risk_score += 0.5
        
        # Check for isolation indicators
        isolation_phrases = [
            "nobody cares", "no one understands", "all alone", "hakuna mtu",
            "peke yangu", "sina mtu", "nobody loves me"
        ]
        for phrase in isolation_phrases:
            if phrase in message:
                risk_score += 1.0
        
        # Check for hopelessness indicators
        hopelessness_phrases = [
            "nothing will change", "no hope", "can't get better", "hakuna tumaini",
            "haitabadilika", "no way out", "trapped"
        ]
        for phrase in hopelessness_phrases:
            if phrase in message:
                risk_score += 1.5
        
        # Check for plan/method indicators (high risk)
        method_phrases = [
            "have a plan", "know how", "pills", "rope", "bridge", "knife",
            "mpango", "njia", "dawa", "kisu"
        ]
        for phrase in method_phrases:
            if phrase in message:
                risk_score += 2.5
        
        # Historical context from user session
        if user_session:
            # Check for pattern of concerning messages
            recent_messages = user_session.get_recent_messages(limit=10)
            crisis_message_count = 0
            
            for msg in recent_messages:
                if msg.get("role") == "user":
                    _, msg_confidence, _ = self.detect_crisis(msg.get("content", ""))
                    if msg_confidence > 0.3:
                        crisis_message_count += 1
            
            # Escalating pattern
            if crisis_message_count >= 3:
                risk_score += 1.0
            elif crisis_message_count >= 2:
                risk_score += 0.5
        
        return risk_score
    
    def _detect_crisis_patterns(self, message: str) -> float:
        """Detect crisis-indicating patterns in text"""
        
        pattern_score = 0.0
        
        # First person + negative action patterns
        first_person_patterns = [
            r"i (want to|will|am going to|plan to) (die|kill|hurt|end)",
            r"mimi (nataka|nitafanya|nina mpango wa) (kufa|kujiua|kujikatia)",
            r"i (can't|cannot|won't) (go on|continue|live|take it)",
            r"(sijui|siwezi|sitaweza) (kuendelea|kuishi|kuvumilia)"
        ]
        
        for pattern in first_person_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                pattern_score += 2.0
        
        # Finality patterns
        finality_patterns = [
            r"(this is|it's|hii ni) (the end|over|goodbye|mwisho|aya)",
            r"(tell everyone|waambie wote|say goodbye|waga)",
            r"(final|last|mwisho) (time|message|ujumbe)"
        ]
        
        for pattern in finality_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                pattern_score += 2.5
        
        # Burden/relief patterns
        burden_patterns = [
            r"(everyone|wote) (would be|better|bora) (without me|bila mimi)",
            r"(burden|mzigo|tatizo) (to everyone|kwa wote)",
            r"(relief|faraja|pumziko) (if i|kama)"
        ]
        
        for pattern in burden_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                pattern_score += 1.5
        
        # Question mark with concerning content (cry for help)
        if "?" in message:
            concerning_questions = [
                "what's the point", "why bother", "should i", "una maana gani",
                "kwa nini", "je ni", "what if i"
            ]
            for question in concerning_questions:
                if question in message:
                    pattern_score += 1.0
        
        return pattern_score
    
    def get_appropriate_resources(self, confidence: float, detected_keywords: List[str]) -> List[str]:
        """Get appropriate resources based on crisis severity"""
        
        if confidence >= 0.8:  # Immediate crisis
            return [
                "🆘 IMMEDIATE HELP NEEDED 🆘",
                "Kenya Red Cross Crisis Line: 1199 (24/7)",
                "Befrienders Kenya: +254 722 178 177",
                "Emergency Services: 999 or 112",
                "If you're in immediate danger, call 999"
            ]
        elif confidence >= 0.6:  # High risk
            return [
                "🚨 Crisis Support Available",
                "Kenya Red Cross: 1199 (24/7 crisis line)",
                "Befrienders Kenya: +254 722 178 177",
                "Mathari Hospital Emergency: +254 20 2723841",
                "You don't have to face this alone"
            ]
        elif confidence >= 0.4:  # Moderate risk
            return [
                "💛 Support Resources",
                "Befrienders Kenya: +254 722 178 177",
                "Mental Health Kenya: mentalhealthkenya.org",
                "Kenya Association of Professional Counsellors",
                "Consider talking to a counselor or trusted person"
            ]
        else:  # General support
            return [
                "💚 Mental Health Resources",
                "Mental Health Kenya: mentalhealthkenya.org",
                "Kenya Association of Professional Counsellors",
                "Remember: It's okay to seek help when you need it"
            ]
    
    def get_crisis_response_template(self, confidence: float, language: str = "en") -> str:
        """Get appropriate crisis response template"""
        
        if confidence >= 0.8:  # Immediate crisis
            if language.lower() in ["sw", "swahili"]:
                return ("Nimehuzunishwa sana na unachoongea. Hii ni hali ya haraka - tafadhali "
                       "wasiliana na msaada wa haraka sasa: Kenya Red Cross 1199. "
                       "Huwezi kukabiliana na hili peke yako na msaada unapatikana.")
            else:
                return ("I'm very concerned about what you've shared. This sounds like an emergency - "
                       "please contact immediate help now: Kenya Red Cross 1199. "
                       "You don't have to face this alone and help is available.")
        
        elif confidence >= 0.6:  # High risk
            if language.lower() in ["sw", "swahili"]:
                return ("Nasikia kwamba unapitia wakati mgumu sana. Hisia zako ni za kweli. "
                       "Tafadhali jua kwamba msaada unapatikana na una thamani kubwa. "
                       "Je, unaweza kuwasiliana na Befrienders Kenya +254 722 178 177?")
            else:
                return ("I hear that you're going through an incredibly difficult time. Your feelings are valid. "
                       "Please know that help is available and you have immense value. "
                       "Would you consider contacting Befrienders Kenya +254 722 178 177?")
        
        elif confidence >= 0.4:  # Moderate risk
            if language.lower() in ["sw", "swahili"]:
                return ("Nimesikia kwamba una matatizo. Ni muhimu ujue kwamba huko peke yako katika hili. "
                       "Kuongea na mtu wa kitaalamu kunaweza kusaidia. "
                       "Kuna rasilimali nyingi za msaada zinazopatikana.")
            else:
                return ("I hear that you're struggling. It's important to know that you're not alone in this. "
                       "Talking to a professional can help. "
                       "There are many support resources available.")
        
        else:  # General support
            if language.lower() in ["sw", "swahili"]:
                return ("Nashukuru kwa kuongea nami. Kumbuka kwamba ni sawa kutafuta msaada "
                       "unapohitaji na kuna watu wengi wanaotaka kukusaidia.")
            else:
                return ("Thank you for sharing with me. Remember that it's okay to seek help "
                       "when you need it and there are many people who want to support you.")
    
    def analyze_session_risk_trends(self, user_session: UserSession) -> Dict[str, Any]:
        """Analyze risk trends over time for a user session"""
        
        recent_messages = user_session.conversation_history[-20:]  # Last 20 messages
        crisis_incidents = user_session.crisis_flags
        
        # Calculate risk trend
        risk_scores = []
        for msg in recent_messages:
            if msg.role.value == "user":
                _, confidence, _ = self.detect_crisis(msg.content)
                risk_scores.append(confidence)
        
        if not risk_scores:
            return {"trend": "stable", "risk_level": "low", "recommendation": "continue_monitoring"}
        
        # Analyze trend
        recent_avg = sum(risk_scores[-5:]) / min(len(risk_scores), 5) if risk_scores else 0
        overall_avg = sum(risk_scores) / len(risk_scores)
        
        trend = "stable"
        if recent_avg > overall_avg + 0.1:
            trend = "escalating"
        elif recent_avg < overall_avg - 0.1:
            trend = "improving"
        
        # Determine risk level
        if recent_avg >= 0.7:
            risk_level = "high"
        elif recent_avg >= 0.4:
            risk_level = "moderate"
        else:
            risk_level = "low"
        
        # Generate recommendation
        recommendation = "continue_monitoring"
        if trend == "escalating" and risk_level in ["high", "moderate"]:
            recommendation = "immediate_intervention"
        elif risk_level == "high":
            recommendation = "urgent_followup"
        elif trend == "escalating":
            recommendation = "increased_monitoring"
        
        return {
            "trend": trend,
            "risk_level": risk_level,
            "recommendation": recommendation,
            "recent_average_risk": recent_avg,
            "overall_average_risk": overall_avg,
            "crisis_incidents_count": len(crisis_incidents),
            "last_crisis_detected": crisis_incidents[-1]["timestamp"] if crisis_incidents else None
        }


# Global crisis detection service instance
crisis_service = CrisisDetectionService()
