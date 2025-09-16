from typing import Optional
from pydantic import Field
from .base import BaseDocument


class Sport(BaseDocument):
    name: str = Field(..., description="Sport name", max_length=100)
    description: Optional[str] = Field(None, description="Sport description", max_length=500)
    icon: Optional[str] = Field(None, description="Sport icon emoji", max_length=10)
    sort_order: int = Field(0, description="Sort order for display")
    
    class Config:
        collection = "sports"

    def __str__(self):
        return self.name

    @property
    def display_name(self) -> str:
        """Get display name with icon if available"""
        if self.icon:
            return f"{self.icon} {self.name}"
        return self.name

    @classmethod
    def get_collection_name(cls) -> str:
        return "sports"