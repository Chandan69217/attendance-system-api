from fastapi import APIRouter,status,Depends,Body
from app.core.security import verify_token
from app.core.response import error_response,success_response
from app.schemas.setting_schema import CreateSettingSchema,UpdateSettingSchema
from app.schemas.user_schema import Role
from app.firebase.firebase_init import db




router = APIRouter()


@router.put("/save", status_code=status.HTTP_200_OK)
def saveSettings(
    query: UpdateSettingSchema = Body(default=None),
    current_user: dict = Depends(verify_token)
):

    role = current_user.get("role")

    if role != Role.admin:
        return error_response(
            message="Only admin can change the settings"
        )

    settings_ref = db.collection("settings").document("global")
    settings_doc = settings_ref.get()

   
    if not settings_doc.exists:

        default_settings = CreateSettingSchema().model_dump()

        if query:
            update_data = query.model_dump(
                exclude_unset=True,
                exclude_none=True
            )
            default_settings.update(update_data)

        settings_ref.set(default_settings)

        return success_response(
            message="Settings created successfully",
            data=default_settings
        )

    if not query:
        return success_response(
            message="Changes saved successfully"
        )

    update_data = query.model_dump(
        exclude_unset=True,
        exclude_none=True
    )

    if not update_data:
        return error_response(
            message="Changes saved successfully"
        )

    settings_ref.update(update_data)

    return success_response(
        message="Settings updated successfully",
        data=update_data
    )




@router.get("/", status_code=status.HTTP_200_OK)
def getSettings(current_user: dict = Depends(verify_token)):

    user_role = current_user.get("role")

    if user_role != Role.admin:
        return error_response(
            message="Only admin can get settings"
        )

    settings_ref = db.collection("settings").document("global")
    settings_doc = settings_ref.get()

    if not settings_doc.exists:

        default_settings = CreateSettingSchema().model_dump()

        settings_ref.set(default_settings)

        return success_response(
            message="Settings fetched successfully",
            data=default_settings
        )

    settings_data = settings_doc.to_dict()

    return success_response(
        message="Settings fetched successfully",
        data=settings_data
    )



from pydantic import BaseModel, Field
from typing import List
from datetime import date
from enum import Enum


# 🔹 Attendance Mode Enum
class AttendanceMode(str, Enum):
    manual = "manual"
    face_recognition = "face_recognition"
    hybrid = "hybrid"


# 🔹 Notification Level Enum
class NotificationLevel(str, Enum):
    all = "all"
    important = "important"
    none = "none"


class GlobalSettingSchema(BaseModel):

    # ========================
    # 🔹 Attendance Settings
    # ========================

    attendance_mode: AttendanceMode = AttendanceMode.face_recognition
    confidence_threshold: int = Field(default=85, ge=0, le=100)
    late_threshold: int = Field(default=15, ge=0)
    max_check_in_distance: int = Field(default=100, ge=0)

    allow_student_self_attendance: bool = True
    require_faculty_verification: bool = True


    # ========================
    # 🔹 Notification Settings
    # ========================

    notification_level: NotificationLevel = NotificationLevel.all
    send_absent_notifications: bool = True
    email_notifications: bool = True
    low_attendance_alerts: bool = True
    daily_reports: bool = False


    # ========================
    # 🔹 Attendance Rule
    # ========================

    min_attendance_percent: int = Field(default=75, ge=0, le=100)


    # ========================
    # 🔹 Semester Configuration
    # ========================

    semester_start: date
    semester_end: date
    holidays: List[date] = []


    # ========================
    # 🔹 Location Settings
    # ========================

    latitude: float = 0.0
    longitude: float = 0.0
    geo_fencing_enabled: bool = False


    # ========================
    # 🔹 System Metadata
    # ========================

    version: int = 1
    last_updated_by: str | None = None
