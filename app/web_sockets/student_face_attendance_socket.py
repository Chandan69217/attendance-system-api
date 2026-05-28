from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import face_recognition
import numpy as np
import cv2
import base64
from geopy.distance import geodesic
from datetime import datetime, timezone, timedelta
from app.firebase.firebase_init import db
from app.schemas.attendance_schema import (
    AttendanceStatusSchema,
    AttendanceVerificationSchema,
    AttendanceMethodSchema,
)
from app.schemas.user_schema import Role
from app.core.response import error_response, success_response
from app.lib.utils import (
    generate_faculty_attendace_id,
    generate_student_attendance_id,
)
from app.schemas.setting_schema import SettingKey
import pytz
from google.cloud.firestore_v1 import FieldFilter


def get_time(value: str):
    return datetime.strptime(value, "%I:%M %p").time()

def format_time(value:datetime):
    return datetime.strftime(value,"%I:%M %p")

router = APIRouter()



# Utility Functions


def check_geofence(user_lat, user_lng, latitude, longitude, radius):
    distance = geodesic(
        (user_lat, user_lng),
        (latitude, longitude)
    ).meters

    return distance <= radius, distance












@router.websocket("/face-attendance")
async def student_face_recognition_socket(websocket: WebSocket):

    await websocket.accept()

    try:

        settings_doc = db.collection("settings").document("global").get()

        if not settings_doc.exists:
            await websocket.send_json(error_response("Settings not found"))
            return

        settings = settings_doc.to_dict()
        confi_threshold = settings.get("confidence_threshold", 60)
        confidence_threshold = round(1 - confi_threshold / 100, 2)
        allow_self_attendance = settings.get("allow_student_self_attendance", True)

  
        students = []
        students_ref = db.collection("users") \
            .where(filter=FieldFilter("role", "==", Role.student.value)) \
            .stream()

        for doc in students_ref:
            data = doc.to_dict()

            if not data.get("face"):
                continue

            students.append({
                "id": doc.id,
                "name": data.get("name"),
                "face": np.array(data.get("face"))
            })

        ist = pytz.timezone("Asia/Kolkata")

        while True:

            data = await websocket.receive_json()
            image_data = data.get("image")
            lecture_id = data.get("lecture_id")

            if not image_data:
                await websocket.send_json(error_response("Image is required"))
                continue

            if not lecture_id:
                await websocket.send_json(error_response("Lecture ID is required"))
                continue

    
            try:
                img_bytes = base64.b64decode(image_data)
                np_arr = np.frombuffer(img_bytes, np.uint8)
                frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            except Exception:
                await websocket.send_json(error_response("Invalid image data"))
                continue


            face_locations = face_recognition.face_locations(frame)

            if not face_locations:
                await websocket.send_json(error_response("No face detected"))
                continue

            if len(face_locations) > 1:
                await websocket.send_json(error_response("Multiple faces detected"))
                continue

            encodings = face_recognition.face_encodings(frame, face_locations)

            if not encodings:
                await websocket.send_json(error_response("Face encoding failed"))
                continue

            face_encoding = encodings[0]


            matched_user = None

            for student in students:
                distance = face_recognition.face_distance(
                    [student["face"]],
                    face_encoding
                )[0]

                if distance < confidence_threshold:
                    matched_user = student
                    break

            if not matched_user:
                await websocket.send_json(error_response("No matching student found"))
                continue

            lecture_doc = db.collection("lectures").document(lecture_id).get()

            if not lecture_doc.exists:
                await websocket.send_json(error_response("Lecture not found"))
                continue

            lecture_data = lecture_doc.to_dict()
            lecture_status = lecture_data.get("status")

            if lecture_status == "scheduled":
                await websocket.send_json(error_response("Lecture has not started yet"))
                continue

            if lecture_status == "close":
                await websocket.send_json(error_response("Lecture already completed"))
                continue

            subject_id = lecture_data.get("subject_id")

            if not subject_id:
                await websocket.send_json(error_response("Lecture subject missing"))
                continue

            now = datetime.now(ist)
            today = now.date().isoformat()

            # 🔹 Prevent duplicate attendance
            existing_query = (
                db.collection("student_attendances")
                .where(filter=FieldFilter("student_id", "==", matched_user["id"]))
                .where(filter=FieldFilter("subject_id", "==", subject_id))
                .where(filter=FieldFilter("date", "==", today))
                .stream()
            )

            if any(existing_query):
                await websocket.send_json(
                    success_response(
                        message="Attendance already marked",
                         data={
                        "student_name": matched_user["name"],
                        "isMarked": False
                    }
                     )
                )
                continue

            # ── Determine who is marking: faculty (marked_by_id in data) vs self ───
            marked_by_id = data.get("marked_by_id")
            is_self_mark = not marked_by_id  # no marker = student self-scan

            if is_self_mark and not allow_self_attendance:
                await websocket.send_json(
                    error_response(
                        message="Self-attendance is currently disabled by admin. "
                                "Please ask your faculty to mark your attendance."
                    )
                )
                continue

            # ── Create attendance ──────────────────────────────────────
            today = now.date().isoformat()
            attendance_data = {
                "id": generate_student_attendance_id(),
                "student_id": matched_user["id"],
                "student_name": matched_user["name"],
                "date": today,
                "subject_id": subject_id,
                "subject_name": lecture_data.get("subject_name"),
                "status": AttendanceStatusSchema.present.value,
                "marked_by_id": marked_by_id or matched_user["id"],
                "marked_by_name": data.get("marked_by_name") or matched_user["name"],
                "method": (
                    AttendanceMethodSchema.self_marked.value
                    if is_self_mark
                    else AttendanceMethodSchema.face_recognition.value
                ),
                "created_at": now
            }

            db.collection("student_attendances") \
                .document(f"{attendance_data['id']}_{today}") \
                .set(attendance_data)

            await websocket.send_json(
                success_response(
                    message="Attendance marked successfully",
                    data={
                        "student_name": matched_user["name"],
                        "isMarked": True
                    }
                )
            )

    except WebSocketDisconnect:
        print("Client disconnected")

    except Exception as e:
        print("Socket Error:", e)
