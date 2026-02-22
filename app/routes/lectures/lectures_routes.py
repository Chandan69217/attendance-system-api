from fastapi import APIRouter,Depends,status
from app.core.response import error_response,success_response
from app.core.security import verify_token
from app.firebase.firebase_init import db
from app.schemas.user_schema import Role
from datetime import datetime
from app.lib.utils import generate_lecture_id
from google.cloud.firestore_v1 import FieldFilter
import pytz
from datetime import datetime



router = APIRouter()


@router.post("/start-or-create", status_code=status.HTTP_200_OK)
def start_or_create_lecture(current_user: dict = Depends(verify_token)):

    user_id = current_user.get("id")
    user_role = current_user.get("role")
    user_name = current_user.get("name")

    if user_role != Role.faculty.value:
        return error_response(
            message="Only Faculty can start lecture"
        )


    user_doc = db.collection("users").document(user_id).get()
    if not user_doc.exists:
        return error_response(message="User not found")

    user_data = user_doc.to_dict()
    subject_id = user_data.get("subject_id")

    
    subject_doc = db.collection("subjects").document(subject_id).get()
    if not subject_doc.exists:
        return error_response(message="Subject not found")

    subject_data = subject_doc.to_dict()

 
    ist = pytz.timezone("Asia/Kolkata")
    now = datetime.now(ist)
    date = now.date().isoformat()

  
    existing_query = db.collection("lectures") \
        .where(filter=FieldFilter("faculty_id", "==", user_id)) \
        .where(filter=FieldFilter("date", "==", date)) \
        .stream()

    existing_lectures = list(existing_query)

    if existing_lectures:
        lecture_doc = existing_lectures[0]
        lecture_data = lecture_doc.to_dict()

        
        if lecture_data.get("status") == "active":
            return success_response(
                message="Lecture already active",
                data=lecture_data
            )

    
        db.collection("lectures").document(lecture_doc.id).update({
            "status": "active",
            "started_at": now,
            "updated_at": now
        })

        lecture_data["status"] = "active"
        lecture_data["started_at"] = now

        return success_response(
            message="Lecture restarted successfully",
            data=lecture_data
        )

  
    lecture_id = f"{generate_lecture_id()}_{date}"

    lecture_session = {
        "id": lecture_id,
        "subject_id": subject_id,
        "subject_name": subject_data.get("name"),
        "faculty_id": user_id,
        "faculty_name": user_name,
        "date": date,
        "start_time": subject_data.get("start_time"),
        "end_time": subject_data.get("end_time"),
        "class_id": subject_data.get("class_id"),
        "class_name": subject_data.get("class_name"),
        "status": "active",
        "created_at": now,
    }

    db.collection("lectures").document(lecture_id).set(lecture_session)

    return success_response(
        message="Lecture created and started successfully",
        data=lecture_session
    )




@router.get("/today", status_code=status.HTTP_200_OK)
def get_today_lectures(
    lecture_id: str | None = None,
    faculty_id: str | None = None,
    student_id: str | None = None,
    class_id: str | None = None,
    current_user: dict = Depends(verify_token)
):

    ist = pytz.timezone("Asia/Kolkata")
    today = datetime.now(ist).date().isoformat()


    if lecture_id:
        lecture_doc = db.collection("lectures").document(lecture_id).get()

        if not lecture_doc.exists:
            return error_response(message="Lecture not found")

        return success_response(
            message="Lecture fetched successfully",
            data=lecture_doc.to_dict()
        )


    query = db.collection("lectures") \
        .where(filter=FieldFilter("date", "==", today))

  
    if student_id:
        student_doc = db.collection("users").document(student_id).get()
        if not student_doc.exists:
            return error_response(message="Student not found")

        student_data = student_doc.to_dict()
        class_id = student_data.get("class_id")


    if faculty_id:
        query = query.where(
            filter=FieldFilter("faculty_id", "==", faculty_id)
        )

    if class_id:
        query = query.where(
            filter=FieldFilter("class_id", "==", class_id)
        )

    lectures = query.stream()
    lecture_list = [doc.to_dict() for doc in lectures]

    return success_response(
        message="Lectures fetched successfully",
        data=lecture_list
    )


@router.post("/end/{lecture_id}")
def endLecture(lecture_id: str, current_user: dict = Depends(verify_token)):
    
    lecture_ref = db.collection("lectures").document(lecture_id)

    if not lecture_ref.get().exists:
        return error_response(message="Lecture not found")

    lecture_ref.update({
        "status": "closed",
        "ended_at": datetime.now(pytz.timezone("Asia/Kolkata"))
    })

    return success_response(message="Lecture Ended")

    



    
    




