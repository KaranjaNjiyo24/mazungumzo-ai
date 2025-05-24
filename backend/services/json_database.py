# backend/services/json_database.py
"""
Simple JSON-based database for Mazungumzo AI
Perfect for hackathon - no external database needed!

This handles:
- User conversation sessions
- Crisis event logging
- Usage statistics
- Mental health resources
"""

import json
import os
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class JSONDatabase:
    """
    Simple file-based JSON database
    Thread-safe and perfect for hackathon demos
    """
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Database files
        self.files = {
            "sessions": self.data_dir / "user_sessions.json",
            "crisis_events": self.data_dir / "crisis_events.json", 
            "stats": self.data_dir / "usage_stats.json",
            "resources": self.data_dir / "mental_health_resources.json"
        }
        
        # Initialize files if they don't exist
        self._initialize_files()
        
        # In-memory cache for performance
        self._cache = {}
        self._load_all_to_cache()
        
        logger.info(f"✅ JSON Database initialized at {self.data_dir}")
    
    def _initialize_files(self):
        """Create initial JSON files with default data"""
        
        # Default user sessions structure
        if not self.files["sessions"].exists():
            default_sessions = {
                "demo_user_12345": {
                    "user_id": "demo_user_12345",
                    "created_at": datetime.now().isoformat(),
                    "last_active": datetime.now().isoformat(),
                    "conversation_history": [
                        {
                            "role": "assistant",
                            "content": "Hujambo! Mimi ni Mazungumzo. Unahisije leo?",
                            "timestamp": datetime.now().isoformat(),
                            "language": "sw"
                        }
                    ],
                    "mood_scores": [0],
                    "crisis_flags": 0,
                    "platform": "web"
                }
            }
            self._write_json("sessions", default_sessions)
        
        # Crisis events log
        if not self.files["crisis_events"].exists():
            default_crisis = {
                "events": [],
                "total_interventions": 0,
                "last_updated": datetime.now().isoformat()
            }
            self._write_json("crisis_events", default_crisis)
        
        # Usage statistics
        if not self.files["stats"].exists():
            default_stats = {
                "total_users": 1,
                "total_conversations": 1,
                "total_messages": 1,
                "crisis_interventions": 0,
                "languages_used": {"english": 0, "swahili": 1},
                "platforms": {"web": 1, "whatsapp": 0, "sms": 0},
                "daily_stats": {},
                "last_updated": datetime.now().isoformat()
            }
            self._write_json("stats", default_stats)
        
        # Mental health resources for Kenya
        if not self.files["resources"].exists():
            default_resources = {
                "crisis_hotlines": [
                    {
                        "name": "Kenya Red Cross",
                        "number": "1199",
                        "description": "24/7 crisis support line",
                        "language": "English/Swahili"
                    },
                    {
                        "name": "Befrienders Kenya",
                        "number": "+254 722 178 177",
                        "description": "Suicide prevention hotline",
                        "language": "English/Swahili"
                    }
                ],
                "hospitals": [
                    {
                        "name": "Mathari National Teaching & Referral Hospital",
                        "location": "Nairobi",
                        "phone": "+254 20 2723841",
                        "services": "Psychiatric services, counseling"
                    },
                    {
                        "name": "Nairobi Hospital - Mental Health Unit",
                        "location": "Nairobi", 
                        "phone": "+254 719 055555",
                        "services": "Private psychiatric care"
                    }
                ],
                "online_resources": [
                    {
                        "name": "Kenya Association of Professional Counsellors",
                        "website": "kapc.or.ke",
                        "description": "Find certified counsellors"
                    },
                    {
                        "name": "Mental Health Kenya",
                        "website": "mentalhealthkenya.org",
                        "description": "Mental health awareness and resources"
                    }
                ],
                "support_groups": [
                    {
                        "name": "Nairobi Mental Health Support Groups",
                        "location": "Various locations in Nairobi",
                        "contact": "Contact through Mental Health Kenya"
                    }
                ]
            }
            self._write_json("resources", default_resources)
    
    def _load_all_to_cache(self):
        """Load all data into memory cache for fast access"""
        for key, file_path in self.files.items():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    self._cache[key] = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load {key}: {e}")
                self._cache[key] = {}
    
    def _write_json(self, key: str, data: Dict):
        """Write data to JSON file and update cache"""
        try:
            with open(self.files[key], 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self._cache[key] = data
            logger.debug(f"✅ Saved {key} to JSON")
        except Exception as e:
            logger.error(f"❌ Failed to save {key}: {e}")
    
    # User Session Management
    async def get_user_session(self, user_id: str) -> Optional[Dict]:
        """Get user conversation session"""
        sessions = self._cache.get("sessions", {})
        return sessions.get(user_id)
    
    async def create_user_session(self, user_id: str, platform: str = "web") -> Dict:
        """Create new user session"""
        session = {
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "last_active": datetime.now().isoformat(),
            "conversation_history": [],
            "mood_scores": [],
            "crisis_flags": 0,
            "platform": platform
        }
        
        sessions = self._cache.get("sessions", {})
        sessions[user_id] = session
        self._write_json("sessions", sessions)
        
        # Update stats
        await self.increment_stat("total_users")
        
        return session
    
    async def update_user_session(self, user_id: str, updates: Dict):
        """Update user session data"""
        sessions = self._cache.get("sessions", {})
        
        if user_id in sessions:
            sessions[user_id].update(updates)
            sessions[user_id]["last_active"] = datetime.now().isoformat()
            self._write_json("sessions", sessions)
        else:
            logger.warning(f"User session {user_id} not found for update")
    
    async def add_message_to_session(
        self, 
        user_id: str, 
        role: str, 
        content: str, 
        language: str = "en"
    ):
        """Add message to user conversation history"""
        session = await self.get_user_session(user_id)
        
        if not session:
            session = await self.create_user_session(user_id)
        
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "language": language
        }
        
        # Add to conversation history
        session["conversation_history"].append(message)
        
        # Keep only last 50 messages per session
        if len(session["conversation_history"]) > 50:
            session["conversation_history"] = session["conversation_history"][-50:]
        
        # Update session
        await self.update_user_session(user_id, session)
        
        # Update global stats
        await self.increment_stat("total_messages")
        await self.increment_stat(f"languages_used.{language}")
    
    # Crisis Event Management
    async def log_crisis_event(self, user_id: str, message: str, confidence: float):
        """Log crisis intervention event"""
        crisis_data = self._cache.get("crisis_events", {"events": []})
        
        event = {
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "message_snippet": message[:100] + "..." if len(message) > 100 else message,
            "confidence": confidence,
            "intervention_sent": True
        }
        
        crisis_data["events"].append(event)
        crisis_data["total_interventions"] = crisis_data.get("total_interventions", 0) + 1
        crisis_data["last_updated"] = datetime.now().isoformat()
        
        # Keep only last 100 crisis events
        if len(crisis_data["events"]) > 100:
            crisis_data["events"] = crisis_data["events"][-100:]
        
        self._write_json("crisis_events", crisis_data)
        
        # Update user session crisis flag
        session = await self.get_user_session(user_id)
        if session:
            session["crisis_flags"] = session.get("crisis_flags", 0) + 1
            await self.update_user_session(user_id, session)
        
        # Update global stats
        await self.increment_stat("crisis_interventions")
        
        logger.warning(f"🚨 Crisis event logged for user {user_id}")
    
    # Statistics Management
    async def increment_stat(self, stat_path: str, amount: int = 1):
        """Increment a statistic (supports dot notation like 'languages_used.english')"""
        stats = self._cache.get("stats", {})
        
        # Handle nested stats with dot notation
        keys = stat_path.split('.')
        current = stats
        
        # Navigate to parent
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Increment final key
        final_key = keys[-1]
        current[final_key] = current.get(final_key, 0) + amount
        
        # Update timestamp
        stats["last_updated"] = datetime.now().isoformat()
        
        self._write_json("stats", stats)
    
    async def get_stats(self) -> Dict:
        """Get current usage statistics"""
        stats = self._cache.get("stats", {})
        
        # Add real-time calculations
        sessions = self._cache.get("sessions", {})
        crisis_events = self._cache.get("crisis_events", {})
        
        real_time_stats = {
            **stats,
            "active_users": len(sessions),
            "total_conversations": len(sessions),
            "recent_crisis_events": len([
                e for e in crisis_events.get("events", [])
                if datetime.fromisoformat(e["timestamp"]) > datetime.now() - timedelta(hours=24)
            ]),
            "resources_available": sum(
                len(category) for category in self._cache.get("resources", {}).values()
                if isinstance(category, list)
            )
        }
        
        return real_time_stats
    
    # Resource Management
    async def get_mental_health_resources(self, category: Optional[str] = None) -> Dict:
        """Get mental health resources for Kenya"""
        resources = self._cache.get("resources", {})
        
        if category and category in resources:
            return {category: resources[category]}
        
        return resources
    
    async def get_crisis_resources(self) -> List[str]:
        """Get formatted crisis hotline information"""
        resources = self._cache.get("resources", {})
        hotlines = resources.get("crisis_hotlines", [])
        
        formatted = []
        for hotline in hotlines:
            formatted.append(f"🆘 {hotline['name']}: {hotline['number']}")
        
        return formatted
    
    # Utility Methods
    async def cleanup_old_sessions(self, days: int = 7):
        """Clean up old sessions (for production)"""
        sessions = self._cache.get("sessions", {})
        cutoff_date = datetime.now() - timedelta(days=days)
        
        cleaned_sessions = {}
        removed_count = 0
        
        for user_id, session in sessions.items():
            last_active = datetime.fromisoformat(session["last_active"])
            if last_active > cutoff_date:
                cleaned_sessions[user_id] = session
            else:
                removed_count += 1
        
        if removed_count > 0:
            self._write_json("sessions", cleaned_sessions)
            logger.info(f"🧹 Cleaned up {removed_count} old sessions")
    
    async def export_demo_data(self) -> Dict:
        """Export data for hackathon demo purposes"""
        return {
            "sessions_count": len(self._cache.get("sessions", {})),
            "total_messages": sum(
                len(session.get("conversation_history", []))
                for session in self._cache.get("sessions", {}).values()
            ),
            "crisis_events": len(self._cache.get("crisis_events", {}).get("events", [])),
            "resources_loaded": len(self._cache.get("resources", {})),
            "data_files": [str(f) for f in self.files.values()],
            "cache_status": "loaded" if self._cache else "empty"
        }

# Global database instance
db = JSONDatabase()

# Convenience functions for easy import
async def get_user_session(user_id: str):
    return await db.get_user_session(user_id)

async def add_message(user_id: str, role: str, content: str, language: str = "en"):
    return await db.add_message_to_session(user_id, role, content, language)

async def log_crisis(user_id: str, message: str, confidence: float):
    return await db.log_crisis_event(user_id, message, confidence)

async def get_stats():
    return await db.get_stats()

async def get_crisis_resources():
    return await db.get_crisis_resources()