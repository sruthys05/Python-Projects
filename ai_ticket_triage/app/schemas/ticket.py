from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TicketCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1)


class TicketResponse(BaseModel):
    id: int
    title: str
    description: str
    category: str
    priority: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
