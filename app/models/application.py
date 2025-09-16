from datetime import datetime
from typing import Optional
from enum import Enum
from pydantic import Field
from .base import BaseDocument, PyObjectId


class ApplicationStatus(str, Enum):
    PENDING = "pending"  # Подана
    ACCEPTED = "accepted"  # Принята
    TRANSFERRED = "transferred"  # Передана
    COMPLETED = "completed"  # Выполнена
    CANCELLED = "cancelled"  # Отменена
    REJECTED = "rejected"  # Отклонена


class Application(BaseDocument):
    user_id: PyObjectId = Field(..., description="User ID who made the application")
    fok_id: PyObjectId = Field(..., description="FOK ID for the application")
    
    # User information at time of application
    user_name: str = Field(..., description="User's name at time of application")
    user_phone: str = Field(..., description="User's phone at time of application")
    user_telegram_id: int = Field(..., description="User's Telegram ID")
    
    # FOK information at time of application
    fok_name: str = Field(..., description="FOK name at time of application")
    fok_district: str = Field(..., description="FOK district at time of application")
    fok_address: str = Field(..., description="FOK address at time of application")
    
    # Application details
    status: ApplicationStatus = Field(ApplicationStatus.PENDING, description="Application status")
    message: Optional[str] = Field(None, description="Additional message from user")
    admin_notes: Optional[str] = Field(None, description="Admin notes")
    
    # Timestamps
    status_updated_at: Optional[datetime] = Field(None, description="When status was last updated")
    completed_at: Optional[datetime] = Field(None, description="When application was completed")
    cancelled_at: Optional[datetime] = Field(None, description="When application was cancelled")
    
    # Administrative
    processed_by: Optional[PyObjectId] = Field(None, description="Admin who processed the application")
    priority: int = Field(0, description="Application priority (higher = more priority)")
    
    class Config:
        collection = "applications"

    @property
    def status_display(self) -> str:
        """Get localized status display"""
        status_map = {
            ApplicationStatus.PENDING: "⏳ Ожидает обработки",
            ApplicationStatus.ACCEPTED: "✅ Принята",
            ApplicationStatus.TRANSFERRED: "📤 Передана в учреждение",
            ApplicationStatus.COMPLETED: "🎉 Выполнена",
            ApplicationStatus.CANCELLED: "❌ Отменена",
            ApplicationStatus.REJECTED: "🚫 Отклонена"
        }
        return status_map.get(self.status, str(self.status))

    @property
    def can_be_cancelled(self) -> bool:
        """Check if application can be cancelled by user"""
        return self.status in [ApplicationStatus.PENDING, ApplicationStatus.ACCEPTED]

    def update_status(self, new_status: ApplicationStatus, processed_by: Optional[PyObjectId] = None, notes: Optional[str] = None):
        """Update application status"""
        self.status = new_status
        self.status_updated_at = datetime.utcnow()
        self.update_timestamp()
        
        if processed_by:
            self.processed_by = processed_by
        
        if notes:
            self.admin_notes = notes
        
        if new_status == ApplicationStatus.COMPLETED:
            self.completed_at = datetime.utcnow()
        elif new_status == ApplicationStatus.CANCELLED:
            self.cancelled_at = datetime.utcnow()
        
        return self

    def get_card_text(self) -> str:
        """Get formatted card text for display"""
        text_parts = [
            f"📋 <b>Заявка #{str(self.id)[-6:]}</b>",
            f"👤 <b>Заявитель:</b> {self.user_name}",
            f"📞 <b>Телефон:</b> {self.user_phone}",
            "",
            f"🏢 <b>ФОК:</b> {self.fok_name}",
            f"📍 <b>Район:</b> {self.fok_district}",
            f"🏠 <b>Адрес:</b> {self.fok_address}",
            "",
            f"📊 <b>Статус:</b> {self.status_display}",
            f"📅 <b>Подана:</b> {self.created_at.strftime('%d.%m.%Y %H:%M')}"
        ]
        
        if self.message:
            text_parts.append(f"💬 <b>Сообщение:</b> {self.message}")
        
        if self.admin_notes:
            text_parts.append(f"📝 <b>Примечания:</b> {self.admin_notes}")
        
        if self.status_updated_at and self.status != ApplicationStatus.PENDING:
            text_parts.append(f"🔄 <b>Обновлено:</b> {self.status_updated_at.strftime('%d.%m.%Y %H:%M')}")
        
        return "\n".join(text_parts)

    def get_short_display(self) -> str:
        """Get short display for lists"""
        return f"{self.fok_name} - {self.status_display}"

    @classmethod
    def get_collection_name(cls) -> str:
        return "applications"