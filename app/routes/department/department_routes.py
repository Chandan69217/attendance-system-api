from fastapi import APIRouter,status,Depends
from app.schemas.department_schema import Department,UpdateDepartmentSchema
from app.firebase.firebase_init import db
from app.core.security import verify_token
from app.core.response import error_response,success_response
from app.core.custom_exception import HttpsException
from app.schemas.user_schema import Role
from app.lib.utils import generate_dept_id
from datetime import datetime,timezone
from typing import Optional
from app.core.security import verify_token
from collections import defaultdict




router = APIRouter()



@router.post("/create", status_code=status.HTTP_201_CREATED)
def add_department(
    department: Department,
    current_user: dict = Depends(verify_token)
):


    if current_user.get("role") != Role.admin:
        return error_response(
            message="Only admin can create department"
        )

    user_id = current_user.get("id")
    head_id = department.head_id.upper() if department.head_id else None
    head_name = None

    if head_id:
        head_doc = db.collection("users").document(head_id).get()

        if not head_doc.exists:
            return error_response(message="Faculty not found.")

        head_data = head_doc.to_dict()

        if head_data.get("role") != Role.faculty:
            return error_response(
                message="Only faculty can be a head of the department"
            )
        head_name = head_data.get("name")


    dept_id = generate_dept_id()

    new_dept = {
        "id": dept_id,
        "name": department.name.strip(),
        "head_id": head_id,
        "head_name":head_name,
        "student_count": 0,
        "faculty_count": 0,
        "created_by": user_id,
        "created_at": datetime.now(timezone.utc)
    }

    
    db.collection("departments").document(dept_id).set(new_dept)

   
    response_data = {
        "id": dept_id,
        "name": new_dept["name"],
        "head_id": head_id,
        "student_count": 0,
        "faculty_count": 0,
        "created_at": new_dept["created_at"]
    }

    return success_response(
        message="Department created successfully",
        data=response_data
    )

    

     
@router.get("/get-dept", status_code=status.HTTP_200_OK)
def get_department(id: Optional[str] = None, current_user: dict = Depends(verify_token)):

    dept_collection = db.collection("departments")

    users_docs = db.collection("users").stream()

    users = []

    for u in users_docs:
        data = u.to_dict()
        users.append(data)


    student_count = defaultdict(int)
    faculty_count = defaultdict(int)

    for u in users:
        dept_id = u.get("dept_id")
        role = u.get("role")
        if role == "student":
            student_count[dept_id] += 1
        elif role == "faculty":
            faculty_count[dept_id] += 1

    if id:
        doc = dept_collection.document(id.upper()).get()

        if not doc.exists:
            return error_response(message="Department not found")

        dept = doc.to_dict()
        dept_id = dept.get("id")
        dept.update({
            "student_count": student_count.get(dept_id, 0),
            "faculty_count": faculty_count.get(dept_id, 0),
        })

        return success_response(
            message="Department found successfully",
            data=[dept]
        )


    docs = dept_collection.stream()
    depts = []

    for doc in docs:
        dept = doc.to_dict()
        dept_id = dept.get('id')
        dept.update({
            "student_count": student_count.get(dept_id, 0),
            "faculty_count": faculty_count.get(dept_id, 0),
        })

        depts.append(dept)
    depts.reverse()
    return success_response(
        message="All departments fetched successfully",
        data=depts
    )


@router.delete("/delete/{id}")
def delete_department(
    id: str,
    current_user: dict = Depends(verify_token)
):
    try:

        if current_user.get("role") != "admin":
            return error_response(message="Only admin can update department")
         
        department_ref = db.collection("departments").document(id)

        dept_snapshot = department_ref.get()

        if not dept_snapshot.exists:
            return error_response(
                message="Department not found"
            )

        department_ref.delete()

        return success_response(
            message="Department deleted successfully"
        )

    except Exception as e:
        return error_response(
            message=str(e)
        )





@router.put("/update/{id}")
def update_department(
    id: str,
    payload: UpdateDepartmentSchema,
    current_user: dict = Depends(verify_token)
):
    try:
        department_ref = db.collection("departments").document(id)

        dept_snapshot = department_ref.get()

        if not dept_snapshot.exists:
            return error_response(
                message="Department not found"
            )

        if current_user.get("role") != "admin":
            return error_response(message="Only admin can update department")


   
        update_data = payload.model_dump(
                exclude_unset=True,
                exclude_none=True
            )

        if not update_data:
            return error_response(
                message="No fields provided to update"
            )

        department_ref.update(update_data)

        return success_response(
            message="Department updated successfully",
            data={"id": id, **update_data}
        )

    except Exception as e:
        return error_response(
            message=str(e)
        )
