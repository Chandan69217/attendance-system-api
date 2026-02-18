# from fastapi import FastAPI, WebSocket
# import face_recognition
# import numpy as np
# import cv2
# import base64
# from geopy.distance import geodesic

# app = FastAPI()


# def check_geofence(user_lat, user_lng, dept_lat, dept_lng, radius):
#     distance = geodesic(
#         (user_lat, user_lng),
#         (dept_lat, dept_lng)
#     ).meters

#     return distance <= radius, distance


# @app.websocket("/ws/attendance/{user_id}")
# async def attendance_socket(websocket: WebSocket, user_id: str):
#     await websocket.accept()

#     user = get_user_from_db(user_id)
#     dept = get_department(user["department_id"])

#     stored_encoding = np.array(user["face_encoding"])

#     try:
#         while True:
#             data = await websocket.receive_json()

#             image_data = data["image"]  # base64 string
#             latitude = data["latitude"]
#             longitude = data["longitude"]

#             # Decode image
#             img_bytes = base64.b64decode(image_data.split(",")[1])
#             np_arr = np.frombuffer(img_bytes, np.uint8)
#             frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

#             frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)

#             # Detect face
#             face_locations = face_recognition.face_locations(frame)

#             if not face_locations:
#                 await websocket.send_json({
#                     "status": False,
#                     "message": "No face detected"
#                 })
#                 continue

#             face_encoding = face_recognition.face_encodings(frame)[0]

#             # Compare face
#             match = face_recognition.compare_faces(
#                 [stored_encoding],
#                 face_encoding
#             )

#             if not match[0]:
#                 await websocket.send_json({
#                     "status": False,
#                     "message": "Face not matched"
#                 })
#                 continue

#             # Check geofence
#             inside, distance = check_geofence(
#                 latitude, longitude,
#                 dept["latitude"], dept["longitude"],
#                 dept["radius"]
#             )

#             if not inside:
#                 await websocket.send_json({
#                     "status": False,
#                     "message": f"You are {round(distance,2)} meters away"
#                 })
#                 continue

#             # SUCCESS → Mark attendance
#             save_attendance(user_id, latitude, longitude)

#             await websocket.send_json({
#                 "status": True,
#                 "message": "Attendance Marked Successfully"
#             })

#             break  # Stop after success

#     except Exception as e:
#         print(e)
#     finally:
#         await websocket.close()




# from fastapi import APIRouter, WebSocket
# import face_recognition
# import numpy as np
# import cv2
# from geopy.distance import geodesic
# import base64
# from app.firebase.firebase_init import db
# from app.schemas.setting_schema import SettingKey
# from app.schemas.user_schema import Role 
# from app.schemas.attendance_schema import StudentAttendanceResponseSchema,FacultyAttendanceResponseSchema,FacultyAttendanceSchema,StudentAttendanceSchema,AttendanceVerificationSchema,AttendanceStatusSchema,AttendanceMethodSchema  
# from app.core.response import error_response,success_response
# from app.lib.utils import generate_faculty_attendace_id,generate_student_attendance_id
# from datetime import datetime,timezone,time,timedelta

# router = APIRouter()



# def get_time(checkIn:str):
#     return datetime.strptime(checkIn, "%H:%M %p").time()

# def get_date(date:str):
#     return datetime.strptime(date,"%Y-%m-%d").date()

# def format_date(date:datetime):
#     return date.strftime("%Y-%m-%d")

# def format_time(date:time):
#    return date.strftime("%I:%M %p")


# latitude = 0
# longitude = 0
# radius = 0
# lateThreshold = 0 
# confidanceThreshold = 0
# checkIn = get_time("10:00 AM")




# settings = db.collection("settings").document("global").get()

# if settings.exists:
#     setting_dict = settings.to_dict()

#     latitude = setting_dict.get(SettingKey.latitude)
#     longitude = setting_dict.get(SettingKey.longitude)
#     radius = setting_dict.get(SettingKey.max_check_in_distance)
#     lateThreshold = setting_dict.get(SettingKey.late_threshold)
#     confidanceThreshold = setting_dict.get(SettingKey.confidence_threshold)
#     checkIn = get_time(setting_dict.get(SettingKey.check_in))


# users = []

# user_collection = db.collection("users").stream()

# for u in user_collection:
#     user = u.to_dict()
#     users.append(user)


# def check_geofence(user_lat, user_lng):
#     distance = geodesic(
#         (user_lat, user_lng),
#         (latitude, longitude)
#     ).meters

#     return distance <= radius, distance


# @router.websocket("/{user_id}")
# async def attendance_socket(websocket: WebSocket, user_id: str):
#     await websocket.accept()

#     user = next((u for u in users if u["user_id"] == user_id), None)
#     stored_encoding = (
#     np.array(user["face"])
#     if user.get("face") is not None
#     else None
#     )

#     role = user.get("role")

#     isFaculty = role == Role.faculty

#     if not stored_encoding :
#         await websocket.send_json(
#             error_response(message="User face is not register first regiter")
#         )
#         return

#     try:
#         while True:
#             now = datetime.now(timezone.utc)
#             data = await websocket.receive_json()

#             if(isFaculty):
#                 validate = FacultyAttendanceResponseSchema(**data)
#                 if(not validate.status):
#                     await websocket.send_json(
#                         error_response(
#                             message="required fields are missing"
#                         )
#                     )
#             else:
#                 validate = StudentAttendanceResponseSchema(**data)
#                 if(not validate.status):
#                     await websocket.send_json(
#                         error_response(
#                             message="required fields are missing"
#                         )
#                     )
            
#             image_data = data["image"]  
#             lat = data["latitude"]
#             lng = data["longitude"]


#             img_bytes = base64.b64decode(image_data.split(",")[1])
#             np_arr = np.frombuffer(img_bytes, np.uint8)
#             frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

#             frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)

            
#             face_locations = face_recognition.face_locations(frame)

#             if not face_locations:
#                 await websocket.send_json(
#                     error_response(
#                         message= "No face detected"
#                     )
#                 )
#                 continue

#             face_encoding = face_recognition.face_encodings(frame)[0]

#             match = face_recognition.compare_faces(
#                 [stored_encoding],
#                 face_encoding
#             )

#             if not match[0]:
#                 await websocket.send_json(
#                     error_response(
#                         message= "Face not matched"
#                     )
#                 )
#                 continue

#             # Check geofence
#             inside, distance = check_geofence(lat, lng,)

#             if not inside:
#                 await websocket.send_json(
#                     error_response(
#                         message=f"You are {round(distance,2)} meters away"
#                     )
#                 )
#                 continue

#             # SUCCESS → Mark attendance


#             status = AttendanceStatusSchema.absent


#             if isFaculty:

#                 attendance_ref = db.collection("faculty_attendances")

#                 query = attendance_ref \
#                     .where("faculty_id", "==", user_id) \
#                     .where("date", "==", format_date(now)) \
#                     .limit(1) \
#                     .stream()

#                 existing_record = next(query, None)
                
#                 if existing_record:
#                     if not data.get('check_out'):
#                         await WebSocket.send_json(error_response(message="Check out time is missing"))
#                         continue

#                     doc_ref  = attendance_ref.document(existing_record.id)
#                     doc_ref.update(
#                        { "check_out" : format_time(now)}
#                     )

#                 else:
#                     d = {}
#                     d['id'] = generate_faculty_attendace_id()
#                     d['faculty_id'] = user_id
#                     d['faculty_name'] = user.get("name")
#                     d['date'] = format_date(now)
#                     d['check_in'] = format_time(now)
#                     d["check_out"] = ""
#                     d["remarks"] = data['remarks']
#                     d['verification_status'] = AttendanceVerificationSchema.pending

#                     check_in_time =  get_time(checkIn)
                    
#                     check_in_datetime = datetime.combine(
#                         now.date(),
#                         check_in_time
#                     )


#                     allowedTime = check_in_datetime + timedelta(minutes=lateThreshold)

#                     if now>allowedTime:
#                         d['status'] = AttendanceStatusSchema.late
#                     else: 
#                         d['status'] = AttendanceStatusSchema.present
                    
#                 save_faculty_attendance(data=d)
#             else:

#                 d = {}

#                 d['id'] = generate_student_attendance_id()
#                 d['student_id'] = user_id
#                 d['student_name'] = user.get('name')
#                 d['date'] = format_date(now)
#                 d['subject_id'] = data['subject_id']
#                 d['subject_name'] = data['subject_name']
#                 d['method'] = data['method']
#                 d['marked_by_id'] = data['marked_by_id']
#                 d['marked_by_name'] = data['marked_by_name']
#                 d['status'] = AttendanceStatusSchema.present
#                 save_faculty_attendance(data=d,)
            

#             await websocket.send_json(
#                 success_response(
#                     message="Attendance Marked Successfully"
#                 )
#             )

#             break 

#     except Exception as e:
#         print(e)
#     finally:
#         await websocket.close()



  



 



# def  save_faculty_attendance(data:FacultyAttendanceSchema):
#     pass


# def  save_student_attendance(data:StudentAttendanceSchema):
#     pass





from fastapi import APIRouter, WebSocket
from app.core.security import verify_token
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

router = APIRouter()


def get_time(value: str):
    return datetime.strptime(value, "%I:%M %p").time()


def check_geofence(user_lat, user_lng, latitude, longitude, radius):
    distance = geodesic(
        (user_lat, user_lng),
        (latitude, longitude)
    ).meters

    return distance <= radius, distance


def save_faculty_attendance(data: dict):
    doc_id = generate_faculty_attendace_id()
    db.collection("faculty_attendances").document(doc_id).set(data)


def save_student_attendance(data: dict):
    doc_id = generate_student_attendance_id()
    db.collection("student_attendances").document(doc_id).set(data)



@router.websocket("/{user_id}")
async def attendance_socket(websocket: WebSocket, user_id: str):

    await websocket.accept()
   

    now = datetime.now(timezone.utc)

    settings_doc = db.collection("settings").document("global").get()

    if not settings_doc.exists:
        await websocket.send_json(error_response("Settings not found"))
        return

    settings = settings_doc.to_dict()

    latitude = settings.get("latitude")
    longitude = settings.get("max_check_in_distance")
    radius = settings.get("max_check_in_distance")
    late_threshold = settings.get("late_threshold", 0)
    confidence_threshold = settings.get("confidence_threshold", 0.6)
    check_in_setting = datetime.strptime(settings.get("check_in"),"%H:%M").time()

    # 🔹 Get user
    user_doc = db.collection("users").document(user_id).get()

    if not user_doc.exists:
        await websocket.send_json(error_response("User not found"))
        return

    user = user_doc.to_dict()

    if not user.get("face"):
        await websocket.send_json(
            error_response("User face not registered")
        )
        return

    stored_encoding = np.array(user["face"])
    role = user.get("role")
    is_faculty = role == Role.faculty.value

    try:
        while True:
            data = await websocket.receive_json()

            image_data = data["image"]
            user_lat = data["latitude"]
            user_lng = data["longitude"]

            # 🔹 Decode image
            img_bytes = base64.b64decode(image_data.split(",")[1])
            np_arr = np.frombuffer(img_bytes, np.uint8)
            frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)

            face_locations = face_recognition.face_locations(frame)

            if not face_locations:
                await websocket.send_json(
                    error_response("No face detected")
                )
                continue

            face_encoding = face_recognition.face_encodings(frame)[0]

            # 🔹 Compare faces with confidence
            distance = face_recognition.face_distance(
                [stored_encoding],
                face_encoding
            )[0]

            if distance > confidence_threshold:
                await websocket.send_json(
                    error_response("Face not matched")
                )
                continue

            # 🔹 Geofence check
            inside, dist = check_geofence(
                user_lat, user_lng,
                latitude, longitude, radius
            )

            if not inside:
                await websocket.send_json(
                    error_response(
                        f"You are {round(dist,2)} meters away"
                    )
                )
                continue

            today = now.date().isoformat()

            # =========================================================
            # FACULTY
            # =========================================================
            if is_faculty:

                doc_id = f"{user_id}_{today}"
                attendance_ref = db.collection("faculty_attendances").document(doc_id)
                existing = attendance_ref.get()

                if existing.exists:
                    attendance_ref.update({
                        "check_out": now,
                        "updated_at": now
                    })

                    await websocket.send_json(
                        success_response("Check-out updated")
                    )
                else:
                    # 🔹 Late calculation
                    check_in_datetime = datetime.combine(
                        now.date(),
                        check_in_setting
                    )

                    allowed_time = check_in_datetime + timedelta(
                        minutes=late_threshold
                    )

                    status = (
                        AttendanceStatusSchema.late.value
                        if now > allowed_time
                        else AttendanceStatusSchema.present.value
                    )

                    attendance_data = {
                        "id": generate_faculty_attendace_id(),
                        "faculty_id": user_id,
                        "faculty_name": user.get("name"),
                        "date": now.date(),
                        "check_in": now,
                        "check_out": None,
                        "status": status,
                        "verification_status": AttendanceVerificationSchema.pending.value,
                        "remarks": data.get("remarks"),
                        "created_at": now
                    }

                    save_faculty_attendance(attendance_data)

                    await websocket.send_json(
                        success_response("Check-in marked")
                    )

            # =========================================================
            # STUDENT
            # =========================================================
            else:

                attendance_data = {
                    "id": generate_student_attendance_id(),
                    "student_id": user_id,
                    "student_name": user.get("name"),
                    "date": now.date(),
                    "subject_id": data["subject_id"],
                    "subject_name": data["subject_name"],
                    "status": AttendanceStatusSchema.present.value,
                    "marked_by_id": data["marked_by_id"],
                    "marked_by_name": data["marked_by_name"],
                    "method": AttendanceMethodSchema.face_recognition.value,
                    "created_at": now
                }

                save_student_attendance(attendance_data)

                await websocket.send_json(
                    success_response("Attendance Marked Successfully")
                )

            break

    except Exception as e:
        print("Error:", e)

    finally:
        await websocket.close()
