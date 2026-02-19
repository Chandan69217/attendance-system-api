from fastapi import APIRouter, status,Depends
from app.core.response import error_response,success_response
from app.firebase.firebase_init import db
from app.core.security import verify_token
from typing import Optional
from google.cloud.firestore_v1 import FieldFilter
from collections import defaultdict
from app.schemas.user_schema import Role,UserStatus,UserUpdateSchema


router = APIRouter()

collection = db.collection('users')


@router.get("/get-user", status_code=status.HTTP_200_OK)
def get_user_by_id(
    id: Optional[str] = None,
    current_user: dict = Depends(verify_token)
):

    collection = db.collection("users")

    if id:
        doc = collection.document(id.upper()).get()

        if not doc.exists:
            return error_response(message="User not found")

        user = doc.to_dict()
        user["id"] = doc.id
        user.pop("password", None)

        return success_response(
            message="User found successfully",
            data=[user]
        )

    users = []

    docs = collection.stream()

    for doc in docs:
        user = doc.to_dict()
        user["id"] = doc.id
        user.pop("password", None)
        users.append(user)

    users.reverse()
    return success_response(
        message="All users fetched successfully",
        data=users
    )




@router.get("/filter-user", status_code=status.HTTP_200_OK)
def get_users(
    search: Optional[str] = None,
    current_user: dict = Depends(verify_token)
):

    users_collection = db.collection("users")
    dept_collection = db.collection("departments")
    class_collection = db.collection("classes")

    users = []

    depts_map = {
        doc.id: doc.to_dict()
        for doc in dept_collection.stream()
    }

    class_map = {
        doc.id:doc.to_dict()
        for doc in class_collection.stream()
    }


    def enrich_user(doc):
        user = doc.to_dict()
        user["id"] = doc.id
        user.pop("password", None)
        dept = depts_map.get(user.get("dept_id"))
        cls = class_map.get(user.get("class_id"))
        user["department"] = dept.get("name") if dept else None
        user["class"] = cls.get("name") if cls else None

        return user


    if search and search.lower() != "all":
        search = search.strip()

        doc = users_collection.document(search.upper()).get()
        if doc.exists:
            return success_response(
                message="User found successfully",
                data=[enrich_user(doc)]
            )

        role_query = users_collection \
            .where(filter=FieldFilter("role", "==", search.lower())) \
            .stream()

        users = [enrich_user(doc) for doc in role_query]

        users.reverse()
        return success_response(
            message="Search results",
            data=users
        )


    docs = users_collection.stream()
    users = [enrich_user(doc) for doc in docs]
    users.reverse()
    return success_response(
        message="Users fetched successfully",
        data=users
    )


@router.get("/user-stats", status_code=status.HTTP_200_OK)
def userStats(current_user: dict = Depends(verify_token)):

    users_snap = db.collection("users").stream()

    student_count = 0
    faculty_count = 0
    active_count = 0

    for u in users_snap:
        user = u.to_dict()

        if user.get("role") == Role.student:
            student_count += 1
        elif user.get("role") == Role.faculty:
            faculty_count += 1

        if user.get("status") == UserStatus.active:
            active_count += 1

    return success_response(
        message="User stats calculated successfully",
        data={
            "student_count": student_count,
            "faculty_count": faculty_count,
            "active_count": active_count,
        }
    )
 


@router.delete("/delete/{id}",status_code=status.HTTP_200_OK)
def deleteUser(id:str,current_user:dict = Depends(verify_token)):
    
    user_role = current_user.get("role")

    if user_role != Role.admin:
        return error_response(
            message="Only admin can delete the user"
        )
    
    user_ref = db.collection("users").document(id.upper())

    user_doc = user_ref.get()

    if not user_doc.exists:
            return error_response(
                message="User not found"
        )

    deleted_user = user_doc.to_dict()

    user_ref.delete()

    return success_response(
            message="User deleted successfully",
            data=deleted_user
    )

  

@router.put("/update/{id}", status_code=status.HTTP_200_OK)
def updateUser(
    id: str,
    data: UserUpdateSchema,
    current_user: dict = Depends(verify_token)
):


    update_data = data.model_dump(
        exclude_unset=True,
        exclude_none=True
    )

    if not update_data:
        return error_response(message="No fields provided to update")
    
    


    user_ref = db.collection("users").document(id.upper())
    user_snap = user_ref.get()

    if not user_snap.exists:
        return error_response(message="User not found")
    
    old_user = user_snap.to_dict()

    new_phone = update_data.get("phone")
    # Check phone uniqueness
    if new_phone and not new_phone ==old_user.get("phone"):

        phone_query = db.collection("users") \
            .where("phone", "==", update_data["phone"]) \
            .limit(1) \
            .stream()

        existing_phone_user = next(phone_query, None)

        if existing_phone_user and existing_phone_user.id != id.upper():
            return error_response(message="Phone number already exists")


 

    # Check email uniqueness
    new_email = update_data.get("email")
    if new_email and not old_user.get("email") == new_email:

        email_query = db.collection("users") \
            .where("email", "==", update_data["email"]) \
            .limit(1) \
            .stream()

        existing_email_user = next(email_query, None)

        if existing_email_user and existing_email_user.id != id.upper():
            return error_response(message="Email already exists")
   
    if "role" in update_data:
        try:
            Role(update_data["role"])
        except ValueError:
            return error_response(message="Invalid Role")

 
    final_role = update_data.get("role") or old_user.get("role")

  
    if final_role == Role.student:
        if not (update_data.get("class_id") or old_user.get("class_id")):
            return error_response(message="Class is required for student")

        if not (update_data.get("dept_id") or old_user.get("dept_id")):
            return error_response(message="Department is required for student")

    elif final_role == Role.faculty:
        if not (update_data.get("dept_id") or old_user.get("dept_id")):
            return error_response(message="Department is required for faculty")


    if update_data.get("dept_id"):
        dept_doc = db.collection("departments") \
            .document(update_data["dept_id"].upper()) \
            .get()

        if not dept_doc.exists:
            return error_response(message="Department not found")

        update_data["department"] = dept_doc.to_dict().get("name")


    if update_data.get("class_id"):
        cls_doc = db.collection("classes") \
            .document(update_data["class_id"].upper()) \
            .get()

        if not cls_doc.exists:
            return error_response(message="Class not found")

        update_data["class"] = cls_doc.to_dict().get("name")

    user_ref.update(update_data)

    return success_response(
        message="User updated successfully",
        data=update_data
    )

    
