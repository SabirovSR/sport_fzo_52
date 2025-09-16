from typing import Optional
from pydantic import Field
from .base import BaseDocument


class District(BaseDocument):
    name: str = Field(..., description="District name", max_length=100)
    description: Optional[str] = Field(None, description="District description", max_length=500)
    sort_order: int = Field(0, description="Sort order for display")
    
    class Config:
        collection = "districts"

    def __str__(self):
        return self.name

    @classmethod
    def get_collection_name(cls) -> str:
        return "districts"