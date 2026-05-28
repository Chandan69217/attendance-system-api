from pydantic import BaseModel
from typing import Optional

class ExamSchema(BaseModel):
    subject: str
    date: str
    time: str
    venue: str
    type: str
    class_id: Optional[str] = "all"
