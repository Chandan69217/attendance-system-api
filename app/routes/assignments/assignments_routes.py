from fastapi import APIRouter, Depends, HTTPException
from app.firebase.firebase_init import db
from app.core.security import verify_token
from app.schemas.assignment_schema import AssignmentSchema
from app.core.response import success_response, error_response
import uuid

router = APIRouter()

@router.post("/create")
def create_assignment(assignment: AssignmentSchema, current_user: dict = Depends(verify_token)):
    if current_user.get("role") not in ["admin", "faculty"]:
        return error_response(message="Unauthorized to create assignments")

    assignment_id = f"AS{str(uuid.uuid4())[:8]}"
    assign_data = assignment.model_dump()
    assign_data["id"] = assignment_id
    assign_data["createdBy"] = current_user.get("id")

    db.collection("assignments").document(assignment_id).set(assign_data)
    
    return success_response(message="Assignment created successfully", data=assign_data)

@router.get("/get")
def get_assignments(current_user: dict = Depends(verify_token)):
    assign_ref = db.collection("assignments").stream()
    assignments = []
    for doc in assign_ref:
        assignments.append(doc.to_dict())
        
    return success_response(message="Assignments retrieved", data=assignments)
