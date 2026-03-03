from fastapi import APIRouter,status,Depends
from app.core.security import verify_token
from app.firebase.firebase_init import db
from app.core.response import success_response,error_response
from app.schemas.user_schema import Role
from collections import defaultdict
from datetime import datetime,timezone
from zoneinfo import ZoneInfo
from google.cloud.firestore_v1 import FieldFilter,Query
from app.schemas.attendance_schema import AttendanceStatusSchema

router = APIRouter()


@router.get('/dashboard-stats', status_code=status.HTTP_200_OK)
def getDashboardStatsCount(current_user: dict = Depends(verify_token)):

    today = datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%d-%m-%Y")

    user_role = current_user.get('role')

    if user_role != Role.admin:
        return error_response(
            message="Only Admin can access this stats"
        )

    student_count_query = (
        db.collection('users')
        .where(filter=FieldFilter("role", "==", Role.student))
        .count()
        .get()
    )

    faculty_count_query = (
        db.collection('users')
        .where(filter=FieldFilter("role", "==", Role.faculty))
        .count()
        .get()
    )

    student_count = student_count_query[0][0].value if student_count_query else 0
    faculty_count = faculty_count_query[0][0].value if faculty_count_query else 0


    todayTotalAttendance = 0
    todayPresentAttendance = 0

    
    student_attendance = (
        db.collection('student_attendances')
        .where(filter=FieldFilter("date", "==", today))
        .stream()
    )

    for attend in student_attendance:
        attendance = attend.to_dict()
        todayTotalAttendance += 1

        if attendance.get("status") == AttendanceStatusSchema.present.value:
            todayPresentAttendance += 1


    faculty_attendance = (
        db.collection('faculty_attendances')
        .where(filter=FieldFilter("date", "==", today))
        .stream()
    )

    for attend in faculty_attendance:
        attendance = attend.to_dict()
        todayTotalAttendance += 1

        if attendance.get("status") in [
            AttendanceStatusSchema.present.value,
            AttendanceStatusSchema.late.value
        ]:
            todayPresentAttendance += 1

    if todayTotalAttendance > 0:
        todayPercentage = round(
            (todayPresentAttendance * 100) / todayTotalAttendance, 2
        )
    else:
        todayPercentage = 0

    pending_verification_query = (
        db.collection('faculty_attendances')
        .where(filter=FieldFilter("verification_status", "==", "pending"))
        .count()
        .get()
    )

    pending_verification = (
        pending_verification_query[0][0].value
        if pending_verification_query
        else 0
    )

    data = {
        "student_count": student_count,
        "faculty_count": faculty_count,
        "today_attendance_percentage": todayPercentage,
        "pending_verification": pending_verification
    }

    return success_response(
        message="Stats fetched successfully",
        data=data
    )





@router.get("/recent-faculty-attendance", status_code=status.HTTP_200_OK)
def get_recent_faculty_attendance(
    limit: int = 8,
    current_user: dict = Depends(verify_token)
):
   
    if current_user.get("role") != Role.admin:
        return error_response(
            message="Only Admin can access recent faculty attendance"
        )

    faculty_attendance_docs = (
        db.collection("faculty_attendances")
        .order_by("created_at", direction=Query.DESCENDING)
        .limit(limit)
        .stream()
    )

    recent_attendance = []

    for doc in faculty_attendance_docs:
        data = doc.to_dict()
        data["id"] = doc.id
        recent_attendance.append(data)

    return success_response(
        message="Recent faculty attendance fetched successfully",
        data=recent_attendance
    )
