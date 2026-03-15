from fastapi import APIRouter, Depends, status
from typing import Optional
from datetime import datetime
from app.firebase.firebase_init import db
from app.core.response import success_response, error_response
from app.core.security import verify_token
from app.schemas.attendance_schema import AttendanceVerificationRequest
from app.schemas.user_schema import Role
from collections import defaultdict
from google.cloud.firestore_v1 import FieldFilter

router = APIRouter()


@router.get("/faculty-attendance", status_code=status.HTTP_200_OK)
def get_faculty_attendance(
    faculty_id: Optional[str] = None,
    date: Optional[str] = None,   
    current_user: dict = Depends(verify_token)
):
    """
    Get all faculty attendance
    OR filter by faculty_id
    OR filter by date
    """

    try:
        collection = db.collection("faculty_attendances")
        query = collection

       
        if faculty_id:
            query = query.where("faculty_id", "==", faculty_id)

        if date:
            query = query.where("date", "==", date)

        docs = query.stream()

        attendances = []

        for doc in docs:
            data = doc.to_dict()

          
            if data.get("check_in"):
                data["check_in"] = data["check_in"]

            if data.get("check_out"):
                data["check_out"] = data["check_out"]

            if data.get("created_at"):
                data["created_at"] = data["created_at"].isoformat()

            if data.get("updated_at"):
                data["updated_at"] = data["updated_at"].isoformat()

            attendances.append(data)

        attendances.sort(
            key=lambda x: x.get("created_at", ""),
            reverse=True
        )

        return success_response(
            message="Faculty attendance fetched successfully",
            data=attendances
        )

    except Exception as e:
        return error_response(
            message=f"Failed to fetch attendance: {str(e)}"
        )


@router.get("/student-attendance", status_code=status.HTTP_200_OK)
def get_student_attendance(
    student_id: Optional[str] = None,
    date: Optional[str] = None,   
    current_user: dict = Depends(verify_token)
):

    try:
        collection = db.collection("student_attendances")
        query = collection

        if student_id:
            query = query.where("student_id", "==", student_id)

        if date:
            query = query.where("date", "==", date)

        docs = query.stream()

        attendances = []

        for doc in docs:
            data = doc.to_dict()

            if data.get("created_at"):
                data["created_at"] = data["created_at"].isoformat()

            if data.get("updated_at"):
                data["updated_at"] = data["updated_at"].isoformat()

            attendances.append(data)

        attendances.sort(
            key=lambda x: x.get("created_at", ""),
            reverse=True
        )

        return success_response(
            message="Student attendance fetched successfully",
            data=attendances
        )

    except Exception as e:
        return error_response(
            message=f"Failed to fetch attendance: {str(e)}"
        )




@router.post("/verify/{id}",status_code=status.HTTP_200_OK)
def verifyFacultyAttendance(id:str,payload : AttendanceVerificationRequest,current_user:dict = Depends(verify_token)):
    
    role = current_user.get('role')
    name = current_user.get('name')
    current_user_id  = current_user.get('id')

    if role != Role.admin.value:
        return error_response(
            message="Only admin can verify attendance"
        )
    
    attentRecordRef = db.collection("faculty_attendances").document(id)

    attentRecord = attentRecordRef.get()

    if not  attentRecord.exists:
        return error_response(
            message="Attendance record not found"
        )
    
    attentRecordRef.update({
        "verification_status" : payload.status.value,
        "verify_by_id":current_user_id,
        "verify_by_name": name
    })

    
    updated_data = attentRecordRef.get()

    if not updated_data.exists:
        return error_response(message="something went wrong")
    
    return success_response(
        message="successfully verified",
        data=updated_data.to_dict()
    )





@router.get("/student/subject-attendance")
def get_subject_attendance(current_user: dict = Depends(verify_token)):

    student_id = current_user.get("id")

    attendance_docs = db.collection("student_attendances") \
        .where("student_id", "==", student_id) \
        .stream()

    subject_data = defaultdict(lambda: {
        "subject": "",
        "total": 0,
        "present": 0
    })

    for doc in attendance_docs:
        data = doc.to_dict()
        subject_id = data.get("subject_id")
        subject_name = data.get("subject_name")
        status = data.get("status")

        subject_data[subject_id]["subject"] = subject_name
        subject_data[subject_id]["total"] += 1

        if status in ["present", "late"]:
            subject_data[subject_id]["present"] += 1

    result = []

    for subject in subject_data.values():
        percentage = round(
            (subject["present"] / subject["total"]) * 100
        ) if subject["total"] > 0 else 0

        result.append({
            "subject": subject["subject"],
            "percentage": percentage
        })

    return success_response(
        message="Subject by attendance fetched successfully",
        data= result
    )




@router.get("/class-attendance", status_code=status.HTTP_200_OK)
def get_class_attendance(
    date: Optional[str] = None,
    current_user: dict = Depends(verify_token)
):
    try:
        user_id = current_user.get("id")
        role = current_user.get("role")

       
        if role != Role.faculty.value:
            return error_response(
                message="Only faculty can access the class record"
            )

        
        faculty_doc = db.collection("users").document(user_id).get()

        if not faculty_doc.exists:
            return error_response(message="Faculty not found")

        faculty_data = faculty_doc.to_dict()
        subject_id = faculty_data.get("subject_id")

        if not subject_id:
            return error_response(message="Faculty subject not found")

      
        query = db.collection("student_attendances") \
                  .where(filter=FieldFilter("subject_id", "==", subject_id))

        if date:
            query = query.where("date", "==", date)

        docs = query.stream()

        attendances = []

        for doc in docs:
            data = doc.to_dict()

            if data.get("created_at"):
                data["created_at"] = data["created_at"].isoformat()

            if data.get("updated_at"):
                data["updated_at"] = data["updated_at"].isoformat()

            attendances.append(data)

        attendances.sort(
            key=lambda x: x.get("created_at", ""),
            reverse=True
        )

        return success_response(
            message="Class attendance fetched successfully",
            data=attendances
        )

    except Exception as e:
        return error_response(
            message=f"Failed to fetch class attendance: {str(e)}"
        )