# backend/models/resource_models.py
"""
Mental health resources and crisis support models
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from enum import Enum


class ResourceType(str, Enum):
    """Types of mental health resources"""
    CRISIS_HOTLINE = "crisis_hotline"
    PROFESSIONAL_HELP = "professional_help"
    ONLINE_RESOURCE = "online_resource"
    EMERGENCY_SERVICE = "emergency_service"
    SUPPORT_GROUP = "support_group"


class CrisisResource(BaseModel):
    """Individual crisis resource model"""
    name: str = Field(..., description="Resource name")
    contact: str = Field(..., description="Phone number or contact info")
    description: Optional[str] = Field(None, description="Resource description")
    type: ResourceType = Field(..., description="Type of resource")
    available_24_7: bool = Field(default=False, description="24/7 availability")
    languages: List[str] = Field(default=["en", "sw"], description="Supported languages")
    location: Optional[str] = Field(None, description="Physical location if applicable")


class MentalHealthResources(BaseModel):
    """Complete mental health resources structure for Kenya"""
    crisis_hotlines: List[CrisisResource]
    professional_help: List[CrisisResource]
    online_resources: List[CrisisResource]
    emergency_services: List[CrisisResource]
    
    @classmethod
    def get_kenya_resources(cls) -> "MentalHealthResources":
        """Get default mental health resources for Kenya"""
        
        crisis_hotlines = [
            CrisisResource(
                name="Kenya Red Cross Crisis Line",
                contact="1199",
                description="24/7 crisis support and emergency response",
                type=ResourceType.CRISIS_HOTLINE,
                available_24_7=True,
                languages=["en", "sw"],
                location="Nationwide"
            ),
            CrisisResource(
                name="Befrienders Kenya",
                contact="+254 722 178 177",
                description="Suicide prevention and emotional support",
                type=ResourceType.CRISIS_HOTLINE,
                available_24_7=True,
                languages=["en", "sw"]
            ),
            CrisisResource(
                name="Kenya Association of Professional Counsellors",
                contact="+254 20 2729970",
                description="Professional counselling referrals",
                type=ResourceType.CRISIS_HOTLINE,
                available_24_7=False,
                languages=["en", "sw"]
            )
        ]
        
        professional_help = [
            CrisisResource(
                name="Mathari National Teaching & Referral Hospital",
                contact="+254 20 2723841",
                description="National mental health hospital",
                type=ResourceType.PROFESSIONAL_HELP,
                available_24_7=True,
                languages=["en", "sw"],
                location="Nairobi"
            ),
            CrisisResource(
                name="Nairobi Hospital - Mental Health Unit",
                contact="+254 719 055555",
                description="Private hospital mental health services",
                type=ResourceType.PROFESSIONAL_HELP,
                available_24_7=True,
                languages=["en", "sw"],
                location="Nairobi"
            ),
            CrisisResource(
                name="Aga Khan Hospital - Psychiatry Department",
                contact="+254 20 3662000",
                description="Private psychiatric services",
                type=ResourceType.PROFESSIONAL_HELP,
                available_24_7=False,
                languages=["en", "sw"],
                location="Nairobi"
            ),
            CrisisResource(
                name="Moi Teaching and Referral Hospital",
                contact="+254 53 2033471",
                description="Mental health services in Western Kenya",
                type=ResourceType.PROFESSIONAL_HELP,
                available_24_7=True,
                languages=["en", "sw"],
                location="Eldoret"
            )
        ]
        
        online_resources = [
            CrisisResource(
                name="Mental Health Kenya",
                contact="mentalhealthkenya.org",
                description="Online mental health resources and information",
                type=ResourceType.ONLINE_RESOURCE,
                available_24_7=True,
                languages=["en", "sw"]
            ),
            CrisisResource(
                name="Kenya Association of Professional Counsellors",
                contact="kapc.or.ke",
                description="Professional counsellor directory",
                type=ResourceType.ONLINE_RESOURCE,
                available_24_7=True,
                languages=["en"]
            ),
            CrisisResource(
                name="Shang Ring Mental Health",
                contact="shangring.org",
                description="Mental health awareness and support",
                type=ResourceType.ONLINE_RESOURCE,
                available_24_7=True,
                languages=["en", "sw"]
            )
        ]
        
        emergency_services = [
            CrisisResource(
                name="Police Emergency",
                contact="999",
                description="Police emergency services",
                type=ResourceType.EMERGENCY_SERVICE,
                available_24_7=True,
                languages=["en", "sw"],
                location="Nationwide"
            ),
            CrisisResource(
                name="Medical Emergency",
                contact="999",
                description="Medical emergency services",
                type=ResourceType.EMERGENCY_SERVICE,
                available_24_7=True,
                languages=["en", "sw"],
                location="Nationwide"
            )
        ]
        
        return cls(
            crisis_hotlines=crisis_hotlines,
            professional_help=professional_help,
            online_resources=online_resources,
            emergency_services=emergency_services
        )
    
    def get_crisis_contacts(self) -> List[str]:
        """Get formatted crisis contact strings"""
        contacts = []
        for resource in self.crisis_hotlines:
            emoji = "📞" if resource.type == ResourceType.CRISIS_HOTLINE else "🏥"
            availability = " (24/7)" if resource.available_24_7 else ""
            contacts.append(f"{emoji} {resource.name}: {resource.contact}{availability}")
        return contacts
    
    def get_all_resources_count(self) -> int:
        """Get total count of all resources"""
        return (
            len(self.crisis_hotlines) +
            len(self.professional_help) +
            len(self.online_resources) +
            len(self.emergency_services)
        )
