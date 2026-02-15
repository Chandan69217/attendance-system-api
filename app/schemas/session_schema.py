from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum
from datetime import date


class SessionStatus(str, Enum):
    active = "active"
    upcoming = "upcoming"
    completed = "completed"


class CreateSessionSchema(BaseModel):
    id: Optional[str] = None
    name: str
    start_date: date
    end_date: date
    status: Optional[SessionStatus] = SessionStatus.active


class UpdateSessionSchema(BaseModel):
    name: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[SessionStatus] = None
