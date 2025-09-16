from datetime import datetime
from typing import Optional, List
from pydantic import Field
from .base import BaseDocument


class User(BaseDocument):
    telegram_id: int = Field(..., description="Telegram user ID")
    username: Optional[str] = Field(None, description="Telegram username")
    first_name: str = Field(..., description="User's first name")
    last_name: Optional[str] = Field(None, description="User's last name")
    display_name: str = Field(..., description="How to address the user")
    phone: Optional[str] = Field(None, description="User's phone number")
    language_code: Optional[str] = Field("ru", description="User's language preference")
    
    # User status and permissions
    is_admin: bool = Field(False, description="Is user an admin")
    is_super_admin: bool = Field(False, description="Is user a super admin")
    is_blocked: bool = Field(False, description="Is user blocked")
    
    # User activity tracking
    last_activity: Optional[datetime] = Field(None, description="Last activity timestamp")
    registration_completed: bool = Field(False, description="Has user completed registration")
    phone_shared: bool = Field(False, description="Has user shared phone number")
    
    # User preferences
    preferred_districts: List[str] = Field(default_factory=list, description="User's preferred districts")
    preferred_sports: List[str] = Field(default_factory=list, description="User's preferred sports")
    
    # Statistics
    total_applications: int = Field(0, description="Total number of applications made")
    
    class Config:
        collection = "users"

    @property
    def full_name(self) -> str:
        """Get user's full name"""
        if self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name

    @property
    def can_make_applications(self) -> bool:
        """Check if user can make applications (has shared phone)"""
        return self.phone_shared and self.phone is not None

    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = datetime.utcnow()
        return self