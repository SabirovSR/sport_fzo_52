from typing import List, Optional, Dict, Any
from pydantic import Field, validator
from .base import BaseDocument


class FOKContact(BaseDocument):
    contact_type: str = Field(..., description="Contact type (phone, email, website)")
    value: str = Field(..., description="Contact value")
    description: Optional[str] = Field(None, description="Contact description")
    is_primary: bool = Field(False, description="Is this a primary contact")


class FOK(BaseDocument):
    name: str = Field(..., description="FOK name", max_length=200)
    district: str = Field(..., description="District name")
    address: str = Field(..., description="FOK address", max_length=300)
    description: Optional[str] = Field(None, description="FOK description", max_length=1000)
    
    # Sports available at this FOK
    sports: List[str] = Field(default_factory=list, description="Available sports")
    
    # Contact information
    contacts: List[Dict[str, Any]] = Field(default_factory=list, description="Contact information")
    
    # Additional information
    working_hours: Optional[str] = Field(None, description="Working hours", max_length=200)
    website: Optional[str] = Field(None, description="Website URL")
    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Primary phone number")
    
    # Geolocation (for future features)
    latitude: Optional[float] = Field(None, description="Latitude coordinate")
    longitude: Optional[float] = Field(None, description="Longitude coordinate")
    
    # Metadata
    capacity: Optional[int] = Field(None, description="Capacity of the facility")
    rating: Optional[float] = Field(None, description="Average rating", ge=0, le=5)
    total_applications: int = Field(0, description="Total number of applications")
    
    # Administrative
    sort_order: int = Field(0, description="Sort order for display")
    featured: bool = Field(False, description="Is this FOK featured")
    
    class Config:
        collection = "foks"

    @validator('sports')
    def validate_sports(cls, v):
        """Ensure sports list is not empty and contains valid sports"""
        if not v:
            return []
        return [sport.strip() for sport in v if sport.strip()]

    @validator('contacts')
    def validate_contacts(cls, v):
        """Validate contact information structure"""
        if not v:
            return []
        
        valid_contacts = []
        for contact in v:
            if isinstance(contact, dict) and 'type' in contact and 'value' in contact:
                valid_contacts.append(contact)
        return valid_contacts

    @property
    def sports_display(self) -> str:
        """Get formatted sports list for display"""
        if not self.sports:
            return "Не указано"
        return ", ".join(self.sports)

    @property
    def contacts_display(self) -> str:
        """Get formatted contacts for display"""
        if not self.contacts:
            return "Не указано"
        
        contact_lines = []
        for contact in self.contacts:
            contact_type = contact.get('type', '').capitalize()
            contact_value = contact.get('value', '')
            if contact_type and contact_value:
                contact_lines.append(f"{contact_type}: {contact_value}")
        
        return "\n".join(contact_lines) if contact_lines else "Не указано"

    def add_contact(self, contact_type: str, value: str, description: Optional[str] = None, is_primary: bool = False):
        """Add contact information"""
        contact = {
            'type': contact_type,
            'value': value,
            'description': description,
            'is_primary': is_primary
        }
        self.contacts.append(contact)
        return self

    def get_card_text(self) -> str:
        """Get formatted card text for display"""
        text_parts = [
            f"🏢 <b>{self.name}</b>",
            f"📍 <b>Район:</b> {self.district}",
            f"🏠 <b>Адрес:</b> {self.address}",
            f"⚽ <b>Виды спорта:</b> {self.sports_display}"
        ]
        
        if self.contacts_display != "Не указано":
            text_parts.append(f"📞 <b>Контакты:</b>\n{self.contacts_display}")
        
        if self.description:
            text_parts.append(f"📝 <b>Описание:</b> {self.description}")
        
        if self.working_hours:
            text_parts.append(f"🕐 <b>Режим работы:</b> {self.working_hours}")
        
        return "\n\n".join(text_parts)

    @classmethod
    def get_collection_name(cls) -> str:
        return "foks"