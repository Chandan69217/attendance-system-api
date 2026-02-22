from fastapi import APIRouter, status, Depends
from datetime import datetime,timezone
from app.firebase.firebase_init import db
from app.core.response import success_response, error_response
from app.core.security import verify_token
from app.lib.utils import generate_subject_id
from collections import defaultdict
from app.schemas.user_schema import Role
from app.schemas.subject_schema import CreateSubjectSchema,UpdateSubjectSchema
from app.routes.department.department_routes import get_department
from app.routes.user.user_routes import get_users
from google.cloud.firestore_v1 import FieldFilter

router = APIRouter()


def format_to_12_hour(time_24: str) -> str:
    try:
        time_obj = datetime.strptime(time_24, "%H:%M")
        return time_obj.strftime("%I:%M %p").lstrip("0")
    except (ValueError, TypeError):
        return time_24  


@router.post("/create", status_code=status.HTTP_201_CREATED)
def create_subject(
    payload: CreateSubjectSchema,
    current_user: dict = Depends(verify_token)
):

    if current_user.get("role") != Role.admin:
        return error_response(
            message="Only admin can create the subject"
        )

    generate_id = generate_subject_id()


    subject_ref = db.collection("subjects").document(generate_id)

    if subject_ref.get().exists:
        return error_response(message="Subject ID already exists")


    if not payload.dept_id:
        return error_response(
            message="Department id is required"
        )
    
    
    department_ref = db.collection("departments").document(payload.dept_id)
    department_doc = department_ref.get()

    if not department_doc.exists:
        return error_response(message="Department not found")

    department_data = department_doc.to_dict()



    if not payload.class_id:
        return error_response(
            message="Class id is required"
        )
    
    
    class_ref = db.collection("classes").document(payload.class_id)
    class_doc = class_ref.get()

    if not class_doc.exists:
        return error_response(message="Class not found")

    class_data = class_doc.to_dict()

    


    subject_ref.set({
        "id": generate_id,
        "name": payload.name,
        "dept_id": payload.dept_id,
        "dept_name": department_data.get("name"),
        "class_id" : payload.class_id,
        "class_name" : class_data.get('name'),
        "start_time" :payload.start_time,
        "end_time" : payload.end_time,
        "faculty_count": 0,
        "created_at": datetime.now(timezone.utc)
    })  

    return success_response(
        message="Subject created successfully",
        data=payload.model_dump()
    )


@router.get("/get-subject", status_code=status.HTTP_200_OK)
def get_subjects(
    id: str | None = None,
    dept_id:str | None = None,
    current_user: dict = Depends(verify_token)
):



    collection = db.collection("subjects")
    users = db.collection("users") \
    .where(filter=FieldFilter("role", "==", "faculty")) \
    .select(["subject_id"]) \
    .stream()



    user_map = defaultdict(int)

    for user in users:
        data = user.to_dict()
        subject_id = data.get("subject_id")

        if subject_id:
            user_map[subject_id] += 1
        

    if id:
        subject_ref = collection.document(id.upper())
        subject_doc = subject_ref.get()

        if not subject_doc.exists:
            return error_response(message="Subject not found")

        subject_data = subject_doc.to_dict()
        subject_data["faculty_count"] = user_map.get(subject_data.get("id"), 0)


        return success_response(
            message="Subject fetched successfully",
            data=[subject_data]
        )

    subjects = []

    for doc in collection.stream():
        data = doc.to_dict()
        data['faculty_count'] = user_map.get(data['id'], 0)
        subjects.append(data)

    if dept_id: 
        filtered_subjects = [
            s for s in subjects if s.get("dept_id").lower() == dept_id.lower()
        ]
        filtered_subjects.reverse()
        return success_response(
        message="subjects fetched successfully",
        data=filtered_subjects
    )
    else:
        subjects.reverse()
        return success_response(
        message="subjects fetc successfully",
        data=subjects
        )

    




@router.put("/update/{id}", status_code=status.HTTP_200_OK)
def update_subject(
    id: str,
    payload: UpdateSubjectSchema,
    current_user: dict = Depends(verify_token)
):


    if current_user.get("role") != Role.admin:
        return error_response(
            message="Only admin can update the subject"
        )

    subject_ref = db.collection("subjects").document(id.upper())
    subject_doc = subject_ref.get()

    if not subject_doc.exists:
        return error_response(message="Subject not found")

    update_data = payload.model_dump(
        exclude_unset=True,
        exclude_none=True
    )

    if not update_data:
        return error_response(
            message="no parameter founds to be update"
        )

    if "dept_id" in update_data:

        department = db.collection("departments").document(update_data["dept_id"]).get()

        if not department.exists:
            return error_response(message="Department not found")

        update_data["dept_name"] = department.get("name")
    else:
        return error_response(message="Department id required")
    


    if "class_id" in update_data:

        classes = db.collection("classes").document(update_data["class_id"]).get()

        if not classes.exists:
            return error_response(message="Class not found")

        update_data["class_name"] = classes.get("name")
    else:
        return error_response(message="Class id required")
    

    if  not "start_time" in update_data:
        return error_response(message="start time is required")
    
    if not "end_time" in update_data:
        return error_response(message="end time is required")

    update_data["updated_at"] = datetime.now(timezone.utc)

    subject_ref.update(update_data)

    return success_response(
        message="Subject updated successfully",
        data=update_data
    )


@router.delete("/delete/{id}", status_code=status.HTTP_200_OK)
def delete_subject(
    id: str,
    current_user: dict = Depends(verify_token)
):
    subject_ref = db.collection("subjects").document(id.upper())
    subject_doc = subject_ref.get()

    if not subject_doc.exists:
        return error_response(message="subject not found")

    subject_ref.delete()

    return success_response(
        message="subject deleted successfully"
    )
