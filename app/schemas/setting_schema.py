from pydantic import BaseModel
from typing import List,Optional
from enum import Enum


class CreateSettingSchema(BaseModel):
    confidence_threshold: int = 85
    late_threshold: int = 15
    max_check_in_distance: int = 100
    allow_student_self_attendance: bool = True
    require_faculty_verification: bool = True
    send_absent_notifications: bool = True
    email_notifications: bool = True
    low_attendance_alerts: bool = True
    daily_reports: bool = False
    min_attendance_percent: int = 75
    semester_start: str = ""
    semester_end: str = ""
    holidays: List[str] = []
    latitude: float = 0.0
    longitude: float = 0.0
    check_in: str = "10:00 AM"





class UpdateSettingSchema(BaseModel):
    confidence_threshold: Optional[int] = None
    late_threshold: Optional[int] = None
    max_check_in_distance: Optional[int] = None
    allow_student_self_attendance: Optional[bool] = None
    require_faculty_verification: Optional[bool] = None
    send_absent_notifications: Optional[bool] = None
    email_notifications: Optional[bool] = None
    low_attendance_alerts: Optional[bool] = None
    daily_reports: Optional[bool] = None
    min_attendance_percent: Optional[int] = None
    semester_start: Optional[str] = None
    semester_end: Optional[str] = None
    holidays: Optional[List[str]] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    check_in: str = "10:00 AM"



class NotificationLevel(str, Enum):
    all = "all"
    important = "important"
    none = "none"

class AttendanceMode(str, Enum):
    manual = "manual"
    face_recognition = "face_recognition"
    hybrid = "hybrid"



class SettingKey(str, Enum):
    confidence_threshold = "confidence_threshold"
    late_threshold = "late_threshold"
    max_check_in_distance = "max_check_in_distance"

    allow_student_self_attendance = "allow_student_self_attendance"
    require_faculty_verification = "require_faculty_verification"

    send_absent_notifications = "send_absent_notifications"
    email_notifications = "email_notifications"
    low_attendance_alerts = "low_attendance_alerts"
    daily_reports = "daily_reports"

    min_attendance_percent = "min_attendance_percent"

    semester_start = "semester_start"
    semester_end = "semester_end"

    holidays = "holidays"

    latitude = "latitude"
    longitude = "longitude"
    check_in = "check_in"
