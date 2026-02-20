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



# Attendance WebSocket


@router.websocket("/{user_id}")
async def attendance_socket(websocket: WebSocket, user_id: str):

    await websocket.accept()

    try:
    
        # Load Global Settings

        settings_doc = db.collection("settings").document("global").get()

        if not settings_doc.exists:
            await websocket.send_json(
                error_response(message= "Settings not found")
                )
            return

        settings = settings_doc.to_dict()

        latitude = settings.get(SettingKey.latitude.value)
        longitude = settings.get(SettingKey.longitude.value)
        radius = settings.get(SettingKey.max_check_in_distance.value)
        late_threshold = settings.get(SettingKey.late_threshold.value, 0)
        confi_threshold = settings.get(SettingKey.confidence_threshold.value, 0.45)
        confidence_threshold = round(1 - confi_threshold / 100, 2)
        check_in_setting = datetime.strptime(
            settings.get("check_in"),
            "%H:%M"
        ).time()

        print(f" check in setting: {check_in_setting}")
        # Get User
 
        user_doc = db.collection("users").document(user_id).get()

        if not user_doc.exists:
            await websocket.send_json(error_response(message="User not found"))
            return

        user = user_doc.to_dict()

        if not user.get("face"):
            await websocket.send_json(
                error_response(message="User face not registered")
            )
            return

        stored_encoding = np.array(user["face"])
        role = user.get("role")
        is_faculty = role == Role.faculty.value

       
        # 🔄 Continuous Listening Loop
      
        while True:

            ist = pytz.timezone("Asia/Kolkata")
            now = datetime.now(ist)

            data = await websocket.receive_json()

            image_data = data.get("image")
            user_lat = data.get(SettingKey.latitude.value)
            user_lng = data.get(SettingKey.longitude.value)
            remarks = data.get("remarks")
            if not image_data:
                await websocket.send_json(
                    success_response(message="Face not found")
                )
                continue

       
            # Decode Image
           
            try:
                img_bytes = base64.b64decode(image_data)
                np_arr = np.frombuffer(img_bytes, np.uint8)
                frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            except Exception:
                await websocket.send_json(
                    success_response(message="Face is not clear")
                )
                continue

            
            # Face Detection
        
            face_locations = face_recognition.face_locations(frame)

            if not face_locations:
                await websocket.send_json(
                    success_response(message="No face detected")
                )
                continue


            if len(face_locations) > 1:
                await websocket.send_json(
                    success_response("Multiple faces detected")
                )
                continue

            encodings = face_recognition.face_encodings(frame, face_locations)

            if not encodings:
                await websocket.send_json(
                    success_response(message="Face encoding failed")
                )
                continue

            face_encoding = encodings[0]

           
            # Face Matching
          
          
            distance = face_recognition.face_distance(
                [stored_encoding],
                face_encoding
            )[0]

            
            if distance > confidence_threshold:
                await websocket.send_json(
                    success_response( message="Face not matched")
                )
                continue

            await websocket.send_json(
                success_response(
                    message="Face matched & marking your attendance"
                )
            )
         
            # Geofence Check
            
            inside, dist = check_geofence(
                user_lat, user_lng,
                latitude, longitude, radius
            )

            if not inside:
                await websocket.send_json(
                    success_response(
                        message=f"You are {round(dist, 2)} meters away"
                    )
                )
                continue

            today = now.date().isoformat()

          
            # FACULTY ATTENDANCE
         
            if is_faculty:

                doc_id = f"{user_id}_{today}"
                attendance_ref = db.collection(
                    "faculty_attendances"
                ).document(doc_id)

                existing = attendance_ref.get()

                if existing.exists:
                    attendance_data = existing.to_dict()

                    if attendance_data.get("check_out"):
                        await websocket.send_json(
                            success_response(message="Already checked out today")
                        )
                        continue

                    attendance_ref.update({
                        "check_out": format_time(datetime.now()),
                        "updated_at": now
                    })

                    await websocket.send_json(
                        success_response(
                            message="Check-out updated",
                            data={"isMarked": True}
                        )
                    )

                else:

                    allowed_time = ist.localize(datetime(
                    now.year,
                    now.month,
                    now.day,
                    check_in_setting.hour,
                    check_in_setting.minute)) + timedelta(minutes=late_threshold)


                    status = (
                        AttendanceStatusSchema.late.value
                        if now > allowed_time
                        else AttendanceStatusSchema.present.value
                    )

                    attendance_data = {
                        "id": doc_id,
                        "faculty_id": user_id,
                        "faculty_name": user.get("name"),
                        "date": today,
                        "check_in": format_time(datetime.now()),
                        "check_out": None,
                        "status": status,
                        "remarks":remarks,
                        "verification_status":
                            AttendanceVerificationSchema.pending.value,
                        "created_at": now,
                        "updated_at": now
                    }

                    attendance_ref.set(attendance_data)

                    await websocket.send_json(
                        success_response(message="Check-in marked",data={
                            "isMarked" : True
                        })
                    )
                    break

        
            # STUDENT ATTENDANCE
         
            else:

                subject_id = data.get("subject_id")

                # Prevent duplicate attendance for same subject today
                existing_query = db.collection("student_attendances") \
                    .where("student_id", "==", user_id) \
                    .where("subject_id", "==", subject_id) \
                    .where("date", "==", today) \
                    .stream()

                if any(existing_query):
                    await websocket.send_json(
                        success_response(message= "Attendance already marked",data={
                            "isMarked" :True
                        })
                    )
                    continue

                attendance_data = {
                    "id": generate_student_attendance_id(),
                    "student_id": user_id,
                    "student_name": user.get("name"),
                    "date": today,
                    "subject_id": subject_id,
                    "subject_name": data.get("subject_name"),
                    "status": AttendanceStatusSchema.present.value,
                    "marked_by_id": data.get("marked_by_id"),
                    "marked_by_name": data.get("marked_by_name"),
                    "method": AttendanceMethodSchema.face_recognition.value,
                    "created_at": now
                }

                db.collection("student_attendances") \
                    .document(attendance_data["id"]) \
                    .set(attendance_data)

                await websocket.send_json(
                    success_response(message="Attendance Marked Successfully",data={
                        "isMarked" : True
                    })
                )

    except WebSocketDisconnect:
        print("Client disconnected")

    except Exception as e:
        print("Attendance Socket Error:", e)
