# backend/services/advanced_features.py
"""
Advanced features to implement if you have extra time during hackathon
These are optional enhancements that can make your demo stand out
"""

import os
import json
import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging
from langdetect import detect
import re

logger = logging.getLogger(__name__)

class AdvancedMentalHealthService:
    """
    Enhanced mental health features for competitive advantage
    """
    
    def __init__(self):
        self.mood_tracking = {}
        self.conversation_patterns = {}
        self.cultural_contexts = self.load_cultural_contexts()
        
    def load_cultural_contexts(self) -> Dict:
        """
        Load Kenya-specific cultural contexts for better responses
        """
        return {
            "greetings": {
                "swahili": ["hujambo", "mambo", "habari", "salama"],
                "english": ["hello", "hi", "hey", "good morning"]
            },
            "cultural_references": {
                "family_importance": "In Kenyan culture, family support is crucial for mental health",
                "community_healing": "Ubuntu philosophy - we heal together as a community",
                "traditional_healing": "Consider both modern and traditional healing approaches",
                "religious_context": "Many Kenyans find strength through faith communities"
            },
            "local_context": {
                "economic_stress": "Financial challenges are common - you're not alone",
                "unemployment": "Job market stress affects many young Kenyans",
                "rural_urban": "Moving between rural and urban areas can be challenging"
            }
        }
    
    async def analyze_mood_progression(self, user_id: str, message: str) -> Dict:
        """
        Track user mood over time for better personalized support
        This shows AI learning and adaptation
        """
        
        # Simple mood keywords (in production, use sentiment analysis)
        positive_words = ["happy", "good", "better", "hopeful", "furaha", "nzuri"]
        negative_words = ["sad", "bad", "worse", "hopeless", "huzuni", "mbaya"]
        
        message_lower = message.lower()
        
        # Calculate mood score
        positive_score = sum(1 for word in positive_words if word in message_lower)
        negative_score = sum(1 for word in negative_words if word in message_lower)
        
        mood_score = positive_score - negative_score
        
        # Store mood history
        if user_id not in self.mood_tracking:
            self.mood_tracking[user_id] = []
        
        mood_entry = {
            "timestamp": datetime.now().isoformat(),
            "score": mood_score,
            "message_length": len(message),
            "language": await self.detect_language(message)
        }
        
        self.mood_tracking[user_id].append(mood_entry)
        
        # Keep only last 10 entries
        self.mood_tracking[user_id] = self.mood_tracking[user_id][-10:]
        
        # Analyze trend
        recent_scores = [entry["score"] for entry in self.mood_tracking[user_id][-5:]]
        trend = "improving" if len(recent_scores) > 1 and recent_scores[-1] > recent_scores[0] else "stable"
        
        return {
            "current_mood": mood_score,
            "trend": trend,
            "session_length": len(self.mood_tracking[user_id]),
            "recommendation": self.get_mood_recommendation(mood_score, trend)
        }
    
    async def detect_language(self, text: str) -> str:
        """
        Detect message language for better cultural response
        """
        try:
            detected = detect(text)
            # Map common East African language codes
            language_map = {
                "sw": "swahili",
                "en": "english",
                "so": "somali"  # Some Kenyan communities
            }
            return language_map.get(detected, "english")
        except:
            return "english"
    
    def get_mood_recommendation(self, mood_score: int, trend: str) -> str:
        """
        Provide culturally appropriate recommendations based on mood
        """
        if mood_score <= -2:
            return "Consider reaching out to family or visiting a health center. Ubuntu - we are stronger together."
        elif mood_score < 0:
            return "Take time for self-care. In Kenyan tradition, talking to elders can provide wisdom."
        else:
            return "Your positive energy is good. Share it with your community - it helps others heal too."
    
    async def generate_personalized_response(
        self, 
        message: str, 
        user_id: str, 
        base_ai_response: str
    ) -> str:
        """
        Enhance AI response with cultural context and personalization
        """
        
        # Analyze mood
        mood_analysis = await self.analyze_mood_progression(user_id, message)
        language = mood_analysis.get("language", "english")
        
        # Add cultural context
        enhanced_response = base_ai_response
        
        # Add mood-aware suffix
        if mood_analysis["trend"] == "improving":
            if language == "swahili":
                enhanced_response += "\n\nNaona unaboresha kidogo. Hii ni nzuri sana! 🌟"
            else:
                enhanced_response += "\n\nI notice you're improving a bit. That's wonderful! 🌟"
        
        # Add cultural wisdom
        if "family" in message.lower() or "familia" in message.lower():
            enhanced_response += f"\n\n💝 {self.cultural_contexts['cultural_references']['family_importance']}"
        
        return enhanced_response
    
    async def generate_conversation_insights(self, user_id: str) -> Dict:
        """
        Generate insights for demo dashboard
        Shows AI learning capabilities
        """
        
        if user_id not in self.mood_tracking:
            return {"status": "new_user", "insights": []}
        
        mood_history = self.mood_tracking[user_id]
        
        insights = []
        
        # Session length insight
        if len(mood_history) > 5:
            insights.append(f"Engaged in {len(mood_history)} meaningful exchanges")
        
        # Mood trend insight
        recent_scores = [entry["score"] for entry in mood_history[-3:]]
        if len(recent_scores) > 1:
            if recent_scores[-1] > recent_scores[0]:
                insights.append("Mood trending positively during conversation")
            elif recent_scores[-1] < recent_scores[0]:
                insights.append("May need additional support - mood declining")
        
        # Language preference
        languages = [entry.get("language", "english") for entry in mood_history]
        primary_lang = max(set(languages), key=languages.count)
        if primary_lang == "swahili":
            insights.append("Prefers Swahili communication")
        
        return {
            "status": "active_user",
            "insights": insights,
            "session_score": sum(entry["score"] for entry in mood_history),
            "primary_language": primary_lang
        }


class VoiceMessageService:
    """
    Voice message processing for WhatsApp (if time permits)
    This adds a WOW factor to the demo
    """
    
    def __init__(self):
        self.supported_formats = [".mp3", ".ogg", ".wav", ".m4a"]
    
    async def process_voice_message(self, audio_url: str, user_id: str) -> str:
        """
        Process WhatsApp voice messages (mock implementation for demo)
        In production, would use speech-to-text service
        """
        
        # Mock transcription for demo
        mock_transcriptions = [
            "Nimehisi vibaya sana leo", # I feel very bad today
            "Nahitaji msaada wa haraka", # I need help urgently  
            "Familia yangu hainielezi", # My family doesn't understand me
            "Nina wasiwasi mkuu kuhusu kazi" # I have big worries about work
        ]
        
        import random
        transcription = random.choice(mock_transcriptions)
        
        logger.info(f"🎤 Mock voice transcription for {user_id}: {transcription}")
        
        return transcription
    
    async def convert_response_to_voice(self, text: str, language: str = "sw") -> str:
        """
        Convert text response to voice (mock for demo)
        In production, would use text-to-speech service
        """
        
        # Mock voice response URL
        mock_voice_url = f"https://api.mazungumzo.demo/voice/{hash(text)}.mp3"
        
        logger.info(f"🗣️ Mock voice response generated: {mock_voice_url}")
        
        return mock_voice_url


class CommunityFeatures:
    """
    Community support features for scalability demo
    """
    
    def __init__(self):
        self.peer_support_groups = {}
        self.success_stories = self.load_success_stories()
    
    def load_success_stories(self) -> List[Dict]:
        """
        Load anonymized success stories for hope and inspiration
        """
        return [
            {
                "story": "A university student from Nairobi overcame anxiety through daily check-ins with Mazungumzo",
                "impact": "Improved academic performance and social relationships",
                "duration": "3 months"
            },
            {
                "story": "A young farmer from Kiambu found coping strategies for climate-related stress",
                "impact": "Better emotional resilience during drought season",
                "duration": "2 months"
            },
            {
                "story": "A mother from Mombasa accessed postpartum depression support",
                "impact": "Connected with local maternal health services",
                "duration": "1 month"
            }
        ]
    
    async def suggest_peer_support(self, user_id: str, mood_pattern: str) -> Dict:
        """
        Suggest anonymous peer support connections
        """
        
        # Match users with similar challenges (privacy-preserving)
        support_suggestions = {
            "academic_stress": "Connect with other students facing similar pressures",
            "family_conflict": "Join discussions about family relationships in Kenyan context", 
            "economic_anxiety": "Share experiences with others navigating financial challenges",
            "general_support": "Join our daily check-in community for mutual encouragement"
        }
        
        return {
            "available": True,
            "suggestion": support_suggestions.get(mood_pattern, support_suggestions["general_support"]),
            "privacy_note": "All peer connections are anonymous and moderated"
        }


# Global service instances
advanced_service = AdvancedMentalHealthService()
voice_service = VoiceMessageService() 
community_service = CommunityFeatures()


# Integration with main app
async def enhance_ai_response(message: str, user_id: str, base_response: str) -> Dict:
    """
    Main function to enhance responses with advanced features
    Call this from your main chat endpoint
    """
    
    try:
        # Get mood analysis
        mood_analysis = await advanced_service.analyze_mood_progression(user_id, message)
        
        # Generate personalized response
        enhanced_response = await advanced_service.generate_personalized_response(
            message, user_id, base_response
        )
        
        # Get conversation insights
        insights = await advanced_service.generate_conversation_insights(user_id)
        
        # Suggest community support if appropriate
        community_suggestion = await community_service.suggest_peer_support(
            user_id, "general_support"
        )
        
        return {
            "response": enhanced_response,
            "mood_analysis": mood_analysis,
            "insights": insights,
            "community_suggestion": community_suggestion,
            "success_stories": community_service.success_stories[:2]  # Show 2 for inspiration
        }
        
    except Exception as e:
        logger.error(f"Advanced features error: {str(e)}")
        return {
            "response": base_response,
            "error": "Advanced features temporarily unavailable"
        }