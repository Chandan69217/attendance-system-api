from fastapi import APIRouter, status,Depends
from app.core.response import error_response,success_response
from app.firebase.firebase_init import db
from app.core.security import verify_token
from typing import Optional
from google.cloud.firestore_v1 import FieldFilter


router = APIRouter()

collection = db.collection('users')


@router.get("/get-user", status_code=status.HTTP_200_OK)
def get_user_by_id(
    id: Optional[str] = None,
    limit: int = 20,
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

    return success_response(
        message="All users fetched successfully",
        data=users
    )






@router.get("/filter-user", status_code=status.HTTP_200_OK)
def get_users(
    search: Optional[str] = None,
    limit: int = 20,
    current_user: dict = Depends(verify_token)
):

    collection = db.collection("users")
    users = []


    if search:
        search = search.strip()

    
        doc = collection.document(search.upper()).get()
        if doc.exists:
            user = doc.to_dict()
            user["id"] = doc.id
            user.pop("password", None)

            return success_response(
                message="User found successfully",
                data=[user]
            )

        role_query = collection\
            .where(filter=FieldFilter("role", "==", search.lower()))\
            .limit(limit)\
            .stream()

        for doc in role_query:
            user = doc.to_dict()
            user["id"] = doc.id
            user.pop("password", None)
            users.append(user)

        return success_response(
            message="Search results",
            data=users
        )

    docs = collection.limit(limit).stream()

    for doc in docs:
        user = doc.to_dict()
        user["id"] = doc.id
        user.pop("password", None)
        users.append(user)

    return success_response(
        message="Users fetched successfully",
        data=users
    )

