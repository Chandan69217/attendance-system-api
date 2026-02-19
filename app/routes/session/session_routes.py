from fastapi import APIRouter, status, Depends
from datetime import datetime,timezone
from app.firebase.firebase_init import db
from app.core.response import success_response, error_response
from app.schemas.session_schema import (
    CreateSessionSchema,
    UpdateSessionSchema,
    SessionStatus,
)
from app.core.security import verify_token
from app.lib.utils import generate_session_id
from collections import defaultdict
from app.schemas.user_schema import Role


router = APIRouter()



def get_session_status(
    start_date_str: str,
    end_date_str: str,
    default_status: str = "unknown"
) -> str:
    try:
        start_datetime = datetime.strptime(f"{start_date_str}", "%Y-%m-%d")
        end_datetime = datetime.strptime(f"{end_date_str}", "%Y-%m-%d")

        start_datetime = start_datetime.replace(tzinfo=timezone.utc)
        end_datetime = end_datetime.replace(tzinfo=timezone.utc)

        now = datetime.now(timezone.utc)

        if now < start_datetime:
            return "upcoming"
        elif start_datetime <= now <= end_datetime:
            return "active"
        else:
            return "completed"

    except Exception as e:
        print(f"Status calculation error: {e}")
        return default_status



@router.post("/create", status_code=status.HTTP_201_CREATED)
def create_session(
    payload: CreateSessionSchema,
    current_user: dict = Depends(verify_token)
):

    user_role = current_user.get('role')
    if user_role != Role.admin:
        return error_response(
            message="Only admin can create the session"
        )
    generate_id = generate_session_id()
    payload.id = generate_id
    session_ref = db.collection("sessions").document(generate_id)

    if session_ref.get().exists:
        return error_response(message="Session ID already exists")

    if payload.end_date <= payload.start_date:
        return error_response(message="End date must be after start date")
    
    status = get_session_status(payload.start_date,payload.end_date)

    session_ref.set({
        "id": payload.id.upper(),
        "name": payload.name,
        "start_date": payload.start_date.strftime("%Y-%m-%d"),
        "end_date": payload.end_date.strftime("%Y-%m-%d"),
        "status": status,
        "created_at": datetime.now(timezone.utc)
    })

    return success_response(
        message="Session created successfully",
        data=payload.model_dump()
    )


@router.get("/get-session", status_code=status.HTTP_200_OK)
def get_sessions(
    id: str | None = None,
    status: str | None = None,
    current_user: dict = Depends(verify_token)
):

    collection = db.collection("sessions")
    users = db.collection("users") \
    .where("role", "==", "student") \
    .select(["session_id"]) \
    .stream()

    user_map = {}

    for user in users:
        data = user.to_dict()
        session_id = data.get("session_id")

        if not session_id:
            continue

        if session_id in user_map:
            user_map[session_id] += 1
        else:
            user_map[session_id] = 1

    if id:
        session_ref = collection.document(id.upper())
        session_doc = session_ref.get()

        if not session_doc.exists:
            return error_response(message="Session not found")

        session_data = session_doc.to_dict()
        session_data["student_count"] = user_map[session_data.get("id")]

        return success_response(
            message="Session fetched successfully",
            data=[session_data]
        )

    sessions = []

    for doc in collection.stream():
        data = doc.to_dict()
        data['student_count'] = user_map.get(data['id'], 0)
        sessions.append(data)

    if status:
        filtered_sessions = [
            s for s in sessions if s.get("status").lower() == status.lower()
        ]
        filtered_sessions.reverse()
        return success_response(
        message="Sessions fetched successfully",
        data=filtered_sessions
    )
    else:
        sessions.reverse()
        return success_response(
        message="Sessions fetched successfully",
        data=sessions
        )

    



@router.put("/update/{id}", status_code=status.HTTP_200_OK)
def update_session(
    id: str,
    payload: UpdateSessionSchema,
    current_user: dict = Depends(verify_token)
):

    session_ref = db.collection("sessions").document(id.upper())
    session_doc = session_ref.get()

    if not session_doc.exists:
        return error_response(message="Session not found")

    update_data = payload.model_dump(
        exclude_unset=True,
        exclude_none=True
    )

    if "start_date" in update_data:
        update_data["start_date"] = update_data["start_date"].strftime("%Y-%m-%d")

    if "end_date" in update_data:
        update_data["end_date"] = update_data["end_date"].strftime("%Y-%m-%d")

    session_ref.update(update_data)

    return success_response(
        message="Session updated successfully",
        data=update_data
    )


@router.delete("/delete/{id}", status_code=status.HTTP_200_OK)
def delete_session(
    id: str,
    current_user: dict = Depends(verify_token)
):
    session_ref = db.collection("sessions").document(id.upper())
    session_doc = session_ref.get()

    if not session_doc.exists:
        return error_response(message="Session not found")

    session_ref.delete()

    return success_response(
        message="Session deleted successfully"
    )
