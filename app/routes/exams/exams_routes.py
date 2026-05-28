from fastapi import APIRouter, Depends, HTTPException
from app.firebase.firebase_init import db
from app.core.security import verify_token
from app.schemas.exam_schema import ExamSchema
from app.core.response import success_response, error_response
import uuid

router = APIRouter()

@router.post("/create")
def create_exam(exam: ExamSchema, current_user: dict = Depends(verify_token)):
    if current_user.get("role") not in ["admin", "faculty"]:
        return error_response(message="Unauthorized to create exams")

    exam_id = f"E{str(uuid.uuid4())[:8]}"
    exam_data = exam.model_dump()
    exam_data["id"] = exam_id
    exam_data["created_by"] = current_user.get("id")

    db.collection("exams").document(exam_id).set(exam_data)
    
    return success_response(message="Exam scheduled successfully", data=exam_data)

@router.get("/get")
def get_exams(current_user: dict = Depends(verify_token)):
    exams_ref = db.collection("exams").stream()
    exams = []
    for doc in exams_ref:
        exams.append(doc.to_dict())
        
    return success_response(message="Exams retrieved", data=exams)
