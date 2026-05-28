from pydantic import BaseModel
from typing import Optional

class AssignmentSchema(BaseModel):
    title: str
    subject: str
    dueDate: str
    description: str
    status: str = "pending"
    createdBy: str
    class_id: Optional[str] = "all"
