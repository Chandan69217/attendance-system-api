from fastapi import APIRouter,status,Depends
from app.schemas.class_schema import ClassSchema,ClassUpdateSchema
from app.core.security import verify_token
from app.schemas.user_schema import Role
from app.core.response import error_response,success_response
from app.firebase.firebase_init import db
from app.lib.utils import generate_class_id
from datetime import datetime,timedelta,timezone
from typing import Optional
from collections import defaultdict

router = APIRouter()




@router.post("/create",status_code=status.HTTP_201_CREATED)
def create(data:ClassSchema,currect_user:dict=Depends(verify_token)):
    role = currect_user.get("role")
    user_id = currect_user.get("id")

    if role != Role.admin:
        return error_response(
            message="Only admin can add the classes"
        )
    
    teacher_id = data.class_teacher_id

    if not teacher_id:
        return error_response(message="Class Teacher is required")
    
    head_doc = db.collection("users").document(teacher_id).get()

    if not head_doc.exists:
        return error_response(
            message= "Faculty does not exists"
        )
    if head_doc.to_dict().get("role") != Role.faculty:
        return error_response(
            message="Only faculty is a class teacher."
        )
    
    dept_doc = db.collection("departments").document(data.dept_id).get()

    if not dept_doc.exists:
        return error_response(
            message="Department does not exists"
        )
    
    class_teacher = head_doc.to_dict().get("name")
    department = dept_doc.to_dict().get("name")

    id = generate_class_id()

    new_class = {
        "id":id,
        "name": data.name,
        "class_teacher_id" : teacher_id,
        "class_teacher": class_teacher,
        "dept_id":data.dept_id,
        "dept_name": department,
        "created_at": datetime.now(timezone.utc),
        "created_by": user_id
    }

    db.collection("classes").document(id).set(new_class)

    return success_response(
        message="class created successfully",
        data= new_class
    )



@router.get("/get-class", status_code=status.HTTP_200_OK)
def get_classes(
    id: Optional[str] = None,
    dept_id: Optional[str] = None,
    current_user: dict = Depends(verify_token)
):

    try:
        class_collection = db.collection("classes")


        if dept_id:
            class_collection = class_collection.where("dept_id", "==", dept_id.upper())

        if id:
            class_collection = class_collection.where("id", "==", id.upper())

    
        users_doc = (
            db.collection("users")
            .where("role", "==", Role.student)
            .stream()
        )

        student_count = defaultdict(int)

        for u in users_doc:
            user_dict = u.to_dict()
            class_id = user_dict.get("class_id")
            if class_id:
                student_count[class_id] += 1

        class_snapshot = class_collection.stream()

        classes = []

        for cls in class_snapshot:
            cls_dict = cls.to_dict()
            class_id = cls_dict.get("id")

            cls_dict.update({
                "student_count": student_count.get(class_id, 0)
            })

            classes.append(cls_dict)

        return success_response(
            message="Classes fetched successfully",
            data=classes
        )

    except Exception as e:
        return error_response(message=str(e))


@router.put("/update/{id}",status_code=status.HTTP_200_OK)
def update(id:str,data:ClassUpdateSchema, current_user:dict=Depends(verify_token)):
    
    try:
        user_role = current_user.get('role')

        if user_role != Role.admin:
            return error_response(
                message="Only admin can update the class"
            )
        
        class_ref = db.collection("classes").document(id.upper())

        class_doc = class_ref.get()

        if not class_doc.exists:
            return error_response(
                message="Class not found"
            )
        
        updated_data = data.model_dump( 
            exclude_unset=True,
            exclude_none=True
            )

        if not updated_data:
            return error_response(
                message="No fields provided to update"
            )
        
        class_ref.update(updated_data)
        return success_response(
            message="Class updated successfully",
            data=updated_data
        )

    except Exception as e:
        return error_response(
            message=str(e)
        )
    
@router.delete("/delete/{id}",status_code=status.HTTP_200_OK)
def delete(id:str,current_user:dict = Depends(verify_token)):
    
    user_role = current_user.get("role")

    if user_role != Role.admin:
        return error_response(
            message="Only admin can deleted class"
        )
    
    class_ref = db.collection("classes").document(id.upper())

    class_doc = class_ref.get()

    if not class_doc.exists:
        return error_response(
            message="class not found"
        )
    deleted_data = class_doc.to_dict()

    class_ref.delete()
    return success_response(
        message="Class deleted successfully",
        data=deleted_data
    )