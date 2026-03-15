from pydantic import BaseModel
from typing import Optional
from enum import Enum

class NotificationCategory(str,Enum):
    EXAM = "exam" 
    ASSIGNMENT =  "assignment" 
    ANNOUNCEMENT =  "announcement" 
    ATTENDANCE = "attendance"

class NotificationTarget(str, Enum):
    ALLUSER = "all"
    FACULTY = "faculty"
    STUDENT = "student"


class NotificationSchema(BaseModel):
    title: str
    message: str
    category: NotificationCategory
    target: NotificationTarget


class UpdateNotificationSchema(BaseModel):
    is_read: bool